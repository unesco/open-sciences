# UNESCO Open Science Portal - Kubernetes Deployment

Kubernetes deployment for **InvenioRDM** (repository) + **Drupal CMS** (headless CMS) on k3d (local), staging, and production environments.

---

## Prerequisites

| Tool                       | Install (macOS)                                               | Purpose                    |
| -------------------------- | ------------------------------------------------------------- | -------------------------- |
| Docker Desktop (or colima) | [docker.com](https://www.docker.com/products/docker-desktop/) | Container runtime          |
| kubectl                    | `brew install kubectl`                                        | Kubernetes CLI             |
| helm                       | `brew install helm`                                           | Kubernetes package manager |
| k3d                        | `brew install k3d`                                            | Lightweight k3s in Docker  |
| envsubst                   | `brew install gettext`                                        | Template rendering         |
| openssl                    | pre-installed on macOS                                        | Secret generation          |

---

## Local Installation (from zero to running)

Everything runs from the `deploy/` directory.

### Step 1 — Install

```bash
cd deploy/
make install ENV=local
```

This single command performs 9 steps in order:

1. **Generate `.env.local`** — copies `.env.example` and replaces all `CHANGE_ME_*` placeholders with random secrets (skipped if `.env.local` already exists)
2. **Create k3d cluster** — `unesco-rdm` with ports 80 and 8443 mapped, plus pre-loads `nginx:1.25-alpine` into the cluster
3. **Check tools** — verifies kubectl, helm, and cluster connectivity
4. **Render `invenio.cfg`** — substitutes env vars into the config template
5. **Build Docker images** — InvenioRDM + Drupal CMS, then loads them into k3d
6. **Deploy infrastructure** — external services (PostgreSQL 16, Redis, RabbitMQ, OpenSearch, MinIO), Kubernetes secrets, MinIO bucket init, Helm chart install
7. **Initialize InvenioRDM** — database, search indices, vocabularies, custom fields, admin user
8. **Deploy & initialize CMS** — Drupal site install, survey data migration, search indexing
9. **Deploy backup CronJob** — automated backup schedule

> **Duration:** ~15–20 minutes on first run (Docker image builds take the bulk of time).

### Step 2 — Verify

```bash
# Check all pods are Running
kubectl get pods -n unesco-rdm

# Test HTTP endpoints
curl -s -o /dev/null -w "%{http_code}" http://localhost       # 200
curl -s -o /dev/null -w "%{http_code}" http://localhost/cms/   # 200
```

### Step 3 — Access

| Service          | URL                                | Credentials                                                    |
| ---------------- | ---------------------------------- | -------------------------------------------------------------- |
| InvenioRDM       | http://localhost                   | see `ADMIN_USER_EMAIL` / `ADMIN_USER_PASSWORD` in `.env.local` |
| Drupal CMS admin | http://localhost/cms/user/login    | see `ADMIN_USER_EMAIL` / `ADMIN_USER_PASSWORD` in `.env.local` |
| Drupal CMS API   | http://localhost/cms/api/countries | —                                                              |

### Step 4 — Load sample data (optional)

```bash
make reset-lens ENV=local
```

Imports Lens.org publications into InvenioRDM.

---

## Day-to-day Operations

```bash
make stop                          # Stop all pods (keeps data)
make up                            # Start all pods
make deploy ENV=local              # Rebuild images + redeploy (CI/CD style)
make destroy                       # Delete everything (DESTRUCTIVE — asks confirmation)
```

---

## Rebuilding After Code Changes

```bash
# InvenioRDM only
make load-image ENV=local
kubectl rollout restart deployment -l app.kubernetes.io/component=web -n unesco-rdm

# CMS only
make load-cms-image ENV=local
kubectl rollout restart deployment cms -n unesco-rdm

# Both (CI/CD workflow)
make deploy ENV=local
```

---

## Backup & Restore

```bash
make backup ENV=local              # Snapshot PostgreSQL (both DBs), OpenSearch, MinIO
make list-backups ENV=local        # List available backups
make restore BACKUP=<ts> ENV=local # Restore from a specific backup
```

---

## Individual Targets Reference

### Setup

| Target                        | Description                                |
| ----------------------------- | ------------------------------------------ |
| `make install ENV=<env>`      | Complete first-time setup (9 steps)        |
| `make generate-env ENV=<env>` | Generate `.env.<env>` with random secrets  |
| `make setup-k3d`              | Create k3d cluster + pre-load images       |
| `make check`                  | Verify kubectl, helm, cluster connectivity |

### Build

| Target                           | Description                            |
| -------------------------------- | -------------------------------------- |
| `make render-config ENV=<env>`   | Generate `invenio.cfg` from template   |
| `make build-image ENV=<env>`     | Build InvenioRDM Docker image          |
| `make load-image ENV=<env>`      | Build + load InvenioRDM image into k3d |
| `make build-cms-image ENV=<env>` | Build CMS Docker image                 |
| `make load-cms-image ENV=<env>`  | Build + load CMS image into k3d        |

### Deploy

| Target                      | Description                                         |
| --------------------------- | --------------------------------------------------- |
| `make deploy ENV=<env>`     | CI/CD: rebuild images + upgrade Helm + restart      |
| `make deploy-services`      | Deploy external services (DB, cache, search, queue) |
| `make deploy-helm`          | Install/upgrade Helm chart                          |
| `make deploy-cms ENV=<env>` | Apply CMS manifests                                 |

### Initialize

| Target                        | Description                                         |
| ----------------------------- | --------------------------------------------------- |
| `make init-app ENV=<env>`     | Reinitialize InvenioRDM (DB, indices, vocabularies) |
| `make create-admin ENV=<env>` | Create InvenioRDM admin user                        |
| `make init-cms ENV=<env>`     | Run Drupal site install + migrations                |

### Data

| Target                         | Description                                  |
| ------------------------------ | -------------------------------------------- |
| `make reset-lens ENV=<env>`    | Delete all records + re-import Lens.org data |
| `make rebuild-index ENV=<env>` | Rebuild OpenSearch indices                   |

### Lifecycle

| Target         | Description                        |
| -------------- | ---------------------------------- |
| `make up`      | Start InvenioRDM + CMS             |
| `make stop`    | Stop InvenioRDM + CMS (keeps data) |
| `make destroy` | Remove everything (DESTRUCTIVE)    |

---

## Environments

| ENV          | Cluster            | Usage       |
| ------------ | ------------------ | ----------- |
| `local`      | k3d on macOS/Linux | Development |
| `dev`        | Remote k3s         | Staging     |
| `production` | Remote k3s         | Production  |

---

## Troubleshooting

| Symptom                                  | Cause                                     | Fix                                                           |
| ---------------------------------------- | ----------------------------------------- | ------------------------------------------------------------- |
| `make install` fails at env-check        | `.env.local` has `CHANGE_ME` placeholders | `rm .env.local && make generate-env ENV=local`                |
| Pods stuck in `ImagePullBackOff`         | Image not in k3d registry                 | `make load-image ENV=local` / `make load-cms-image ENV=local` |
| `ERR_CONNECTION_REFUSED` on `/cms/api/*` | Browser cached old JS bundle              | Hard refresh: `Cmd+Shift+R`                                   |
| Drupal shows "No front page content"     | Normal — headless CMS, no display nodes   | Use REST API: `/cms/api/countries`                            |
| PostgreSQL fails for CMS                 | Drupal 11 requires PostgreSQL 16+         | Verify `external-services.yaml` uses `postgres:16`            |

---

## Help

```bash
make help
```
