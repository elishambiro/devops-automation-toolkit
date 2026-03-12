#!/usr/bin/env python3
"""
iam_access_key_audit.py
Finds IAM access keys that are old or haven't been used recently.
Critical for security hygiene - old keys are a common attack vector.
Usage: python iam_access_key_audit.py --max-age 90 --max-unused 30
"""

import argparse
from datetime import datetime, timezone

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"


def days_since(dt) -> int:
    if dt is None:
        return -1
    if hasattr(dt, 'tzinfo') and dt.tzinfo:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.utcnow()
    return (now - dt).days


def main():
    parser = argparse.ArgumentParser(description="Audit IAM access key age and usage")
    parser.add_argument("--max-age", type=int, default=90, help="Warn if key older than N days")
    parser.add_argument("--max-unused", type=int, default=30, help="Warn if not used in N days")
    parser.add_argument("--profile", help="AWS profile")
    args = parser.parse_args()

    print(f"\n{'='*75}")
    print("  IAM Access Key Audit")
    print(f"  Max age: {args.max_age} days | Max unused: {args.max_unused} days")
    print(f"{'='*75}\n")

    if not HAS_BOTO3:
        print(f"{YELLOW}[DEMO MODE]{RESET}\n")
        data = [
            {"user": "deploy-user", "key_id": "AKIA...ABC", "status": "Active",
             "age_days": 45, "last_used_days": 2, "issue": None},
            {"user": "old-service", "key_id": "AKIA...DEF", "status": "Active",
             "age_days": 120, "last_used_days": 95, "issue": "OLD + UNUSED"},
            {"user": "ci-user", "key_id": "AKIA...GHI", "status": "Inactive",
             "age_days": 200, "last_used_days": -1, "issue": "INACTIVE"},
        ]
        print(f"{'USER':25} {'KEY ID':15} {'STATUS':10} {'AGE':8} {'LAST USED':12} ISSUE")
        print("-" * 75)
        for d in data:
            color = RED if d["issue"] else GREEN
            last_used = f"{d['last_used_days']}d ago" if d["last_used_days"] >= 0 else "Never"
            print(f"{color}{d['user']:25} {d['key_id']:15} {d['status']:10} {d['age_days']:>5}d   "
                  f"{last_used:12} {d['issue'] or 'OK'}{RESET}")
        return

    try:
        session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
        iam = session.client("iam")
        users = iam.list_users()["Users"]
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        return

    print(f"{'USER':25} {'KEY ID':22} {'STATUS':10} {'AGE':8} {'LAST USED':12} ISSUES")
    print("-" * 80)

    findings = []
    for user in users:
        username = user["UserName"]
        keys = iam.list_access_keys(UserName=username)["AccessKeyMetadata"]
        for key in keys:
            age = days_since(key["CreateDate"])
            try:
                lu = iam.get_access_key_last_used(AccessKeyId=key["AccessKeyId"])
                last_used_date = lu["AccessKeyLastUsed"].get("LastUsedDate")
                last_used_days = days_since(last_used_date) if last_used_date else -1
            except Exception:
                last_used_days = -1

            issues = []
            if age > args.max_age:
                issues.append(f">{args.max_age}d old")
            if last_used_days == -1:
                issues.append("never used")
            elif last_used_days > args.max_unused:
                issues.append(f"unused {last_used_days}d")
            if key["Status"] == "Inactive":
                issues.append("inactive")

            color = RED if issues else GREEN
            last_used_str = f"{last_used_days}d ago" if last_used_days >= 0 else "Never"
            issue_str = " | ".join(issues) if issues else "OK"
            print(f"{color}{username:25} {key['AccessKeyId']:22} {key['Status']:10} "
                  f"{age:>5}d   {last_used_str:12} {issue_str}{RESET}")
            if issues:
                findings.append(username)

    print(f"\n{len(findings)} key(s) require attention.")


if __name__ == "__main__":
    main()
