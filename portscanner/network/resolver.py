"""Target hostname and IP resolution."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass

from portscanner.logging_config import get_logger

logger = get_logger("network.resolver")


@dataclass(frozen=True, slots=True)
class ResolvedTarget:
    """A scan target resolved to a concrete network address."""

    query: str
    address: str
    family: socket.AddressFamily

    @property
    def connect_host(self) -> str:
        """Host string used for banner-grab protocol headers."""
        return self.query


def resolve_host(target: str) -> ResolvedTarget | None:
    """Resolve *target* to an IPv4/IPv6 address suitable for TCP scanning."""
    normalized = target.strip()
    if not normalized:
        return None

    ipv4 = _parse_ipv4(normalized)
    if ipv4 is not None:
        return ResolvedTarget(
            query=normalized,
            address=ipv4,
            family=socket.AF_INET,
        )

    ipv6 = _parse_ipv6(normalized)
    if ipv6 is not None:
        return ResolvedTarget(
            query=normalized,
            address=ipv6,
            family=socket.AF_INET6,
        )

    return _resolve_hostname(normalized)


def resolve_target(target: str) -> str | None:
    """Legacy helper returning the resolved IP address string."""
    resolved = resolve_host(target)
    return resolved.address if resolved else None


def _parse_ipv4(value: str) -> str | None:
    try:
        return str(ipaddress.IPv4Address(value))
    except ipaddress.AddressValueError:
        return None


def _parse_ipv6(value: str) -> str | None:
    try:
        return str(ipaddress.IPv6Address(value))
    except ipaddress.AddressValueError:
        return None


def _resolve_hostname(hostname: str) -> ResolvedTarget | None:
    try:
        results = socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        logger.warning(
            "DNS resolution failed for target '%s': %s",
            hostname,
            exc,
        )
        return None

    for family in (socket.AF_INET, socket.AF_INET6):
        for info in results:
            if info[0] != family:
                continue
            address = info[4][0]
            return ResolvedTarget(
                query=hostname,
                address=address,
                family=family,
            )

    logger.warning(
        "DNS resolution returned no usable addresses for target '%s'",
        hostname,
    )
    return None
