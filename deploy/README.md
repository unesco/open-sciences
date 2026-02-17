# UNESCO Open Science Portal - Kubernetes Deployment

Deploy InvenioRDM on Kubernetes (k3s for production, k3d for local testing)
using a shared, environment-aware configuration.

## 🚀 Quick Summary

**Critical ordering for first-time deployment:**

1. Generate secrets → `make generate-secrets`
2. Create k3d cluster → `k3d cluster create ...`
3. **Build Docker image FIRST** → `make load-image ENV=local`
4. Deploy InvenioRDM → `make deploy ENV=local`
5. Import test data → `make reset-lens ENV=local`

**Why build first?** The Docker image contains your customized InvenioRDM code.
Helm cannot deploy pods without the image existing in the cluster.

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

**IMPORTANT**: Build the Docker image **BEFORE** deploying InvenioRDM.

```bash
cd deploy/

# 1. Generate secrets
make generate-secrets

# 2. Create k3d cluster
k3d cluster create unesco-rdm \
  --port "8080:80@loadbalancer" \
  --port "8443:443@loadbalancer" \
  --agents 0

# 3. Build and load Docker image (MUST be done before deploy)
make load-image ENV=local

# 4. Deploy InvenioRDM
make deploy ENV=local

# 5. Import test data (optional)
make reset-lens ENV=local

# 6. Access the application
open http://localhost:8080
```

**Admin credentials**: `admin@invenio.org` / `admin123` (configured in `.env.local`)

**Note**: Step 3 (build image) is **critical** — `make deploy` alone will fail if the image doesn't exist in k3d.

## Quick Start — Production (k3s)

```bash
cd deploy/

# 1. Generate secrets
make generate-secrets

# 2. Install k3s
make install-k3s

# 3. Verify production domain
cat .env.production

# 4. Build Docker image
make build-image ENV=production
make push-image ENV=production    # Push to registry

# 5. Deploy InvenioRDM
make deploy ENV=production

# 6. Set up HTTPS
make tls-setup ENV=production

# 7. Set up automated backups
make backup-schedule ENV=production
```

## Deployment Steps Explained

The deployment follows this **chronological order**:

### 1. **Preparation**

```bash
make generate-secrets          # Generate random passwords/keys → .env.secrets
```

### 2. **Build Docker Image** (CRITICAL STEP)

```bash
make load-image ENV=local      # For k3d: build + load into cluster
# OR
make push-image ENV=production # For k3s: build + push to registry
```

**Why first?** The Docker image contains your customized InvenioRDM code and configuration.
Helm needs this image to exist before it can deploy pods.

### 3. **Deploy Infrastructure**

```bash
make deploy ENV=local          # Runs all sub-steps automatically:
```

- `deploy-services` — PostgreSQL, Redis, RabbitMQ, OpenSearch
- `deploy-secrets` — K8s secrets from `.env.*` files
- `deploy-helm` — InvenioRDM Helm chart (uses the pre-built image)
- `init` — Database schema, search indices, vocabularies, CMS fixtures
- `create-admin` — Admin user account

### 4. **Import Data** (Optional)

```bash
make reset-lens ENV=local      # Delete all records + import Lens.org test data
```

## Makefile Targets Reference

### Core Workflow (In Order)

| Step | Target             | Description                                   |
| ---- | ------------------ | --------------------------------------------- |
| 1    | `generate-secrets` | Create `.env.secrets` with random credentials |
| 2    | `load-image`       | **Build Docker image + load into k3d**        |
| 3    | `deploy`           | Deploy all services + InvenioRDM + init       |
| 4    | `reset-lens`       | Import Lens.org test data (57 records)        |

### Build & Update

| Target          | Description                              |
| --------------- | ---------------------------------------- |
| `render-config` | Render `invenio.cfg` from template       |
| `build-image`   | Render config + build Docker image       |
| `load-image`    | Build + load into k3d cluster            |
| `push-image`    | Build + push to registry (production)    |
| `upgrade`       | Backup DB + rebuild image + helm upgrade |

### Operations

