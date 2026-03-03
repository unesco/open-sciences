# UNESCO Open Science Portal - Kubernetes Deployment

Kubernetes deployment for InvenioRDM on k3d (local), staging, and production environments.

## Quick Start

```bash
# Complete first-time setup (macOS/Linux)
make install ENV=local

# Load sample data (Lens.org publications)
make reset-lens ENV=local

# Access the portal
open http://localhost
```

**Default credentials:** See `.env.local` for `ADMIN_USER_EMAIL` and `ADMIN_USER_PASSWORD`.

---

## Main Targets

### Setup & Deployment

- `make install ENV=<env>` — Complete setup: tools → k3d → build → deploy → init
- `make deploy ENV=<env>` — CI/CD deployment: rebuild image + upgrade Helm + restart pods
- `make init-app ENV=<env>` — Reinitialize database, search indices, and vocabularies
- `make create-admin ENV=<env>` — Create admin user

### Operations

- `make up` — Start InvenioRDM (scale up)
- `make stop` — Stop InvenioRDM (keeps data)

### Data Management

- `make reset-lens ENV=<env>` — Delete all records + import Lens.org data
- `make rebuild-index ENV=<env>` — Rebuild OpenSearch indices (fix sync issues)

### Backup & Restore

- `make backup ENV=<env>` — Create backup of all data
- `make restore BACKUP=<timestamp> ENV=<env>` — Restore from backup
- `make list-backups ENV=<env>` — List available backups
- `make deploy-backup-cronjob ENV=<env>` — Deploy automated backup CronJob

### Build

- `make render-config ENV=<env>` — Generate invenio.cfg from template + .env file
- `make build-image ENV=<env>` — Render config + build Docker image
- `make load-image ENV=<env>` — Build + load image into k3d cluster

### Cleanup

- `make destroy` — Remove everything (DESTRUCTIVE)

---

## Environments

Set `ENV` to switch between environments:

- `local` — k3d cluster on macOS/Linux (default)
- `dev` — Staging server
- `production` — Production server

---

## Requirements

**Local (k3d):**

- Docker Desktop or colima
- kubectl, helm, k3d
- envsubst (from gettext)

**Staging/Production (k3s):**

- kubectl, helm
- Access to k3s cluster (KUBECONFIG)

---

## Help

```bash
make help
```
