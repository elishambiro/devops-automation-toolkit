#!/usr/bin/env python3
"""
security_group_audit.py
Finds AWS security groups with overly permissive rules (0.0.0.0/0 or ::/0).
Critical for security auditing and compliance.
Usage: python security_group_audit.py --profile myprofile --region us-east-1
"""

import argparse
from datetime import datetime

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

DANGEROUS_CIDRS = {"0.0.0.0/0", "::/0"}
SENSITIVE_PORTS = {22: "SSH", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL",
                   6379: "Redis", 27017: "MongoDB", 9200: "Elasticsearch"}


def is_open_to_world(rule: dict) -> bool:
    for cidr in rule.get("IpRanges", []):
        if cidr.get("CidrIp") in DANGEROUS_CIDRS:
            return True
    for cidr in rule.get("Ipv6Ranges", []):
        if cidr.get("CidrIpv6") in DANGEROUS_CIDRS:
            return True
    return False


def check_rule_severity(rule: dict) -> str:
    port_from = rule.get("FromPort", 0)
    port_to = rule.get("ToPort", 65535)
    if port_from == 0 and port_to == 65535:
        return "CRITICAL"
    for port in SENSITIVE_PORTS:
        if port_from <= port <= port_to:
            return "HIGH"
    return "MEDIUM"


def print_demo():
    print(f"\n{YELLOW}[DEMO MODE] Showing sample findings{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="Audit AWS security groups for open rules")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--severity", choices=["CRITICAL", "HIGH", "MEDIUM"], help="Min severity to show")
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print(f"  Security Group Audit | {args.region} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}\n")

    if not HAS_BOTO3:
        print_demo()
        findings = [
            {"sg_id": "sg-0abc123", "sg_name": "web-sg", "direction": "ingress",
             "port": "80-80", "protocol": "tcp", "severity": "MEDIUM", "service": "HTTP"},
            {"sg_id": "sg-0def456", "sg_name": "admin-sg", "direction": "ingress",
             "port": "22-22", "protocol": "tcp", "severity": "HIGH", "service": "SSH"},
            {"sg_id": "sg-0ghi789", "sg_name": "old-sg", "direction": "ingress",
             "port": "0-65535", "protocol": "-1", "severity": "CRITICAL", "service": "ALL"},
        ]
    else:
        try:
            session = (boto3.Session(profile_name=args.profile, region_name=args.region)
                       if args.profile else boto3.Session(region_name=args.region))
            ec2 = session.client("ec2")
            sgs = ec2.describe_security_groups()["SecurityGroups"]
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
            return

        findings = []
        for sg in sgs:
            for rule in sg.get("IpPermissions", []):
                if is_open_to_world(rule):
                    severity = check_rule_severity(rule)
                    port_from = rule.get("FromPort", "ALL")
                    port_to = rule.get("ToPort", "ALL")
                    port_str = f"{port_from}-{port_to}" if port_from != "ALL" else "ALL"
                    service = SENSITIVE_PORTS.get(port_from, "")
                    findings.append({
                        "sg_id": sg["GroupId"], "sg_name": sg.get("GroupName", "-"),
                        "direction": "ingress", "port": port_str,
                        "protocol": rule.get("IpProtocol", "-"),
                        "severity": severity, "service": service
                    })

    severity_filter = args.severity
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}

    for f in findings:
        if severity_filter and f["severity"] != severity_filter:
            continue
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        color = RED if f["severity"] == "CRITICAL" else (YELLOW if f["severity"] == "HIGH" else "\033[93m")
        service_str = f" [{f['service']}]" if f["service"] else ""
        print(f"{color}[{f['severity']:8}]{RESET} {f['sg_id']:15} {f['sg_name']:20} "
              f"{f['direction']:8} port={f['port']:12}{service_str}")

    print("\nSummary:")
    print(f"  {RED}CRITICAL: {counts['CRITICAL']}{RESET}")
    print(f"  {YELLOW}HIGH:     {counts['HIGH']}{RESET}")
    print(f"  MEDIUM:   {counts['MEDIUM']}")

    if counts["CRITICAL"] + counts["HIGH"] > 0:
        print(f"\n{RED}ACTION REQUIRED: Review and restrict open security group rules!{RESET}")
    else:
        print(f"\n{GREEN}No critical/high severity findings.{RESET}")


if __name__ == "__main__":
    main()
