"""Backward-compatible constant re-exports.

Prefer importing settings directly from ``portscanner.config``.
"""

from portscanner.config import (
    APP_TITLE,
    CSV_HEADERS,
    CSV_SUMMARY_TITLE,
    DATETIME_FORMAT,
    DEFAULT_END_PORT,
    DEFAULT_START_PORT,
    MAX_PORT,
    MIN_PORT,
    OPEN_STATUS,
    SUMMARY_PLACEHOLDER,
    TABLE_COLUMNS,
    UNKNOWN_BANNER,
    UNKNOWN_SERVICE,
    WINDOW_GEOMETRY,
    WINDOW_MIN_SIZE,
)

__all__ = [
    "APP_TITLE",
    "CSV_HEADERS",
    "CSV_SUMMARY_TITLE",
    "DATETIME_FORMAT",
    "DEFAULT_END_PORT",
    "DEFAULT_START_PORT",
    "MAX_PORT",
    "MIN_PORT",
    "OPEN_STATUS",
    "SUMMARY_PLACEHOLDER",
    "TABLE_COLUMNS",
    "UNKNOWN_BANNER",
    "UNKNOWN_SERVICE",
    "WINDOW_GEOMETRY",
    "WINDOW_MIN_SIZE",
]
