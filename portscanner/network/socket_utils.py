"""Shared socket lifecycle helpers."""

from __future__ import annotations

import socket
import ssl


def close_socket(sock: socket.socket | ssl.SSLSocket | None) -> None:
    """Shut down and close a socket, ignoring errors from already-closed handles."""
    if sock is None:
        return

    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass

    try:
        sock.close()
    except OSError:
        pass
