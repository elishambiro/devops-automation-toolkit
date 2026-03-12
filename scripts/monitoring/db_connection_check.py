#!/usr/bin/env python3
"""
db_connection_check.py
Tests connectivity to databases: PostgreSQL, MySQL, Redis, MongoDB.
Useful in CI pipelines to verify DB is up before running tests.
Usage: python db_connection_check.py --type postgres --host localhost --port 5432
       python db_connection_check.py --config db_targets.json
"""

import argparse
import json
import socket
import sys
import time

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

DB_DEFAULTS = {
    "postgres": {"port": 5432, "banner": b""},
    "mysql": {"port": 3306, "banner": b""},
    "redis": {"port": 6379, "banner": b"*1\r\n$4\r\nPING\r\n"},
    "mongodb": {"port": 27017, "banner": b""},
    "elastic": {"port": 9200, "banner": b""},
}


def tcp_check(host: str, port: int, timeout: float = 5.0) -> dict:
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency = round((time.time() - start) * 1000, 2)
            return {"status": "UP", "latency_ms": latency, "error": None}
    except socket.timeout:
        return {"status": "TIMEOUT", "latency_ms": None, "error": "Connection timed out"}
    except ConnectionRefusedError:
        return {"status": "REFUSED", "latency_ms": None, "error": "Connection refused"}
    except OSError as e:
        return {"status": "ERROR", "latency_ms": None, "error": str(e)}


def redis_ping(host: str, port: int, password: str = None, timeout: float = 5.0) -> dict:
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            if password:
                s.sendall(f"*2\r\n$4\r\nAUTH\r\n${len(password)}\r\n{password}\r\n".encode())
                s.recv(128)
            s.sendall(b"PING\r\n")
            resp = s.recv(128).decode()
            if "+PONG" in resp:
                return {"status": "UP", "latency_ms": 0, "error": None}
        return {"status": "ERROR", "latency_ms": None, "error": "Unexpected response"}
    except Exception as e:
        return {"status": "ERROR", "latency_ms": None, "error": str(e)}


def check_db(db_type: str, host: str, port: int = None) -> dict:
    port = port or DB_DEFAULTS.get(db_type, {}).get("port", 0)
    if db_type == "redis":
        result = redis_ping(host, port)
    else:
        result = tcp_check(host, port)
    result["type"] = db_type
    result["host"] = host
    result["port"] = port
    return result


def main():
    parser = argparse.ArgumentParser(description="Database connectivity checker")
    parser.add_argument("--type", choices=list(DB_DEFAULTS.keys()), help="DB type")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int)
    parser.add_argument("--config", help="JSON config with multiple targets")
    args = parser.parse_args()

    targets = []
    if args.config:
        with open(args.config) as f:
            targets = json.load(f).get("databases", [])
    elif args.type:
        targets = [{"type": args.type, "host": args.host, "port": args.port}]
    else:
        # Demo: check common local services
        targets = [
            {"type": "postgres", "host": "localhost"},
            {"type": "redis", "host": "localhost"},
            {"type": "mysql", "host": "localhost"},
        ]

    print(f"\n{'='*65}")
    print("  Database Connectivity Check")
    print(f"{'='*65}\n")
    print(f"{'TYPE':12} {'HOST':25} {'PORT':6} {'STATUS':10} {'LATENCY'}")
    print("-" * 65)

    failed = []
    for t in targets:
        r = check_db(t["type"], t["host"], t.get("port"))
        color = GREEN if r["status"] == "UP" else RED
        latency = f"{r['latency_ms']}ms" if r["latency_ms"] else r.get("error", "N/A")
        print(f"{color}{r['type']:12} {r['host']:25} {r['port']:<6} {r['status']:10} {latency}{RESET}")
        if r["status"] != "UP":
            failed.append(r)

    print(f"\nResult: {len(targets) - len(failed)}/{len(targets)} databases reachable")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
