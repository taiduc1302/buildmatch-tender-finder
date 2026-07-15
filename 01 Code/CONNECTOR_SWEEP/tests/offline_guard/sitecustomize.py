"""Process-wide network deny guard used only by authoritative Self-Test.

Python imports ``sitecustomize`` automatically when this directory is first
on ``PYTHONPATH``.  Every Self-Test child process therefore fails before any
DNS lookup or socket connection can leave the machine.  Attempts are also
recorded outside the repository so a caught exception cannot hide them.
"""
from __future__ import annotations

import os
import socket
from pathlib import Path


if os.environ.get("TENDER_FINDER_OFFLINE_ONLY", "").strip().casefold() in {
    "1", "true", "yes",
}:
    _original_socket = socket.socket
    _log_path = os.environ.get("TENDER_FINDER_NETWORK_GUARD_LOG", "").strip()

    def _blocked(operation: str, *args, **_kwargs):
        detail = f"{operation}: {args[:2]}"
        if _log_path:
            try:
                path = Path(_log_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(detail + "\n")
            except OSError:
                pass
        raise RuntimeError(
            "TENDER_FINDER Self-Test blocked a network operation: " + detail
        )

    class OfflineBlockedSocket(_original_socket):
        def connect(self, address):
            return _blocked("socket.connect", address)

        def connect_ex(self, address):
            return _blocked("socket.connect_ex", address)

    def _blocked_create_connection(address, *args, **kwargs):
        return _blocked("socket.create_connection", address, *args, **kwargs)

    def _blocked_getaddrinfo(host, port, *args, **kwargs):
        return _blocked("socket.getaddrinfo", host, port, *args, **kwargs)

    socket.socket = OfflineBlockedSocket
    socket.create_connection = _blocked_create_connection
    socket.getaddrinfo = _blocked_getaddrinfo
