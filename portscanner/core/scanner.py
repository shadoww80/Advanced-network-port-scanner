"""Concurrent TCP port scanner."""

from __future__ import annotations

import socket
import threading
import time
from concurrent.futures import CancelledError, FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import datetime

from portscanner.config import (
    OPEN_STATUS,
    SCAN_CONNECT_TIMEOUT_SECONDS,
    SCAN_MAX_PENDING_TASKS,
    SCAN_MAX_WORKER_THREADS,
    SCAN_PROGRESS_UPDATE_INTERVAL_SECONDS,
    SCAN_WORKER_POLL_TIMEOUT_SECONDS,
    SUMMARY_PLACEHOLDER,
    UNKNOWN_BANNER,
)
from portscanner.logging_config import get_logger
from portscanner.models import ScanSummary
from portscanner.network.banner import BannerGrabber
from portscanner.network.resolver import ResolvedTarget, resolve_host, resolve_target
from portscanner.network.services import lookup_service
from portscanner.network.socket_utils import close_socket
from portscanner.types import (
    CompleteCallback,
    ProgressCallback,
    ResultCallback,
    ScanStartedCallback,
    StatusCallback,
)
from portscanner.validation import ValidationError, validate_port_range, validate_target

logger = get_logger("core.scanner")


class PortScanner:
    """Run concurrent TCP connect scans with optional banner grabbing."""

    def __init__(
        self,
        on_progress: ProgressCallback,
        on_result: ResultCallback,
        on_status: StatusCallback,
        on_complete: CompleteCallback,
        on_scan_started: ScanStartedCallback | None = None,
    ) -> None:
        self._callbacks = _ScanCallbacks(
            on_progress, on_result, on_status, on_complete, on_scan_started
        )

        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()
        self._executor: ThreadPoolExecutor | None = None
        self._scan_thread: threading.Thread | None = None

        self._open_port_count = 0
        self._scanned_port_count = 0
        self._total_port_count = 0
        self._last_progress_emit_time = 0.0
        self._banner_grabber = BannerGrabber()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_scanning(self) -> bool:
        """Return True while a background scan thread is running."""
        return self._scan_thread is not None and self._scan_thread.is_alive()

    def start(self, target: str, start_port: int, end_port: int) -> None:
        """Start scanning *target* on the inclusive port range."""
        try:
            normalized_target = validate_target(target)
            validate_port_range(start_port, end_port)
        except ValidationError as exc:
            self._callbacks.status(exc.user_message)
            return

        with self._state_lock:
            if self._scan_thread is not None and self._scan_thread.is_alive():
                self._callbacks.status("A scan is already running.")
                return

            self._stop_event.clear()
            scan_thread = threading.Thread(
                target=self._execute_scan,
                args=(normalized_target, start_port, end_port),
                daemon=True,
                name="PortScanWorker",
            )
            self._scan_thread = scan_thread

        scan_thread.start()

    def stop(self) -> None:
        """Request cancellation of the active scan."""
        self._stop_event.set()
        logger.info("Scan cancellation requested")

        executor = self._executor
        if executor is not None:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except RuntimeError:
                logger.exception("Failed to shut down scan executor during cancellation")

        self._callbacks.status("Stopping scan…")

    # ------------------------------------------------------------------
    # Scan orchestration
    # ------------------------------------------------------------------

    def _execute_scan(self, target: str, start_port: int, end_port: int) -> None:
        start_time = datetime.now()

        try:
            validate_port_range(start_port, end_port)
        except ValidationError as exc:
            self._callbacks.status(exc.user_message)
            self._callbacks.complete(
                ScanSummary.started(target, SUMMARY_PLACEHOLDER, start_time).finished(
                    end_time=datetime.now(),
                    total_ports_scanned=0,
                    open_ports_found=0,
                    stopped=False,
                )
            )
            return

        resolved = resolve_host(target)
        if resolved is None:
            self._callbacks.status(
                "Could not resolve target — check the hostname or IP address."
            )
            self._callbacks.complete(
                ScanSummary.started(target, SUMMARY_PLACEHOLDER, start_time).finished(
                    end_time=datetime.now(),
                    total_ports_scanned=0,
                    open_ports_found=0,
                    stopped=False,
                )
            )
            return

        scan_summary = ScanSummary.started(target, resolved.address, start_time)
        logger.info(
            "Scan started | target=%s | resolved_ip=%s | ports=%d-%d",
            target,
            resolved.address,
            start_port,
            end_port,
        )
        self._callbacks.scan_started(scan_summary)
        self._reset_scan_counters(end_port - start_port + 1)
        self._callbacks.status(
            f"Scanning {target} ({resolved.address}) — ports {start_port}–{end_port}"
        )
        self._emit_progress(0.0, force=True)

        stopped = self._run_worker_pool(resolved, range(start_port, end_port + 1))
        self._finalize_scan(scan_summary, stopped=stopped)

    def _finalize_scan(self, scan_summary: ScanSummary, *, stopped: bool) -> None:
        with self._state_lock:
            open_count = self._open_port_count
            scanned_count = self._scanned_port_count
            final_progress = scanned_count / max(self._total_port_count, 1)

        self._emit_progress(final_progress, force=True)

        completed_summary = scan_summary.finished(
            end_time=datetime.now(),
            total_ports_scanned=scanned_count,
            open_ports_found=open_count,
            stopped=stopped,
        )

        if stopped:
            self._callbacks.status("Scan stopped.")
            logger.info(
                "Scan cancelled | target=%s | resolved_ip=%s | duration=%s | "
                "ports_scanned=%d | open_ports=%d",
                completed_summary.target,
                completed_summary.resolved_ip,
                completed_summary.format_duration(),
                scanned_count,
                open_count,
            )
        else:
            self._callbacks.status(
                f"Scan complete — {open_count} open port(s) found."
            )
            logger.info(
                "Scan completed | target=%s | resolved_ip=%s | duration=%s | "
                "ports_scanned=%d | open_ports=%d",
                completed_summary.target,
                completed_summary.resolved_ip,
                completed_summary.format_duration(),
                scanned_count,
                open_count,
            )

        self._callbacks.complete(completed_summary)

    def _run_worker_pool(self, resolved: ResolvedTarget, ports: range) -> bool:
        """Submit port scans with bounded concurrency. Returns True if stopped early."""
        port_iter = iter(ports)
        stopped = False
        executor: ThreadPoolExecutor | None = None
        pending: dict[Future[None], int] = {}

        try:
            executor = ThreadPoolExecutor(max_workers=SCAN_MAX_WORKER_THREADS)
            self._executor = executor
            has_more_ports = True

            while pending or has_more_ports:
                if self._stop_event.is_set():
                    stopped = True
                    break

                while (
                    len(pending) < SCAN_MAX_PENDING_TASKS
                    and not self._stop_event.is_set()
                ):
                    try:
                        port = next(port_iter)
                    except StopIteration:
                        has_more_ports = False
                        break

                    future = executor.submit(self._scan_single_port, resolved, port)
                    pending[future] = port

                if not pending:
                    break

                done, _ = wait(
                    pending.keys(),
                    return_when=FIRST_COMPLETED,
                    timeout=SCAN_WORKER_POLL_TIMEOUT_SECONDS,
                )
                for future in done:
                    pending.pop(future, None)
                    self._consume_future(future)

        except (OSError, RuntimeError):
            logger.exception("Unexpected error while running scan worker pool")
            self._callbacks.status("Scan error — see logs for details.")
            return True
        finally:
            if executor is not None:
                try:
                    if stopped or self._stop_event.is_set():
                        for future in pending:
                            future.cancel()
                        executor.shutdown(wait=False, cancel_futures=True)
                    else:
                        executor.shutdown(wait=True)
                except RuntimeError:
                    logger.exception("Failed to shut down scan executor cleanly")
            self._executor = None

        return stopped

    def _scan_single_port(self, resolved: ResolvedTarget, port: int) -> None:
        """Probe one port, optionally grab a banner, and publish the result."""
        if self._stop_event.is_set():
            return

        sock: socket.socket | None = None
        elapsed_ms = 0
        is_open = False
        service = ""
        banner = UNKNOWN_BANNER

        try:
            sock = socket.socket(resolved.family, socket.SOCK_STREAM)
            sock.settimeout(SCAN_CONNECT_TIMEOUT_SECONDS)

            connect_address = (
                (resolved.address, port, 0, 0)
                if resolved.family == socket.AF_INET6
                else (resolved.address, port)
            )

            started_at = time.perf_counter()
            connect_result = sock.connect_ex(connect_address)
            elapsed_ms = round((time.perf_counter() - started_at) * 1000)
            is_open = connect_result == 0

            if is_open and not self._stop_event.is_set():
                service = lookup_service(port)
                banner = self._banner_grabber.grab(
                    sock,
                    resolved.connect_host,
                    port,
                    service,
                )
        except OSError as exc:
            logger.warning(
                "Port probe failed for %s:%d: %s",
                resolved.address,
                port,
                exc,
            )
        finally:
            close_socket(sock)

        with self._state_lock:
            self._scanned_port_count += 1
            progress = self._scanned_port_count / self._total_port_count
            if is_open:
                self._open_port_count += 1

        self._emit_progress(progress)

        if is_open and not self._stop_event.is_set():
            self._callbacks.result(
                port,
                OPEN_STATUS,
                service,
                f"{elapsed_ms} ms",
                banner,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _reset_scan_counters(self, total_ports: int) -> None:
        self._open_port_count = 0
        self._scanned_port_count = 0
        self._total_port_count = total_ports
        self._last_progress_emit_time = 0.0

    def _emit_progress(self, progress: float, *, force: bool = False) -> None:
        """Throttle progress callbacks to avoid flooding the GUI event queue."""
        now = time.monotonic()
        with self._state_lock:
            if (
                not force
                and progress < 1.0
                and (now - self._last_progress_emit_time)
                < SCAN_PROGRESS_UPDATE_INTERVAL_SECONDS
            ):
                return
            self._last_progress_emit_time = now

        self._callbacks.progress(min(progress, 1.0))

    @staticmethod
    def _consume_future(future: Future[None]) -> None:
        try:
            future.result()
        except CancelledError:
            return
        except (OSError, RuntimeError, ValueError):
            logger.exception("Unexpected error in scan worker future")


class _ScanCallbacks:
    """Small wrapper that keeps scanner callback wiring in one place."""

    __slots__ = ("complete", "progress", "result", "scan_started", "status")

    def __init__(
        self,
        on_progress: ProgressCallback,
        on_result: ResultCallback,
        on_status: StatusCallback,
        on_complete: CompleteCallback,
        on_scan_started: ScanStartedCallback | None,
    ) -> None:
        self.progress = on_progress
        self.result = on_result
        self.status = on_status
        self.complete = on_complete
        self.scan_started = on_scan_started or (lambda _summary: None)


# Backward-compatible helpers for legacy imports.
detect_service = lookup_service

__all__ = ["PortScanner", "detect_service", "resolve_target"]
