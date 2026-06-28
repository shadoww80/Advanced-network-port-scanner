"""Network utilities for host resolution, service lookup, and banner grabbing."""

from portscanner.network.banner import BannerGrabber
from portscanner.network.resolver import resolve_host
from portscanner.network.services import COMMON_SERVICES, lookup_service
from portscanner.network.socket_utils import close_socket

__all__ = [
    "BannerGrabber",
    "COMMON_SERVICES",
    "close_socket",
    "lookup_service",
    "resolve_host",
]
