#!/usr/bin/env python3
"""
ssl_cert_expiry.py
Checks SSL certificate expiry dates for a list of domains.
Alerts if a certificate expires within the threshold (default: 30 days).
Usage: python ssl_cert_expiry.py --domains example.com google.com --warn-days 30
"""

import argparse
import socket
import ssl
from datetime import datetime

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def get_cert_expiry(domain: str, port: int = 443) -> dict:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, port))
            cert = s.getpeercert()
            expiry_str = cert["notAfter"]
            expiry = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
            days_left = (expiry - datetime.utcnow()).days
            return {"domain": domain, "expiry": expiry.strftime("%Y-%m-%d"), "days_left": days_left, "error": None}
    except Exception as e:
        return {"domain": domain, "expiry": None, "days_left": None, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Check SSL certificate expiry")
    parser.add_argument("--domains", nargs="+", required=True, help="Domains to check")
    parser.add_argument("--warn-days", type=int, default=30, help="Warn if expiring within N days")
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"  SSL Certificate Expiry Check - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}\n")

    alerts = []
    for domain in args.domains:
        result = get_cert_expiry(domain)
        if result["error"]:
            print(f"{RED}[ERROR  ]{RESET} {domain:35} Error: {result['error']}")
        elif result["days_left"] <= args.warn_days:
            color = RED if result["days_left"] <= 7 else YELLOW
            print(f"{color}[WARNING]{RESET} {domain:35} expires {result['expiry']} ({result['days_left']} days left)")
            alerts.append(result)
        else:
            print(f"{GREEN}[OK     ]{RESET} {domain:35} expires {result['expiry']} ({result['days_left']} days left)")

    if alerts:
        print(f"\n{YELLOW}ALERT: {len(alerts)} certificate(s) expiring soon!{RESET}")


if __name__ == "__main__":
    main()
