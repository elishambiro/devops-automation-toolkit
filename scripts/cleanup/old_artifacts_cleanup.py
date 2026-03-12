#!/usr/bin/env python3
"""
old_artifacts_cleanup.py
Deletes build artifacts (*.zip, *.tar.gz, *.jar, *.war, *.whl, dist/) older than N days.
Usage: python old_artifacts_cleanup.py --dir ./builds --days 30 --dry-run
"""

import argparse
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

ARTIFACT_PATTERNS = ["*.zip", "*.tar.gz", "*.tar.bz2", "*.jar", "*.war",
                     "*.whl", "*.egg", "*.rpm", "*.deb", "*.exe", "*.msi"]


def human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def main():
    parser = argparse.ArgumentParser(description="Clean up old build artifacts")
    parser.add_argument("--dir", required=True, help="Directory to scan")
    parser.add_argument("--days", type=int, default=30, help="Delete files older than N days")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--extensions", nargs="+", help="Custom file extensions (e.g. .zip .tar.gz)")
    args = parser.parse_args()

    root = Path(args.dir)
    if not root.exists():
        print(f"{RED}Directory not found: {args.dir}{RESET}")
        return

    cutoff = time.time() - (args.days * 86400)
    patterns = [f"*{ext}" for ext in args.extensions] if args.extensions else ARTIFACT_PATTERNS

    print(f"\n{'='*60}")
    print(f"  Artifact Cleanup")
    print(f"  Directory: {root}")
    print(f"  Older than: {args.days} days (before {datetime.fromtimestamp(cutoff).strftime('%Y-%m-%d')})")
    if args.dry_run:
        print(f"  MODE: DRY RUN")
    print(f"{'='*60}\n")

    deleted_count = 0
    deleted_size = 0
    skipped = 0

    for pattern in patterns:
        for filepath in root.rglob(pattern):
            if not filepath.is_file():
                continue
            mtime = filepath.stat().st_mtime
            if mtime < cutoff:
                size = filepath.stat().st_size
                age_days = int((time.time() - mtime) / 86400)
                if args.dry_run:
                    print(f"{YELLOW}[DRY RUN]{RESET} {filepath} ({human_size(size)}, {age_days}d old)")
                else:
                    filepath.unlink()
                    print(f"{GREEN}Deleted:{RESET} {filepath} ({human_size(size)}, {age_days}d old)")
                deleted_count += 1
                deleted_size += size
            else:
                skipped += 1

    print(f"\nDeleted: {deleted_count} file(s) ({human_size(deleted_size)})")
    print(f"Skipped: {skipped} recent file(s)")


if __name__ == "__main__":
    main()
