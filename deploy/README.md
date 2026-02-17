# UNESCO Open Science Portal - Kubernetes Deployment

Deploy InvenioRDM on Kubernetes (k3s for production, k3d for local testing)
using a shared, environment-aware configuration.

## Architecture

```
                    ┌─────────────────────────────────────────────────────────────┐
  Internet          │  VM / k3d node                                              │
     │              │                                                             │
     │  :443        │  ┌──────────┐    ┌──────────────┐    ┌───────────────────┐  │
     └──────────────┤► │ Traefik  │───►│  Web (×N)    │───►│  PostgreSQL 15    │  │
                    │  │ (ingress)│    │  uWSGI       │    │  PVC: 20Gi        │  │
                    │  └──────────┘    └──────┬───────┘    └───────────────────┘  │
                    │       │                 │                                    │
                    │       │          ┌──────┴───────┐    ┌───────────────────┐  │
                    │  cert-manager    │  Worker (×N)  │───►│  Redis 7          │  │
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

## Environment-Based Configuration

All configuration is driven by the `ENV` variable (`local`, `staging`, `production`).

```
deploy/
├── .env.local          # k3d desktop testing   (committed, NO secrets)
├── .env.staging        # Staging server         (committed, NO secrets)
├── .env.production     # Production server      (committed, NO secrets)
├── .env.secrets        # GENERATED credentials  (gitignored, mode 600)
├── values.yaml         # Helm values template   (uses ${VAR} substitution)
├── external-services.yaml
├── Makefile
└── README.md
```

| File           | Committed | Contains secrets | Purpose                              |
| -------------- | --------- | ---------------- | ------------------------------------ |
| `.env.<ENV>`   | Yes       | No               | Domain, protocol, replicas, tunables |
| `.env.secrets` | No        | Yes              | Passwords, keys, salts               |
| `values.yaml`  | Yes       | No               | Helm chart template (envsubst'd)     |

The Makefile loads both files and exports all variables:

```makefile
ENV ?= local
-include .env.$(ENV)
-include .env.secrets
export
```

Two rendering steps use `envsubst`:

1. **`invenio.cfg.template` → `invenio.cfg`** — baked into the Docker image
2. **`values.yaml` → rendered values** — passed to Helm at deploy time

## Prerequisites

### Local (k3d on macOS/Linux)

| Requirement | Notes                    |
| ----------- | ------------------------ |
| Docker      | Docker Desktop or colima |
| k3d         | `brew install k3d`       |
| kubectl     | `brew install kubectl`   |
| helm        | `brew install helm`      |

### Production (k3s on VM)

| Requirement | Minimum       | Recommended |
| ----------- | ------------- | ----------- |
| CPU         | 4 cores       | 8 cores     |
| RAM         | 8 GB          | 16 GB       |
| Disk        | 50 GB         | 100 GB      |
| OS          | Ubuntu 22.04+ |             |
| Network     | Ports 80/443  |             |

## Quick Start — Local (k3d)

```bash
cd deploy/

# 1. Generate secrets
make generate-secrets          # creates .env.secrets

# 2. Create k3d cluster
k3d cluster create unesco-rdm \
  --port "8080:80@loadbalancer" \
  --port "8443:443@loadbalancer" \
  --agents 0

# 3. Deploy everything
make deploy ENV=local

# 4. Open browser
open http://localhost:8080
```

Admin login: `admin@invenio.org` / `admin123` (set in `.env.local`).

## Quick Start — Production (k3s)

```bash
cd deploy/

# 1. Generate secrets
make generate-secrets

# 2. Install k3s
make install-k3s

# 3. Edit production domain (already committed, just verify)
cat .env.production

# 4. Deploy
make deploy ENV=production

# 5. Set up HTTPS
make tls-setup

# 6. Set up automated backups
make backup-schedule
```

## Makefile Targets

### Setup & Deploy

| Target             | Description                                    |
| ------------------ | ---------------------------------------------- |
| `generate-secrets` | Create `.env.secrets` with random credentials  |
| `render-config`    | Render `invenio.cfg` from template             |
| `deploy`           | Full first-time deployment (all steps)         |
| `deploy-services`  | Deploy PostgreSQL, Redis, RabbitMQ, OpenSearch |
| `deploy-secrets`   | Create K8s secrets from env config             |
| `deploy-helm`      | Install/upgrade Helm chart                     |
| `init`             | Initialize DB, indices, vocabularies           |
| `create-admin`     | Create admin user                              |

### Build & Update

| Target        | Description                        |
| ------------- | ---------------------------------- |
| `build-image` | Render config + build Docker image |
| `load-image`  | Build + load into k3d cluster      |
| `push-image`  | Build + push to registry           |
| `upgrade`     | Backup + rebuild + helm upgrade    |

### Operations

| Target        | Description                     |
| ------------- | ------------------------------- |
| `status`      | Cluster & pod health            |
| `logs`        | Tail web pod logs               |
| `logs-worker` | Tail worker logs                |
| `shell`       | Bash shell in web pod           |
| `restart`     | Rolling restart (InvenioRDM)    |
| `destroy`     | Remove everything (DESTRUCTIVE) |

All targets accept `ENV=local|staging|production` (default: `local`).

## Operations

### Upgrading InvenioRDM

```bash
make upgrade ENV=production
```

This backs up the database, rebuilds the Docker image (including re-rendering
`invenio.cfg`), re-deploys the Helm chart, and restarts pods.

### Manual Backup & Restore

```bash
make backup
make backup-list
make restore FILE=/opt/backups/unesco-rdm/db/dump.dump
```

### Rebuilding Search Indices

```bash
make rebuild-index
```

### Importing Data

```bash
make import-lens FILE=path/to/publications.json
make import-lens FILE=path/to/publications.json OPTS="--limit 100"
```

## Adding a New Environment Variable

1. Add the variable to each `.env.<ENV>` file
2. Reference it in `values.yaml` as `${VAR_NAME}` (for Helm/K8s env)
3. Or reference it in `invenio.cfg.template` as `${VAR_NAME}` (baked into image)
4. No Makefile changes needed — all vars are auto-exported

## Troubleshooting

### Pods stuck in CrashLoopBackOff

```bash
make status
make logs
kubectl describe pod <name> -n unesco-rdm
```

Common causes:

- **Database not ready** — wait, then `make restart`
- **Wrong credentials** — re-run `make deploy-secrets`
- **OpenSearch OOM** — ensure VM has >= 8GB RAM

### OpenSearch won't start

```bash
sysctl vm.max_map_count   # should be 262144
sudo sysctl -w vm.max_map_count=262144
```

### TLS certificate not issued

```bash
make tls-status
kubectl describe certificate -n unesco-rdm
```

### Reset everything

```bash
make destroy
make deploy ENV=local
```
