"""Input validation for scan targets and port ranges."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

from portscanner.config import MAX_PORT, MIN_PORT
from portscanner.logging_config import get_logger

logger = get_logger("validation")

# RFC 1123 hostname labels: 1-63 chars, alphanumeric plus hyphen, no leading/trailing hyphen.
_HOSTNAME_LABEL = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")


class ValidationError(ValueError):
    """Raised when user input fails validation."""

    def __init__(self, user_message: str, *, log_detail: str | None = None) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        logger.warning("Validation failed: %s", log_detail or user_message)


@dataclass(frozen=True, slots=True)
class ScanInput:
    """Validated scan parameters ready for the scanner engine."""

    target: str
    start_port: int
    end_port: int


def validate_scan_form(raw_target: str, raw_start_port: str, raw_end_port: str) -> ScanInput:
    """Validate UI form values and return normalized scan input."""
    target = validate_target(raw_target)
    start_port = validate_port_input(raw_start_port, "Start port")
    end_port = validate_port_input(raw_end_port, "End port")
    validate_port_range(start_port, end_port)
    return ScanInput(target=target, start_port=start_port, end_port=end_port)


def validate_target(raw_target: str) -> str:
    """Validate an IPv4 address, IPv6 address, or hostname."""
    target = raw_target.strip()

    if not target:
        raise ValidationError(
            "Enter a target IP address or domain name.",
            log_detail="Empty scan target",
        )

    if _is_valid_ipv4(target):
        return target

    if _is_valid_ipv6(target):
        return str(ipaddress.IPv6Address(target))

    if _is_valid_hostname(target):
        return target

    raise ValidationError(
        "Enter a valid IPv4 address, IPv6 address, or domain name.",
        log_detail=f"Invalid target format: {target!r}",
    )


def validate_port_input(raw_value: str, field_name: str) -> int:
    """Parse and validate a single port field from user input."""
    text = raw_value.strip()

    if not text:
        raise ValidationError(
            f"{field_name} is required.",
            log_detail=f"Missing value for {field_name}",
        )

    if not _is_integer_text(text):
        raise ValidationError(
            f"{field_name} must be a whole number.",
            log_detail=f"Non-integer {field_name}: {raw_value!r}",
        )

    port = int(text)
    _validate_port_number(port, field_name)
    return port


def validate_port_range(start_port: int, end_port: int) -> None:
    """Validate an inclusive port range."""
    _validate_port_number(start_port, "Start port")
    _validate_port_number(end_port, "End port")

    if start_port > end_port:
        raise ValidationError(
            f"Start port ({start_port}) cannot be greater than end port ({end_port}).",
            log_detail=f"Port range out of order: {start_port} > {end_port}",
        )


def _validate_port_number(port: int, field_name: str) -> None:
    if port < MIN_PORT or port > MAX_PORT:
        raise ValidationError(
            f"{field_name} must be between {MIN_PORT} and {MAX_PORT}.",
            log_detail=f"{field_name} out of range: {port}",
        )


def _is_integer_text(value: str) -> bool:
    return value.isdigit() or (value.startswith("-") and value[1:].isdigit())


def _is_valid_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        return False
    return True


def _is_valid_ipv6(value: str) -> bool:
    try:
        ipaddress.IPv6Address(value)
    except ipaddress.AddressValueError:
        return False
    return True


def _is_valid_hostname(hostname: str) -> bool:
    candidate = hostname.rstrip(".")

    if not candidate or len(candidate) > 253:
        return False

    labels = candidate.split(".")
    return all(_HOSTNAME_LABEL.fullmatch(label) for label in labels)
