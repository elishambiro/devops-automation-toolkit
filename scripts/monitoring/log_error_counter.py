#!/usr/bin/env python3
"""
log_error_counter.py
Parses log files for ERROR/WARN/CRITICAL patterns, counts occurrences,
and shows trend over time windows.
Usage: python log_error_counter.py --file /var/log/app.log --last-minutes 60
       python log_error_counter.py --file app.log --pattern "Exception|FATAL"
"""

import argparse
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Common log timestamp patterns
TIMESTAMP_PATTERNS = [
    r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})",
    r"(\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2})",
]
LEVEL_PATTERN = re.compile(r"\b(ERROR|CRITICAL|FATAL|WARN|WARNING|INFO|DEBUG)\b", re.IGNORECASE)


def parse_line(line: str) -> dict:
    ts = None
    for pattern in TIMESTAMP_PATTERNS:
        match = re.search(pattern, line)
        if match:
            try:
                ts = datetime.fromisoformat(match.group(1).replace("T", " "))
            except Exception:
                pass
            break

    level_match = LEVEL_PATTERN.search(line)
    level = level_match.group(1).upper() if level_match else "UNKNOWN"
    return {"timestamp": ts, "level": level, "line": line.strip()}


def main():
    parser = argparse.ArgumentParser(description="Analyze log files for errors")
    parser.add_argument("--file", required=True, help="Log file to analyze")
    parser.add_argument("--last-minutes", type=int, default=60)
    parser.add_argument("--pattern", default="ERROR|CRITICAL|FATAL|WARN")
    parser.add_argument("--top-errors", type=int, default=5)
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"{RED}File not found: {args.file}{RESET}")
        return

    cutoff = datetime.now() - timedelta(minutes=args.last_minutes)
    filter_re = re.compile(args.pattern, re.IGNORECASE)

    level_counts = Counter()
    error_messages = Counter()
    hourly_counts = defaultdict(Counter)
    total_lines = 0

    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            total_lines += 1
            if not filter_re.search(line):
                continue
            parsed = parse_line(line)
            if parsed["timestamp"] and parsed["timestamp"] < cutoff:
                continue
            level_counts[parsed["level"]] += 1
            # Extract message after level for top errors
            msg = re.sub(r".*?(ERROR|WARN|CRITICAL|FATAL)\s*:?\s*", "", line, flags=re.IGNORECASE).strip()[:80]
            if msg:
                error_messages[msg] += 1
            if parsed["timestamp"]:
                hour_key = parsed["timestamp"].strftime("%H:00")
                hourly_counts[hour_key][parsed["level"]] += 1

    print(f"\n{'='*65}")
    print(f"  Log Analysis: {path.name}")
    print(f"  Period: last {args.last_minutes} minutes | Pattern: {args.pattern}")
    print(f"{'='*65}\n")

    print(f"{'LEVEL':12} {'COUNT':8} {'BAR'}")
    print("-" * 45)
    for level, count in sorted(level_counts.items(), key=lambda x: -x[1]):
        color = RED if level in ("ERROR", "CRITICAL", "FATAL") else YELLOW if level == "WARN" else GREEN
        bar = "█" * min(count, 40)
        print(f"{color}{level:12} {count:<8} {bar}{RESET}")

    if error_messages:
        print(f"\n{CYAN}Top {args.top_errors} most frequent errors:{RESET}")
        for msg, count in error_messages.most_common(args.top_errors):
            print(f"  [{count:>4}x] {msg}")

    print(f"\nTotal lines scanned: {total_lines:,}")


if __name__ == "__main__":
    main()
