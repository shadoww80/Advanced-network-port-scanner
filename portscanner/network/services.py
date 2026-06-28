"""Well-known port-to-service mappings."""

from __future__ import annotations

from portscanner.config import UNKNOWN_SERVICE

WELL_KNOWN_SERVICES: dict[int, str] = {
    20: "FTP-DATA",
    21: "FTP",
    22: "SSH",
    23: "TELNET",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    119: "NNTP",
    123: "NTP",
    135: "MS-RPC",
    137: "NETBIOS-NS",
    139: "NETBIOS-SSN",
    143: "IMAP",
    161: "SNMP",
    179: "BGP",
    194: "IRC",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    465: "SMTPS",
    514: "SYSLOG",
    587: "SMTP-SUB",
    636: "LDAPS",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "ORACLE",
    2049: "NFS",
    3306: "MYSQL",
    3389: "RDP",
    5432: "POSTGRESQL",
    5900: "VNC",
    6379: "REDIS",
    8080: "HTTP-ALT",
    8443: "HTTPS-ALT",
    9200: "ELASTICSEARCH",
    27017: "MONGODB",
}

# Backward-compatible alias used by legacy imports.
COMMON_SERVICES = WELL_KNOWN_SERVICES


def lookup_service(port: int) -> str:
    """Return the well-known service name for *port*, or ``Unknown``."""
    return WELL_KNOWN_SERVICES.get(port, UNKNOWN_SERVICE)
