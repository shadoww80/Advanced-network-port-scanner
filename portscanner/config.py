"""Centralized application configuration.

All tunable settings for the Advanced Network Port Scanner live here.
Import values from this module instead of hardcoding them elsewhere.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Scan engine
# ---------------------------------------------------------------------------

# TCP connect timeout in seconds applied to each port probe.
SCAN_CONNECT_TIMEOUT_SECONDS: float = 0.5

# Maximum number of concurrent worker threads used during a scan.
SCAN_MAX_WORKER_THREADS: int = 100

# Upper bound on queued scan tasks, expressed as a multiple of worker threads.
SCAN_PENDING_TASKS_MULTIPLIER: int = 4

# Minimum interval in seconds between GUI progress bar updates.
SCAN_PROGRESS_UPDATE_INTERVAL_SECONDS: float = 0.05

# Timeout in seconds when waiting for the next completed worker task.
SCAN_WORKER_POLL_TIMEOUT_SECONDS: float = 0.5

# ---------------------------------------------------------------------------
# Port range
# ---------------------------------------------------------------------------

# Lowest valid TCP port number.
MIN_PORT: int = 1

# Highest valid TCP port number.
MAX_PORT: int = 65535

# Default start port shown in the UI and used for new scans.
DEFAULT_START_PORT: int = 1

# Default end port shown in the UI and used for new scans.
DEFAULT_END_PORT: int = 1024

# ---------------------------------------------------------------------------
# Banner grabbing
# ---------------------------------------------------------------------------

# Socket read timeout in seconds while grabbing a service banner.
BANNER_GRAB_TIMEOUT_SECONDS: float = 2.0

# Maximum number of bytes read while waiting for a banner response.
BANNER_READ_BUFFER_SIZE: int = 4096

# Chunk size in bytes for line-oriented banner reads.
BANNER_LINE_READ_CHUNK: int = 512

# Maximum stored banner length after normalization.
BANNER_MAX_LENGTH: int = 200

# User-Agent header sent with HTTP/HTTPS banner requests.
BANNER_HTTP_USER_AGENT: str = "PortScanner/1.0"

# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

# Character encoding used when writing exported CSV files.
CSV_ENCODING: str = "utf-8"

# Default file extension suggested by the export dialog.
CSV_DEFAULT_EXTENSION: str = ".csv"

# Title shown in the export file dialog window.
CSV_DIALOG_TITLE: str = "Export Scan Results"

# File-type filters offered by the export file dialog.
CSV_FILE_TYPES: tuple[tuple[str, str], ...] = (
    ("CSV files", "*.csv"),
    ("All files", "*.*"),
)

# Prefix used for auto-generated export filenames.
CSV_INITIAL_FILENAME_PREFIX: str = "port_scan_"

# Timestamp format appended to auto-generated export filenames.
CSV_TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"

# Heading written above scan metadata rows in exported CSV files.
CSV_SUMMARY_TITLE: str = "Scan Summary"

# Column headers for port result rows in exported CSV files.
CSV_HEADERS: tuple[str, ...] = (
    "Port",
    "Status",
    "Service",
    "Response Time",
    "Banner",
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

# Directory where log files are stored (created automatically if missing).
LOG_DIRECTORY: Path = Path("logs")

# Log file name inside LOG_DIRECTORY.
LOG_FILE_NAME: str = "scanner.log"

# Full path to the active application log file.
LOG_FILE_PATH: Path = LOG_DIRECTORY / LOG_FILE_NAME

# Root logger namespace for the application.
LOG_ROOT_LOGGER_NAME: str = "portscanner"

# Default logging level for file output (INFO, WARNING, ERROR, etc.).
LOG_LEVEL: str = "INFO"

# Log message format written to the log file.
LOG_FORMAT: str = (
    "%(asctime)s | %(levelname)-8s | %(threadName)s | %(name)s | %(message)s"
)

# Timestamp format used inside LOG_FORMAT.
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# File encoding used when writing log output.
LOG_FILE_ENCODING: str = "utf-8"

# ---------------------------------------------------------------------------
# Application window
# ---------------------------------------------------------------------------

# Main window title displayed in the title bar.
APP_TITLE: str = "Advanced Network Port Scanner"

# Initial window size expressed as "widthxheight".
WINDOW_GEOMETRY: str = "1200x820"

# Minimum window width and height in pixels.
WINDOW_MIN_WIDTH: int = 1000
WINDOW_MIN_HEIGHT: int = 700

# ---------------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------------

# Treeview column identifiers mapped to heading text and pixel width.
TABLE_COLUMNS: dict[str, tuple[str, int]] = {
    "port": ("PORT", 80),
    "status": ("STATUS", 100),
    "service": ("SERVICE", 160),
    "response": ("RESPONSE TIME", 130),
    "banner": ("BANNER", 380),
}

# ---------------------------------------------------------------------------
# Scan result labels and formatting
# ---------------------------------------------------------------------------

# Placeholder shown when a banner cannot be identified.
UNKNOWN_BANNER: str = "Unknown"

# Placeholder shown when a service name is not recognized.
UNKNOWN_SERVICE: str = "Unknown"

# Status text recorded for open ports in the results table.
OPEN_STATUS: str = "OPEN"

# Placeholder shown in the summary panel for empty values.
SUMMARY_PLACEHOLDER: str = "—"

# Datetime format used in the summary panel and CSV metadata.
DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Derived values (computed from settings above)
# ---------------------------------------------------------------------------

# Maximum queued scan tasks submitted ahead of worker completion.
SCAN_MAX_PENDING_TASKS: int = (
    SCAN_MAX_WORKER_THREADS * SCAN_PENDING_TASKS_MULTIPLIER
)

# Minimum window size tuple consumed by Tkinter geometry helpers.
WINDOW_MIN_SIZE: tuple[int, int] = (WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

# Legacy aliases preserved for backward-compatible imports.
DEFAULT_TIMEOUT: float = SCAN_CONNECT_TIMEOUT_SECONDS
DEFAULT_WORKERS: int = SCAN_MAX_WORKER_THREADS
