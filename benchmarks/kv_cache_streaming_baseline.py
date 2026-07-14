#!/usr/bin/env python3
"""Baseline local TCP streaming latency for 128k+ token-sized KV-cache payloads."""

from __future__ import annotations

import argparse
import socket
import threading
from time import perf_counter


def _server(port_holder: list[int], expected_bytes: int) -> None:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        port_holder.append(server.getsockname()[1])
        conn, _ = server.accept()
        with conn:
            received = 0
            while received < expected_bytes:
                chunk = conn.recv(1024 * 1024)
                if not chunk:
                    break
                received += len(chunk)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tokens", type=int, default=128_000)
    parser.add_argument("--bytes-per-token", type=int, default=64)
    args = parser.parse_args()
    payload_bytes = args.tokens * args.bytes_per_token
    payload = b"0" * payload_bytes
    ports: list[int] = []
    thread = threading.Thread(target=_server, args=(ports, payload_bytes), daemon=True)
    thread.start()
    while not ports:
        pass
    start = perf_counter()
    with socket.create_connection(("127.0.0.1", ports[0])) as client:
        client.sendall(payload)
    thread.join(timeout=10)
    duration_ms = (perf_counter() - start) * 1000
    print(f"kv_cache_payload_bytes {payload_bytes}")
    print(f"kv_cache_stream_duration_ms {duration_ms}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
