# UNESCO Open Science Portal - k3s Production Deployment

Production deployment of InvenioRDM on a single VM using [k3s](https://k3s.io/) (lightweight Kubernetes).

## Architecture

```
                    ┌─────────────────────────────────────────────────────────────┐
  Internet          │  VM (k3s node)                                              │
     │              │                                                             │
     │  :443        │  ┌──────────┐    ┌──────────────┐    ┌───────────────────┐  │
     └──────────────┤► │ Traefik  │───►│  Web (×2)    │───►│  PostgreSQL 15    │  │
                    │  │ (ingress)│    │  uWSGI       │    │  PVC: 20Gi        │  │
                    │  └──────────┘    └──────┬───────┘    └───────────────────┘  │
                    │       │                 │                                    │
                    │       │          ┌──────┴───────┐    ┌───────────────────┐  │
                    │  cert-manager    │  Worker (×2)  │───►│  Redis 7          │  │
                    │  (Let's Encrypt) │  Celery       │    │  PVC: 1Gi         │  │
                    │                  └──────┬───────┘    └───────────────────┘  │
                    │                         │                                    │
                    │                  ┌──────┴───────┐    ┌───────────────────┐  │
                    │                  │  Worker-Beat  │───►│  RabbitMQ 3       │  │
                    │                  │  Celery Beat  │    │  PVC: 2Gi         │  │
                    │                  └──────────────┘    └───────────────────┘  │
                    │                                                             │
                    │                                      ┌───────────────────┐  │
                    │                                      │  OpenSearch 2.17  │  │
                    │                                      │  PVC: 20Gi        │  │
                    │                                      └───────────────────┘  │
                    └─────────────────────────────────────────────────────────────┘
```

## Prerequisites

| Requirement | Minimum         | Recommended      |
|-------------|-----------------|------------------|
| CPU         | 4 cores         | 8 cores          |
| RAM         | 8 GB            | 16 GB            |
| Disk        | 50 GB           | 100 GB           |
| OS          | Ubuntu 22.04+, AlmaLinux 9+, RHEL 9+ |  |
| Network     | Public IP, ports 80/443 open          |  |
| DNS         | A record pointing to the VM IP        |  |

## Quick Start

```bash
# 1. Clone and enter deploy directory
git clone <repo-url>
cd sc-openscience/deploy

# 2. Configure
cp .env.example .env
make generate-secrets   # prints secrets to paste into .env
nano .env               # set DOMAIN, paste secrets, SMTP, etc.

# 3. Install k3s
make install-k3s

# 4. Deploy everything
make deploy

# 5. Set up HTTPS
make tls-setup

# 6. Set up automated backups
make backup-schedule
```

Your portal is now live at `https://your-domain.org`.

## Step-by-Step Guide

### 1. Prepare the Server

SSH into your VM and ensure it has a public IP with ports 80 and 443 open.

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo ufw allow 80/tcp && sudo ufw allow 443/tcp

# AlmaLinux/RHEL
sudo dnf update -y
sudo firewall-cmd --permanent --add-service=http --add-service=https
sudo firewall-cmd --reload
```

### 2. Configure Environment

```bash
cd deploy/
cp .env.example .env
chmod 600 .env
```

Edit `.env` and set at minimum:

| Variable                | Description                    | How to generate               |
|-------------------------|--------------------------------|-------------------------------|
| `DOMAIN`                | Your domain name               | e.g. `open-science.unesco.org`|
| `LETSENCRYPT_EMAIL`     | Email for cert notifications   | e.g. `admin@unesco.org`       |
| `SECRET_KEY`            | Flask secret key               | `openssl rand -hex 32`        |
| `SECURITY_LOGIN_SALT`   | Login salt                     | `openssl rand -hex 32`        |
| `POSTGRES_PASSWORD`     | Database password              | `openssl rand -hex 16`        |
| `RABBITMQ_PASSWORD`     | Message queue password         | `openssl rand -hex 16`        |
| `ADMIN_USER_EMAIL`      | Admin login email              | e.g. `admin@unesco.org`       |
| `ADMIN_USER_PASSWORD`   | Admin login password           | Strong password               |

Use `make generate-secrets` to auto-generate cryptographic values.

### 3. Install k3s

```bash
make install-k3s
```

This installs k3s with Traefik ingress controller, Helm, and configures kernel parameters for OpenSearch.

Verify:
```bash
kubectl get nodes
# NAME     STATUS   ROLES                  AGE   VERSION
# myvm     Ready    control-plane,master   1m    v1.28+k3s1
```

### 4. Deploy

```bash
make deploy
```

This runs all deployment steps in order:
1. **deploy-services** - PostgreSQL, Redis, RabbitMQ, OpenSearch (with PVCs)
2. **deploy-secrets** - Creates K8s secrets from `.env` values
3. **deploy-helm** - Installs InvenioRDM via Helm chart
4. **init** - Database, search indices, vocabularies, file storage
5. **create-admin** - Creates admin user

### 5. Set Up HTTPS

```bash
make tls-setup
```

This installs cert-manager and configures Let's Encrypt. Certificates are automatically renewed.

```bash
# Verify certificate
make tls-status
```

### 6. Set Up Automated Backups

```bash
make backup-schedule
```

This creates a K8s CronJob that runs `pg_dump` daily at 2:00 AM UTC, stores backups in `/opt/backups/unesco-rdm/db/`, and retains the last 30 days.

## Operations

### Common Commands

```bash
make status          # Pod status, services, PVCs, resource usage
make logs            # Tail web pod logs
make logs-worker     # Tail worker logs
make shell           # Bash shell in web pod
make db-shell        # psql shell in PostgreSQL
make restart         # Rolling restart (InvenioRDM only)
make restart-all     # Restart everything (including DB)
```

### Upgrading InvenioRDM

After pushing a new Docker image:

```bash
make upgrade
```

This backs up the database, re-deploys the Helm chart, and restarts pods.

For Helm-only changes (e.g. config updates):
```bash
make deploy-helm
make restart
```

### Rebuilding Search Indices

If search results are stale or after a restore:

```bash
make rebuild-index
```

### Manual Backup & Restore

```bash
# Manual backup
make backup

# List available backups
make backup-list

# Restore (stops services, restores DB, rebuilds indices)
make restore FILE=/opt/backups/unesco-rdm/db/db_20260216_020000.dump
```

### Importing Data

```bash
# Import Lens.org publications
make import-lens FILE=path/to/publications.json

# With options
make import-lens FILE=path/to/publications.json OPTS="--limit 100"
```

### Scaling

Edit `.env` to change replica counts, then re-deploy:

```bash
# In .env:
# WEB_REPLICAS=3
# WORKER_REPLICAS=3

make deploy-helm
```

## Differences from `k8s/` (Kind)

| Feature            | `k8s/` (Kind)              | `deploy/` (k3s)              |
|--------------------|----------------------------|-------------------------------|
| Purpose            | Local development          | Production deployment         |
| Kubernetes         | Kind (Docker-in-Docker)    | k3s (single binary)          |
| Storage            | emptyDir (lost on restart) | PVCs (persistent)            |
| TLS                | None                       | Let's Encrypt (automated)    |
| Ingress            | NGINX (manual install)     | Traefik (built-in)           |
| Access             | `localhost:8080` via port-forward | Public domain via Ingress |
| Backups            | None                       | Automated daily + manual     |
| Secrets            | Hardcoded                  | K8s Secrets from `.env`      |
| Health checks      | None                       | Startup, readiness, liveness |

## File Reference

```
deploy/
├── .env.example           # Environment variable template
├── values.yaml            # Helm values (production)
├── values-staging.yaml    # Helm values (staging overrides)
├── external-services.yaml # PostgreSQL, Redis, RabbitMQ, OpenSearch
├── backup-cronjob.yaml    # Automated daily backup CronJob
├── Makefile               # All deployment automation targets
├── README.md              # This file
└── scripts/
    ├── install-k3s.sh     # k3s + Helm installation
    ├── setup-tls.sh       # cert-manager + Let's Encrypt
    ├── backup.sh          # Manual backup script
    └── restore.sh         # Database restore script
```

## Troubleshooting

### Pods stuck in CrashLoopBackOff

```bash
make status                    # See which pods are failing
make logs                      # Check web logs
kubectl describe pod <name> -n unesco-rdm   # Detailed events
```

Common causes:
- **Database not ready**: Wait for PostgreSQL pod, then `make restart`
- **Wrong credentials**: Check `make env-check`, re-run `make deploy-secrets`
- **OpenSearch heap**: Ensure VM has enough RAM (OpenSearch needs ~2GB)

### OpenSearch won't start

```bash
# Check if sysctl is set
sysctl vm.max_map_count
# Should be 262144. If not:
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.d/99-opensearch.conf
```

### TLS certificate not issued

```bash
make tls-status
kubectl describe certificate -n unesco-rdm
kubectl logs -n cert-manager deploy/cert-manager
```

Common causes:
- DNS A record not pointing to VM IP
- Port 80 blocked (needed for HTTP-01 challenge)
- Let's Encrypt rate limits (use `--staging` flag first)

### Disk space issues

```bash
df -h
kubectl get pvc -n unesco-rdm
# Clean old backups
ls -la /opt/backups/unesco-rdm/db/
```

### Reset everything

```bash
make destroy      # Removes all K8s resources (preserves backups)
make deploy       # Fresh deployment
```

## Security Notes

- `.env` file contains secrets — never commit to Git (already in `.gitignore`)
- All inter-service communication is within the K8s cluster network
- Only Traefik exposes ports 80/443 externally
- Database credentials are stored as K8s Secrets (base64-encoded, not encrypted at rest by default)
- For enhanced security, consider enabling K8s Secret encryption at rest