| Target        | Description                              |
| ------------- | ---------------------------------------- |
| `status`      | Show cluster & pod health                |
| `logs`        | Tail web pod logs                        |
| `logs-worker` | Tail worker pod logs                     |
| `shell`       | Open bash shell in web pod               |
| `restart`     | Rolling restart (keeps data)             |
| `destroy`     | Remove everything (DESTRUCTIVE)          |
| `reset-lens`  | Delete records + re-import Lens.org data |
| `import-lens` | Import Lens.org data (FILE=... OPTS=...) |

All targets accept `ENV=local|staging|production` (default: `local`).

## Common Operations

### Check System Status

```bash
make status ENV=local          # Shows pods, services, ingress, PVCs
```

### View Logs

```bash
make logs ENV=local            # Web pod logs
make logs-worker ENV=local     # Worker pod logs
```

### Shell Access

```bash
make shell ENV=local           # Bash in web pod
```

### Restart After Code Changes

```bash
make load-image ENV=local      # Rebuild and load new image
make restart ENV=local         # Rolling restart (no downtime)
```

### Upgrade InvenioRDM

```bash
make upgrade ENV=production    # Backup DB → rebuild image → helm upgrade → restart
```

### Import/Export Data

```bash
make reset-lens ENV=local                           # Delete all + import Lens.org data
make import-lens FILE=data.json OPTS="--limit 10"   # Import specific file
make backup ENV=production                          # Manual DB backup
make restore FILE=/path/to/backup.dump              # Restore from backup
```

## Troubleshooting

### Pods Not Starting

**Symptom**: `make status` shows pods in `CrashLoopBackOff` or `Pending`

**Solution**:

```bash
make logs                              # Check error messages
kubectl describe pod <pod-name> -n unesco-rdm
```

Common causes:

- **Database not ready**: Wait 30s, then `make restart`
- **Wrong image**: Verify with `docker images sc-openscience`
- **Missing secrets**: Re-run `make deploy-secrets ENV=local`

### Image Not Found in k3d

**Symptom**: `ImagePullBackOff` or `ErrImagePull`

**Solution**:

```bash
make load-image ENV=local      # Build and load image into k3d
make restart ENV=local         # Restart pods
```

### OpenSearch Out of Memory

**Symptom**: OpenSearch pod keeps restarting

**Solution**:

```bash
# macOS/Linux
sudo sysctl -w vm.max_map_count=262144

# Verify
sysctl vm.max_map_count
```

### Facets Not Showing Data

**Symptom**: Custom facets show "No options available"

**Solution**:

```bash
# Reindex records for facet aggregations
kubectl exec -n unesco-rdm <web-pod> -c web -- \
  bash -c "echo y | invenio index reindex --pid-type recid && invenio index run"
```

### Start Fresh

**Symptom**: Everything is broken

**Solution**:

```bash
make destroy ENV=local         # Remove everything
make load-image ENV=local      # Rebuild image
make deploy ENV=local          # Redeploy
```

## Development Workflow

### When to Rebuild the Docker Image

You **MUST rebuild** the image when you change:

- Python code in `site/my_site/`
- `invenio.cfg.template`
- `Pipfile` or `Pipfile.lock` (dependencies)
- Templates in `templates/`
- Static assets in `assets/` or `static/`

### Typical Development Cycle

```bash
# 1. Make code changes in site/my_site/
vim ../site/my_site/filters/base.py

# 2. Rebuild and load image
cd deploy/
make load-image ENV=local

# 3. Restart to pick up new image
make restart ENV=local

# 4. Test changes
curl http://localhost:8080/data/search?field=author

# 5. View logs if needed
make logs ENV=local
```

### Full Redeploy (When Things Break)

```bash
cd deploy/
make destroy ENV=local         # 1. Clean slate
make load-image ENV=local      # 2. Fresh image
make deploy ENV=local          # 3. Redeploy
make reset-lens ENV=local      # 4. Import test data
```

## Configuration Management

### Adding Environment Variables

1. Add to `.env.local`, `.env.staging`, `.env.production`
2. Choose where to use it:
   - **In pods**: Add to `values.yaml` as `${VAR_NAME}`
   - **In application**: Add to `invenio.cfg.template` as `${VAR_NAME}`
3. Rebuild if you modified `invenio.cfg.template`:
   ```bash
   make load-image ENV=local
   ```
4. Redeploy if you modified `values.yaml`:
   ```bash
   make deploy-helm ENV=local
   ```

No Makefile changes needed — all variables are auto-exported.
