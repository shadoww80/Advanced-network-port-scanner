"""Shared type aliases for scanner callbacks."""

from __future__ import annotations

from typing import Callable, TypeAlias

from portscanner.models import ScanSummary

ProgressCallback: TypeAlias = Callable[[float], None]
ResultCallback: TypeAlias = Callable[[int, str, str, str, str], None]
StatusCallback: TypeAlias = Callable[[str], None]
ScanStartedCallback: TypeAlias = Callable[[ScanSummary], None]
CompleteCallback: TypeAlias = Callable[[ScanSummary], None]
