# DevOps Automation Toolkit

[![CI](https://github.com/elishambiro/devops-automation-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/elishambiro/devops-automation-toolkit/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Shell](https://img.shields.io/badge/Shell-Bash-green?logo=gnu-bash)](https://www.gnu.org/software/bash/)
[![Ansible](https://img.shields.io/badge/Ansible-2.15-red?logo=ansible)](https://ansible.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.29-blue?logo=kubernetes)](https://kubernetes.io)
[![AWS](https://img.shields.io/badge/AWS-boto3-orange?logo=amazon-aws)](https://aws.amazon.com)

A collection of **40 production-ready automation scripts and playbooks** for DevOps engineers — covering monitoring, cleanup, AWS, Kubernetes, and Ansible infrastructure automation.

Every script is built around real operational needs: reducing alert noise, cutting AWS costs, enforcing security policies, and automating repetitive maintenance work.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Scripts Overview](#scripts-overview)
  - [Monitoring](#-monitoring-10-scripts)
  - [Cleanup](#-cleanup-10-scripts)
  - [AWS](#-aws-10-scripts)
  - [Kubernetes](#-kubernetes-10-scripts)
  - [Ansible Playbooks](#-ansible-playbooks-10-playbooks)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [CI/CD Pipeline](#cicd-pipeline)
- [Requirements](#requirements)

---

## Architecture Overview

```
devops-automation-toolkit/
├── scripts/
│   ├── monitoring/          # Health checks, SSL, process monitoring, benchmarks
│   ├── cleanup/             # Docker, logs, K8s jobs, ECR, git branches
│   ├── aws/                 # Cost reports, inventory, security audits, backups
│   ├── kubernetes/          # Node status, pod health, ingress, PVC, secrets
│   └── ansible/             # Infrastructure provisioning and configuration
├── requirements.txt         # Python dependencies
└── .github/workflows/       # CI: flake8 + shellcheck + ansible-lint
```

**Design principles:**
- **Zero breaking changes** — every script has a `--dry-run` flag or demo mode where applicable
- **No side effects** — read-only operations unless explicitly triggered with `--force` or `--apply`
- **Colorized output** — ANSI colors for quick visual scanning in CI and terminals
- **Exit codes** — exit 1 on failure so scripts compose with alerting pipelines

---

## Scripts Overview

### 📊 Monitoring (10 scripts)

| Script | Description | Key Features |
|---|---|---|
| `check_services_health.py` | HTTP health check for multiple services | Latency reporting, configurable timeouts, exit 1 on failure |
| `ssl_cert_expiry.py` | SSL certificate expiry checker | Configurable warning threshold, supports multiple domains |
| `k8s_pod_restarts.py` | Detect crashlooping Kubernetes pods | Threshold-based, all namespaces, namespace filter |
| `port_connectivity_check.py` | TCP port reachability tester | Service name mapping, multiple hosts/ports |
| `log_error_counter.py` | Parse log files for ERROR/WARN patterns | Regex support, top-N errors, hourly trend graph |
| `process_monitor.py` | CPU/memory monitor for named processes | Watch mode, alert thresholds, psutil-based |
| `response_time_benchmark.py` | API endpoint load tester | Concurrency, p50/p95/p99 latency stats |
| `db_connection_check.py` | Database connectivity checker | Postgres, MySQL, Redis, MongoDB support |
| `uptime_tracker.py` | Health endpoint uptime logger | Calculates uptime %, outage window detection |
| `alertmanager_silence.py` | Prometheus Alertmanager silences | Create / list / delete silences via REST API |

### 🧹 Cleanup (10 scripts)

| Script | Description | Key Features |
|---|---|---|
| `cleanup_docker.sh` | Remove unused Docker resources | Prune containers/images/volumes/networks, `--dry-run` |
| `rotate_logs.sh` | Compress and delete old logs | Configurable age and retention, gzip compression |
| `disk_usage_alert.py` | Monitor disk usage thresholds | Warning/critical levels, all mount points, progress bar |
| `find_large_files.sh` | Find files above a size threshold | Human-readable sizes, configurable path and limit |
| `cleanup_k8s_jobs.sh` | Delete completed/failed K8s jobs | Targets all namespaces, `--dry-run` |
| `remove_merged_branches.sh` | Delete merged git branches | Protected branch list, local + remote, `--dry-run` |
| `cleanup_ecr_images.py` | Trim old ECR container images | Keep last N images per repo, paginated API |
| `cleanup_docker_cache.sh` | Clean Docker build cache | Before/after disk usage diff, `--all` flag |
| `old_artifacts_cleanup.py` | Delete old build artifacts | `.zip`, `.jar`, `.whl`, `.tar.gz`, configurable age |

### ☁️ AWS (10 scripts)

| Script | Description | Key Features |
|---|---|---|
| `backup_to_s3.sh` | Backup local directory to S3 | Timestamp, retention cleanup, tar.gz |
| `aws_cost_report.py` | Cost breakdown by service | Last N days, Cost Explorer API, demo mode |
| `s3_bucket_sizes.py` | Audit S3 buckets by size | CloudWatch metrics, sort by size/name/count |
| `ec2_inventory.py` | Full EC2 instance inventory | CSV export, state filter, demo mode |
| `security_group_audit.py` | Find open security groups | CRITICAL/HIGH/MEDIUM severity, 0.0.0.0/0 detection |
| `iam_access_key_audit.py` | IAM access key age + last-use | Rotation policy enforcement, demo mode |
| `cloudwatch_log_retention.py` | Set log group retention policies | Targets groups with no expiry, dry-run |
| `rds_snapshot_cleanup.py` | Delete old manual RDS snapshots | Age threshold, demo mode |
| `aws_untagged_resources.py` | Find untagged EC2/RDS resources | Required tags list, demo mode, recommendations |

### ⚙️ Kubernetes (10 scripts)

| Script | Description | Key Features |
|---|---|---|
| `k8s_namespace_summary.py` | Overview of all namespaces | Pod/deployment/service counts per namespace |
| `k8s_scale.sh` | Scale deployments in a namespace | Up/down to N replicas, `--dry-run` |
| `k8s_image_versions.py` | Audit container image versions | Warns on `:latest` tag, all namespaces |
| `k8s_resources_without_limits.py` | Find containers missing CPU/memory limits | Risk of resource starvation |
| `k8s_evicted_pods_cleanup.sh` | Delete evicted/failed pods | Namespace filter, `--dry-run` |
| `k8s_node_status.py` | Node health, roles, capacity | CPU/memory allocatable, taints, NotReady flagging |
| `k8s_rolling_restart.sh` | Trigger rolling restarts | All or label-selected deployments, `--dry-run` |
| `k8s_secret_audit.py` | Audit Kubernetes Secrets | Age, size, type, rotation recommendations |
| `k8s_ingress_list.py` | List all Ingress resources | Hosts, paths, backends, TLS status warnings |
| `k8s_pvc_status.sh` | PersistentVolumeClaim status | Bound/Pending/Lost, storage class, access modes |

### 📦 Ansible Playbooks (10 playbooks)

| Playbook | Description | Key Variables |
|---|---|---|
| `setup_docker.yml` | Install Docker Engine + Compose | `docker_users` |
| `harden_server.yml` | CIS-inspired security hardening | `ssh_port`, `allowed_tcp_ports` |
| `deploy_app.yml` | Deploy a Dockerized application | `app_image`, `app_port`, `app_env_vars` |
| `setup_monitoring.yml` | Deploy Prometheus + Grafana + Node Exporter | `grafana_admin_password`, `prometheus_retention` |
| `setup_nginx.yml` | Install and configure Nginx reverse proxy | `nginx_vhosts` |
| `user_management.yml` | Create/remove users, SSH keys, sudo | `users_to_create`, `users_to_remove` |
| `update_and_patch.yml` | OS package updates with rolling reboot | `full_upgrade`, `patch_serial` |
| `setup_k8s_node.yml` | Prepare a Kubernetes worker node | `k8s_version`, `join_command` |
| `backup_configs.yml` | Back up /etc configs to S3 or local | `s3_bucket`, `config_paths`, `retention_days` |
| `setup_ssl.yml` | Let's Encrypt SSL + Nginx HTTPS config | `domains`, `email` |

---

## Quick Start

```bash
git clone https://github.com/elishambiro/devops-automation-toolkit.git
cd devops-automation-toolkit
pip install -r requirements.txt
```

For Ansible playbooks:
```bash
pip install ansible
ansible-galaxy collection install community.docker community.general ansible.posix
```

---

## Usage Examples

### Monitoring

```bash
# Health check multiple services — exits 1 if any service is down
python scripts/monitoring/check_services_health.py \
  --urls http://api.example.com/health http://app.example.com/health

# SSL certificate expiry check (warn if < 30 days)
python scripts/monitoring/ssl_cert_expiry.py \
  --domains example.com api.example.com --warn-days 30

# Find crashlooping pods (restart count > 5)
python scripts/monitoring/k8s_pod_restarts.py --threshold 5

# Check if critical ports are reachable
python scripts/monitoring/port_connectivity_check.py \
  --hosts db.internal cache.internal --ports 5432 6379

# Benchmark an API endpoint with 20 concurrent users
python scripts/monitoring/response_time_benchmark.py \
  --url https://api.example.com/items --concurrency 20 --requests 200

# Monitor a process and alert if CPU > 80%
python scripts/monitoring/process_monitor.py \
  --process nginx --cpu-threshold 80 --watch --interval 10

# Count errors in application logs (last 1000 lines)
python scripts/monitoring/log_error_counter.py \
  --file /var/log/app/error.log --top 10

# Track uptime of a service for 1 hour
python scripts/monitoring/uptime_tracker.py \
  --url http://my-service/health --duration 3600 --interval 30

# Create an Alertmanager silence for 2 hours
python scripts/monitoring/alertmanager_silence.py \
  --alertmanager http://alertmanager:9093 \
  --matchers alertname=HighMemoryUsage env=staging \
  --duration 2h --comment "Scheduled maintenance"
```

### Cleanup

```bash
# Preview what Docker cleanup would remove (no actual deletion)
bash scripts/cleanup/cleanup_docker.sh --dry-run

# Execute Docker cleanup
bash scripts/cleanup/cleanup_docker.sh --force

# Rotate logs: compress files older than 7 days, delete archives > 30 days
bash scripts/cleanup/rotate_logs.sh \
  --log-dir /var/log/myapp --compress-age 7 --delete-age 30

# Find files larger than 500MB
bash scripts/cleanup/find_large_files.sh --path /var/log --size 500M

# Preview K8s job cleanup
bash scripts/cleanup/cleanup_k8s_jobs.sh --namespace production --dry-run

# Remove ECR images, keep last 10 per repo
python scripts/cleanup/cleanup_ecr_images.py --keep 10 --profile myprofile

# Delete merged git branches (except main/master/develop)
bash scripts/cleanup/remove_merged_branches.sh --remote --dry-run
bash scripts/cleanup/remove_merged_branches.sh --remote --force
```

### AWS

```bash
# AWS cost report for the last 30 days (top 10 services)
python scripts/aws/aws_cost_report.py --days 30 --top 10

# Audit all S3 buckets sorted by size
python scripts/aws/s3_bucket_sizes.py --sort size

# Full EC2 inventory, export to CSV
python scripts/aws/ec2_inventory.py --profile prod --output csv > ec2.csv

# Find security groups with 0.0.0.0/0 (open to internet)
python scripts/aws/security_group_audit.py --profile prod --region us-east-1

# IAM access key age audit (flag keys older than 90 days)
python scripts/aws/iam_access_key_audit.py --max-age 90

# Set 90-day retention on all CloudWatch log groups with no expiry
python scripts/aws/cloudwatch_log_retention.py --retention-days 90 --apply

# Find resources missing required tags
python scripts/aws/aws_untagged_resources.py \
  --required-tags Environment Owner Project --profile prod

# Backup /data/app to S3 with 14-day retention
bash scripts/aws/backup_to_s3.sh \
  --source /data/app --bucket my-backups --prefix daily --retention 14
```

### Kubernetes

```bash
# Namespace overview (pods, deployments, services)
python scripts/kubernetes/k8s_namespace_summary.py

# Scale down all deployments in staging (save costs overnight)
bash scripts/kubernetes/k8s_scale.sh --namespace staging --replicas 0

# Scale back up in the morning
bash scripts/kubernetes/k8s_scale.sh --namespace staging --replicas 2

# Find containers running with :latest tag
python scripts/kubernetes/k8s_image_versions.py

# Find containers without resource limits
python scripts/kubernetes/k8s_resources_without_limits.py --namespace production

# Check node health, roles, and capacity
python scripts/kubernetes/k8s_node_status.py

# Rolling restart all deployments in production (picks up new Secrets/ConfigMaps)
bash scripts/kubernetes/k8s_rolling_restart.sh --namespace production --dry-run
bash scripts/kubernetes/k8s_rolling_restart.sh --namespace production

# Rolling restart only specific app
bash scripts/kubernetes/k8s_rolling_restart.sh \
  --namespace production --selector app=api-gateway

# Audit secrets (flag old or large secrets)
python scripts/kubernetes/k8s_secret_audit.py --namespace production --max-age-days 180

# List all Ingress resources and check TLS coverage
python scripts/kubernetes/k8s_ingress_list.py

# Check PVC status across all namespaces
bash scripts/kubernetes/k8s_pvc_status.sh

# Clean up evicted pods
bash scripts/kubernetes/k8s_evicted_pods_cleanup.sh --all-namespaces
```

### Ansible

```bash
# Install Docker on all servers
ansible-playbook scripts/ansible/setup_docker.yml -i inventory.ini

# Harden server security (SSH, UFW, fail2ban, sysctl)
ansible-playbook scripts/ansible/harden_server.yml -i inventory.ini

# Deploy application version 2.1.0
ansible-playbook scripts/ansible/deploy_app.yml -i inventory.ini \
  -e "app_image=myrepo/myapp:2.1.0 app_port=8080"

# Set up full monitoring stack (Prometheus + Grafana + Node Exporter)
ansible-playbook scripts/ansible/setup_monitoring.yml -i inventory.ini \
  -e "grafana_admin_password=SecurePass123"

# Create users and configure SSH keys
ansible-playbook scripts/ansible/user_management.yml -i inventory.ini

# Apply security patches to 30% of servers at a time
ansible-playbook scripts/ansible/update_and_patch.yml -i inventory.ini

# Full upgrade with automatic reboot
ansible-playbook scripts/ansible/update_and_patch.yml -i inventory.ini \
  -e "full_upgrade=true reboot_enabled=true"

# Prepare a new K8s worker node
ansible-playbook scripts/ansible/setup_k8s_node.yml -i inventory.ini \
  -e "k8s_version=1.29 join_command='kubeadm join 10.0.0.1:6443 --token ...'"

# Back up all server configs to S3
ansible-playbook scripts/ansible/backup_configs.yml -i inventory.ini \
  -e "s3_bucket=my-config-backups"

# Obtain Let's Encrypt SSL and configure Nginx HTTPS
ansible-playbook scripts/ansible/setup_ssl.yml -i inventory.ini \
  -e "domains=['example.com','www.example.com'] email=admin@example.com"
```

---

## CI/CD Pipeline

GitHub Actions runs automatically on every push and pull request:

```
Push / PR
    │
    ├── Lint Python Scripts
    │     ├── flake8 (max 120 chars, PEP8)
    │     └── python -m py_compile (syntax validation)
    │
    ├── ShellCheck Bash Scripts
    │     └── shellcheck on all .sh files
    │
    └── Ansible Lint
          └── ansible-lint on all playbooks
```

Configuration: [.github/workflows/ci.yml](.github/workflows/ci.yml)

---

## Requirements

**Python scripts:**
```
requests>=2.31.0
boto3>=1.34.0
psutil>=5.9.0
```

**Bash scripts:**
- bash 4+
- Standard Unix tools: `awk`, `find`, `tar`, `gzip`
- `kubectl` (for Kubernetes scripts)
- `aws` CLI (for backup_to_s3.sh)

**Ansible playbooks:**
- Ansible 2.15+
- Collections: `community.docker`, `community.general`, `ansible.posix`
- Target OS: Ubuntu 20.04 / 22.04 (Debian-based)

Install everything:
```bash
pip install -r requirements.txt ansible
ansible-galaxy collection install community.docker community.general ansible.posix
```
