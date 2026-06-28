"""Domain models shared between the scanner engine and UI."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from portscanner.config import DATETIME_FORMAT, SUMMARY_PLACEHOLDER


@dataclass(frozen=True, slots=True)
class ScanSummary:
    """Metadata describing a single port-scan run."""

    target: str
    resolved_ip: str
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float | None = None
    total_ports_scanned: int = 0
    open_ports_found: int = 0
    stopped: bool = False

    @classmethod
    def empty(cls) -> ScanSummary:
        """Return a blank summary shown before the first scan."""
        now = datetime.now()
        return cls(
            target=SUMMARY_PLACEHOLDER,
            resolved_ip=SUMMARY_PLACEHOLDER,
            start_time=now,
            end_time=None,
        )

    @classmethod
    def started(cls, target: str, resolved_ip: str, start_time: datetime) -> ScanSummary:
        """Return a summary captured when scanning begins."""
        return cls(
            target=target,
            resolved_ip=resolved_ip,
            start_time=start_time,
        )

    def finished(
        self,
        *,
        end_time: datetime,
        total_ports_scanned: int,
        open_ports_found: int,
        stopped: bool,
    ) -> ScanSummary:
        """Return a copy populated with completion metrics."""
        duration = max((end_time - self.start_time).total_seconds(), 0.0)
        return replace(
            self,
            end_time=end_time,
            duration_seconds=duration,
            total_ports_scanned=total_ports_scanned,
            open_ports_found=open_ports_found,
            stopped=stopped,
        )

    def format_start_time(self) -> str:
        return self.start_time.strftime(DATETIME_FORMAT)

    def format_end_time(self) -> str:
        if self.end_time is None:
            return SUMMARY_PLACEHOLDER
        return self.end_time.strftime(DATETIME_FORMAT)

    def format_duration(self) -> str:
        if self.duration_seconds is None:
            return SUMMARY_PLACEHOLDER
        return _format_elapsed(self.duration_seconds)

    def csv_metadata_rows(self) -> list[tuple[str, str]]:
        """Return key/value rows written above port results in CSV exports."""
        return [
            ("Target", self.target),
            ("Resolved IP", self.resolved_ip),
            ("Scan Start Time", self.format_start_time()),
            ("Scan End Time", self.format_end_time()),
            ("Scan Duration", self.format_duration()),
            ("Total Ports Scanned", str(self.total_ports_scanned)),
            ("Open Ports Found", str(self.open_ports_found)),
        ]


def _format_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining = seconds % 60
    if minutes < 60:
        return f"{minutes}m {remaining:.1f}s"

    hours = int(minutes // 60)
    minutes %= 60
    return f"{hours}h {minutes}m {remaining:.0f}s"
