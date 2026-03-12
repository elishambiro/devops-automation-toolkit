#!/usr/bin/env python3
"""
cleanup_ecr_images.py
Keeps only the last N images per ECR repository, deletes older ones.
Prevents ECR storage costs from growing unbounded.
Usage: python cleanup_ecr_images.py --keep 10 --profile myprofile --dry-run
"""

import argparse
from datetime import datetime

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def get_ecr_repos(client) -> list:
    repos = []
    paginator = client.get_paginator("describe_repositories")
    for page in paginator.paginate():
        repos.extend(page["repositories"])
    return repos


def get_images(client, repo_name: str) -> list:
    images = []
    paginator = client.get_paginator("describe_images")
    for page in paginator.paginate(repositoryName=repo_name):
        images.extend(page["imageDetails"])
    return sorted(images, key=lambda x: x.get("imagePushedAt", datetime.min), reverse=True)


def delete_images(client, repo_name: str, image_digests: list, dry_run: bool):
    if not image_digests:
        return 0
    ids = [{"imageDigest": d} for d in image_digests]
    if dry_run:
        print(f"  {YELLOW}[DRY RUN] Would delete {len(ids)} image(s){RESET}")
        return len(ids)
    response = client.batch_delete_image(repositoryName=repo_name, imageIds=ids)
    deleted = len(response.get("imageIds", []))
    failures = response.get("failures", [])
    if failures:
        print(f"  {RED}Failures: {failures}{RESET}")
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Clean up old ECR images")
    parser.add_argument("--keep", type=int, default=10, help="Number of images to keep per repo")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--repo", help="Specific repo name (default: all repos)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not HAS_BOTO3:
        print(f"{RED}boto3 not installed: pip install boto3{RESET}")
        return

    session = boto3.Session(profile_name=args.profile, region_name=args.region) if args.profile else \
              boto3.Session(region_name=args.region)
    ecr = session.client("ecr")

    repos = [{"repositoryName": args.repo}] if args.repo else get_ecr_repos(ecr)

    print(f"\n{'='*60}")
    print(f"  ECR Image Cleanup | Keep last {args.keep} per repo")
    if args.dry_run:
        print(f"  MODE: DRY RUN")
    print(f"{'='*60}\n")

    total_deleted = 0
    for repo in repos:
        name = repo["repositoryName"]
        images = get_images(ecr, name)
        to_delete = images[args.keep:]

        print(f"{GREEN}[{name}]{RESET} Total: {len(images)} | Keep: {min(args.keep, len(images))} | Delete: {len(to_delete)}")
        if to_delete:
            digests = [img["imageDigest"] for img in to_delete]
            deleted = delete_images(ecr, name, digests, args.dry_run)
            total_deleted += deleted
            print(f"  → Deleted {deleted} image(s)")

    print(f"\nTotal images deleted: {total_deleted}")


if __name__ == "__main__":
    main()
