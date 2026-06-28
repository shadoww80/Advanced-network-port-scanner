"""Protocol-aware service banner grabbing."""

from __future__ import annotations

import re
import socket
import ssl
import threading
from typing import Final

from portscanner.config import (
    BANNER_GRAB_TIMEOUT_SECONDS,
    BANNER_HTTP_USER_AGENT,
    BANNER_LINE_READ_CHUNK,
    BANNER_MAX_LENGTH,
    BANNER_READ_BUFFER_SIZE,
    UNKNOWN_BANNER,
)
from portscanner.logging_config import get_logger
from portscanner.network.socket_utils import close_socket

# Service groups that share the same banner-grab strategy.
HTTP_SERVICES: Final = frozenset({"HTTP", "HTTP-ALT"})
HTTPS_SERVICES: Final = frozenset({"HTTPS", "HTTPS-ALT"})
LINE_BANNER_SERVICES: Final = frozenset({"SSH", "FTP", "TELNET"})
SMTP_SERVICES: Final = frozenset({"SMTP", "SMTP-SUB"})
SMTPS_SERVICES: Final = frozenset({"SMTPS"})
POP3_SERVICES: Final = frozenset({"POP3"})
POP3S_SERVICES: Final = frozenset({"POP3S"})
IMAP_SERVICES: Final = frozenset({"IMAP"})
IMAPS_SERVICES: Final = frozenset({"IMAPS"})

SSL_LINE_SERVICES: Final = SMTPS_SERVICES | POP3S_SERVICES | IMAPS_SERVICES
PLAIN_LINE_SERVICES: Final = (
    LINE_BANNER_SERVICES | SMTP_SERVICES | POP3_SERVICES | IMAP_SERVICES
)


logger = get_logger("network.banner")


class BannerGrabber:
    """Grab service banners by reusing an already-connected TCP socket."""

    UNKNOWN = UNKNOWN_BANNER

    _ssl_context: ssl.SSLContext | None = None
    _ssl_lock = threading.Lock()

    def __init__(self) -> None:
        self._ssl_context = self._get_ssl_context()

    @classmethod
    def _get_ssl_context(cls) -> ssl.SSLContext:
        if cls._ssl_context is not None:
            return cls._ssl_context

        with cls._ssl_lock:
            if cls._ssl_context is None:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                cls._ssl_context = context

        return cls._ssl_context

    def grab(self, sock: socket.socket, host: str, port: int, service: str) -> str:
        """Return a banner string for *service*, or ``Unknown`` on failure."""
        if sock.fileno() < 0:
            return UNKNOWN_BANNER

        try:
            sock.settimeout(BANNER_GRAB_TIMEOUT_SECONDS)
            banner = self._grab_for_service(sock, host, service)
            if banner:
                return banner

            if self._supports_banner_grab(service):
                logger.warning(
                    "Banner grab returned no data for %s:%d (%s)",
                    host,
                    port,
                    service,
                )
            return UNKNOWN_BANNER
        except (OSError, ssl.SSLError, UnicodeDecodeError, TimeoutError) as exc:
            logger.warning(
                "Banner grab failed for %s:%d (%s): %s",
                host,
                port,
                service,
                exc,
            )
            return UNKNOWN_BANNER

    @staticmethod
    def _supports_banner_grab(service: str) -> bool:
        return service in (
            HTTP_SERVICES
            | HTTPS_SERVICES
            | PLAIN_LINE_SERVICES
            | SSL_LINE_SERVICES
        )

    def _grab_for_service(
        self, sock: socket.socket, host: str, service: str
    ) -> str:
        if service in HTTP_SERVICES:
            return self._grab_http(sock, host, use_tls=False)
        if service in HTTPS_SERVICES:
            return self._grab_http(sock, host, use_tls=True)
        if service in PLAIN_LINE_SERVICES:
            return self._read_line_banner(sock)
        if service in SSL_LINE_SERVICES:
            return self._read_tls_line_banner(sock, host)
        return ""

    def _wrap_tls(self, sock: socket.socket, host: str) -> ssl.SSLSocket:
        return self._ssl_context.wrap_socket(sock, server_hostname=host)

    def _recv_until_headers_complete(self, sock: socket.socket) -> str:
        buffer = bytearray()
        try:
            while len(buffer) < BANNER_READ_BUFFER_SIZE:
                chunk = sock.recv(BANNER_READ_BUFFER_SIZE - len(buffer))
                if not chunk:
                    break
                buffer.extend(chunk)
                if b"\r\n\r\n" in buffer:
                    break
        except (socket.timeout, ConnectionResetError, BrokenPipeError, OSError):
            pass

        return buffer.decode("utf-8", errors="replace").strip() if buffer else ""

    def _recv_first_line(self, sock: socket.socket) -> str:
        buffer = bytearray()
        try:
            while len(buffer) < BANNER_READ_BUFFER_SIZE:
                chunk = sock.recv(
                    min(BANNER_READ_BUFFER_SIZE - len(buffer), BANNER_LINE_READ_CHUNK)
                )
                if not chunk:
                    break
                buffer.extend(chunk)
                if b"\n" in buffer:
                    break
        except (socket.timeout, ConnectionResetError, BrokenPipeError, OSError):
            pass

        if not buffer:
            return ""

        text = buffer.decode("utf-8", errors="replace")
        return text.split("\r\n", 1)[0].split("\n", 1)[0].strip()

    @staticmethod
    def _extract_server_header(response: str) -> str | None:
        for line in response.split("\r\n"):
            if line.lower().startswith("server:"):
                value = line.split(":", 1)[1].strip()
                return value or None
        return None

    @staticmethod
    def _normalize_banner(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()[:BANNER_MAX_LENGTH]

    def _grab_http(self, sock: socket.socket, host: str, *, use_tls: bool) -> str:
        transport: socket.socket | ssl.SSLSocket = sock
        tls_wrapped = False

        try:
            if use_tls:
                transport = self._wrap_tls(sock, host)
                tls_wrapped = True

            request = (
                f"HEAD / HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"User-Agent: {BANNER_HTTP_USER_AGENT}\r\n"
                f"Connection: close\r\n\r\n"
            )
            transport.sendall(request.encode("ascii"))

            response = self._recv_until_headers_complete(transport)
            server = self._extract_server_header(response)
            return self._normalize_banner(server) if server else ""

        except (OSError, ssl.SSLError, UnicodeDecodeError, TimeoutError) as exc:
            logger.warning(
                "HTTP banner grab failed for %s (%s): %s",
                host,
                "TLS" if use_tls else "plain",
                exc,
            )
            return ""
        finally:
            if tls_wrapped:
                close_socket(transport)

    def _read_line_banner(self, sock: socket.socket) -> str:
        try:
            line = self._recv_first_line(sock)
            return self._normalize_banner(line) if line else ""
        except (OSError, UnicodeDecodeError, TimeoutError) as exc:
            logger.warning("Line banner read failed: %s", exc)
            return ""

    def _read_tls_line_banner(self, sock: socket.socket, host: str) -> str:
        tls_sock: ssl.SSLSocket | None = None
        try:
            tls_sock = self._wrap_tls(sock, host)
            line = self._recv_first_line(tls_sock)
            return self._normalize_banner(line) if line else ""
        except (OSError, ssl.SSLError, UnicodeDecodeError, TimeoutError) as exc:
            logger.warning(
                "TLS line banner read failed for %s: %s",
                host,
                exc,
            )
            return ""
        finally:
            close_socket(tls_sock)
