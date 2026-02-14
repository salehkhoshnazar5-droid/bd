from __future__ import annotations

import argparse
import socket
import sys


def resolve(host: str, port: int) -> list[str]:
    records = socket.getaddrinfo(host, port)
    return sorted({record[4][0] for record in records})


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether a hostname resolves")
    parser.add_argument("host", help="Hostname to resolve (example: kerman_bd)")
    parser.add_argument("--port", type=int, default=8011, help="Port used for getaddrinfo")
    args = parser.parse_args()

    try:
        addresses = resolve(args.host, args.port)
    except socket.gaierror as exc:
        print(f"ERROR: could not resolve '{args.host}': {exc}")
        return 1

    print(f"Resolved '{args.host}' -> {', '.join(addresses)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())