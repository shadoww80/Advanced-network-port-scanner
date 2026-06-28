"""Backward-compatible scanner module shim."""

from portscanner.config import DEFAULT_TIMEOUT, DEFAULT_WORKERS
from portscanner.core.scanner import (
    PortScanner,
    detect_service,
    resolve_target,
)
from portscanner.network.services import COMMON_SERVICES

__all__ = [
    "COMMON_SERVICES",
    "DEFAULT_TIMEOUT",
    "DEFAULT_WORKERS",
    "PortScanner",
    "detect_service",
    "resolve_target",
]
