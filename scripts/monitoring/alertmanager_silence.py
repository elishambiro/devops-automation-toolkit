#!/usr/bin/env python3
"""
alertmanager_silence.py
Creates, lists, and deletes silences in Prometheus Alertmanager.
Useful during planned maintenance to suppress known alerts.
Usage: python alertmanager_silence.py --action create --matcher alertname=HighCPU --duration 2h
       python alertmanager_silence.py --action list
       python alertmanager_silence.py --action delete --id <silence-id>
"""

import argparse
import json
from datetime import datetime, timedelta, timezone

import requests

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def parse_duration(duration_str: str) -> timedelta:
    units = {"m": "minutes", "h": "hours", "d": "days"}
    unit = duration_str[-1]
    value = int(duration_str[:-1])
    return timedelta(**{units[unit]: value})


def list_silences(base_url: str):
    resp = requests.get(f"{base_url}/api/v2/silences", timeout=10)
    resp.raise_for_status()
    silences = [s for s in resp.json() if s["status"]["state"] == "active"]

    print(f"\n{CYAN}Active Silences ({len(silences)}){RESET}\n")
    if not silences:
        print("  No active silences.")
        return

    for s in silences:
        matchers = ", ".join(f"{m['name']}={m['value']}" for m in s["matchers"])
        ends = s["endsAt"][:19].replace("T", " ")
        print(f"  ID:       {s['id']}")
        print(f"  Matchers: {YELLOW}{matchers}{RESET}")
        print(f"  Ends at:  {ends}")
        print(f"  Comment:  {s.get('comment', '-')}\n")


def create_silence(base_url: str, matchers: list, duration: str, comment: str, author: str):
    now = datetime.now(timezone.utc)
    ends_at = now + parse_duration(duration)

    payload = {
        "matchers": [
            {"name": m.split("=")[0], "value": m.split("=")[1], "isRegex": False}
            for m in matchers
        ],
        "startsAt": now.isoformat(),
        "endsAt": ends_at.isoformat(),
        "createdBy": author,
        "comment": comment
    }

    resp = requests.post(f"{base_url}/api/v2/silences", json=payload, timeout=10)
    resp.raise_for_status()
    silence_id = resp.json()["silenceID"]
    print(f"{GREEN}Silence created: {silence_id}{RESET}")
    print(f"  Active until: {ends_at.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Matchers: {', '.join(matchers)}")


def delete_silence(base_url: str, silence_id: str):
    resp = requests.delete(f"{base_url}/api/v2/silence/{silence_id}", timeout=10)
    resp.raise_for_status()
    print(f"{GREEN}Silence {silence_id} deleted successfully.{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Manage Alertmanager silences")
    parser.add_argument("--url", default="http://localhost:9093", help="Alertmanager URL")
    parser.add_argument("--action", required=True, choices=["list", "create", "delete"])
    parser.add_argument("--matcher", nargs="+", help="Matchers (e.g. alertname=HighCPU env=prod)")
    parser.add_argument("--duration", default="2h", help="Duration (e.g. 30m, 2h, 1d)")
    parser.add_argument("--comment", default="Maintenance silence", help="Silence comment")
    parser.add_argument("--author", default="devops-toolkit", help="Created by")
    parser.add_argument("--id", help="Silence ID (for delete)")
    args = parser.parse_args()

    try:
        if args.action == "list":
            list_silences(args.url)
        elif args.action == "create":
            if not args.matcher:
                print(f"{RED}--matcher required for create action{RESET}")
                return
            create_silence(args.url, args.matcher, args.duration, args.comment, args.author)
        elif args.action == "delete":
            if not args.id:
                print(f"{RED}--id required for delete action{RESET}")
                return
            delete_silence(args.url, args.id)
    except requests.exceptions.ConnectionError:
        print(f"{RED}Cannot connect to Alertmanager at {args.url}{RESET}")
        print("Make sure Alertmanager is running (default: http://localhost:9093)")
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")


if __name__ == "__main__":
    main()
