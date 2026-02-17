# UNESCO Open Science Portal - Kubernetes Deployment

Deploy InvenioRDM on Kubernetes (k3s for production, k3d for local testing)
using a shared, environment-aware configuration.

## �� Quick Summary

**First-time complete setup:**

```bash
make install ENV=local
```

This single command performs the entire setup:

1. Checks required tools (docker, kubectl, helm, k3d, etc.)
2. Creates `.env.local` with auto-generated secrets
3. Sets up k3d cluster
4. Builds and loads Docker image
5. Deploys external services + InvenioRDM (Helm)
6. Initializes database, search indices, vocabularies
7. Creates admin user

**CI/CD deployment (code updates):**

```bash
make deploy ENV=local
```

This rebuilds the image, upgrades the Helm release, and restarts pods.

**Optional: Import test data**

```bash
make reset-lens ENV=local
```

**Why this workflow?** The Docker image contains your customized InvenioRDM code.
The first-time setup includes building the image because Helm cannot deploy pods
without it existing in the cluster.

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
├── .env.example        # Template with all variables (committed)
├── .env.local          # k3d testing (gitignored, has secrets)
├── .env.staging        # Staging server (gitignored, has secrets)
├── .env.production     # Production server (gitignored, has secrets)
├── values.yaml         # Helm values template (uses ${VAR} substitution)
├── external-services.yaml
├── Makefile
└── README.md
```

| File           | Committed | Contains secrets  | Purpose                           |
| -------------- | --------- | ----------------- | --------------------------------- |
| `.env.example` | Yes       | No (placeholders) | Template for all environments     |
| `.env.<ENV>`   | No        | Yes               | Complete config including secrets |
| `values.yaml`  | Yes       | No                | Helm chart template (envsubst'd)  |

The Makefile loads the environment file and exports all variables:

```makefile
ENV ?= local
-include .env.$(ENV)
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

**One-command setup + three steps to deploy:**

```bash
cd deploy/

# 1. Complete setup (check tools, create .env.local, setup k3d cluster)
make install ENV=local

# 2. Build and load Docker image
make load-image ENV=local

# 3. Deploy InvenioRDM
make deploy ENV=local

# 4. Import test data (optional)
make reset-lens ENV=local

# 5. Access the application
open http://localhost
```

**What `make install` does:**

- Verifies required tools (docker, k3d, kubectl, helm, envsubst, openssl)
- Creates `.env.local` from `.env.example` with auto-generated secrets
- Creates k3d cluster with port mappings (80:80, 8443:443)

**Admin credentials**: `admin@invenio.org` / `admin123` (configured in `.env.local`)

## Quick Start — Production (k3s)

````bash
cd deploy/

# 1. Install k3s on your server
curl -sfL https://get.k3s.io | sh -

# 2. Setup environment (checks tools, creates .env.production)
make install ENV=production

# 3. Edit .env.production for your domain and settings
vim .env.production

**Note**: For production deployments, you'll need to manually configure TLS certificates
and backup schedules using kubectl/helm directly, as these targets are removed from
the simplified Makefile focused on local k3d development.

## Deployment Steps Explained

### First-Time Setup (Complete, Automated)

```bash
make install ENV=local
```

This **single command** performs the entire first-time setup in 6 steps:

1. **[1/6] Check tools**: Verifies docker, k3d, kubectl, helm, envsubst, openssl
2. **[2/6] Create .env.local**: Copies from .env.example with auto-generated secrets
3. **[3/6] Setup k3d cluster**: Creates cluster with port mappings (ENV=local only)
4. **[4/6] Build + load image**: Renders invenio.cfg → builds Docker image → loads into k3d
5. **[5/6] Deploy Helm**: External services (PostgreSQL, Redis, RabbitMQ, OpenSearch) + InvenioRDM
6. **[6/6] Initialize**: Database schema, search indices, vocabularies, CMS fixtures, admin user

**Result**: Fully operational InvenioRDM at http://localhost

### CI/CD Deployment (Code Updates)

```bash
make deploy ENV=local
```

For updating code after the initial setup, this command:

1. **[1/3] Rebuild image**: Renders invenio.cfg → builds new Docker image → loads into k3d
2. **[2/3] Upgrade Helm**: Updates release with new image and configuration
3. **[3/3] Restart pods**: Rolling restart to pick up changes

**Use this for**: Code changes, configuration updates, image rebuilds

### Manual Operations

```bash
# Reinitialize database + search (when needed)
make init-app ENV=local

# Create admin user (standalone)
make create-admin ENV=local

# Import test data (Lens.org publications)
make reset-lens ENV=local
```

## Makefile Targets Reference

### Primary Workflow

| Target      | Description                                                                     |
| ----------- | ------------------------------------------------------------------------------- |
| `install`   | **First-time complete setup**: tools → config → k3d → build → deploy → init    |
| `deploy`    | **CI/CD update**: Rebuild image, upgrade Helm release, restart pods             |
| `reset-lens`| Import Lens.org test data (57 records)                                          |

### Manual Initialization

| Target        | Description                                 |
| ------------- | ------------------------------------------- |
| `init-app`    | Reinitialize database + search (manual)     |
| `create-admin`| Create admin user (standalone)              |

### Build & Configuration

| Target          | Description                        |
| --------------- | ---------------------------------- |
| `render-config` | Render `invenio.cfg` from template |
| `build-image`   | Render config + build Docker image |
| `load-image`    | Build + load into k3d cluster      |

### Operations

| Target       | Description                              |
| ------------ | ---------------------------------------- |
| `status`     | Show cluster & pod health                |
| `logs`       | Tail web pod logs                        |
| `shell`      | Open bash shell in web pod               |
| `restart`    | Rolling restart (keeps data)             |
| `destroy`    | Remove everything (DESTRUCTIVE)          |
| `reset-lens` | Delete records + re-import Lens.org data |

All targets accept `ENV=local|staging|production` (default: `local`).

## Common Operations

### Check System Status

```bash
make status ENV=local          # Shows pods, services, ingress, PVCs
```

### View Logs

```bash
make logs ENV=local            # Web pod logs
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
make upgrade ENV=local         # Rebuild image → helm upgrade → restart
```

### Import Data

```bash
make reset-lens ENV=local      # Delete all + import Lens.org data
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
curl http://localhost/data/search?field=author

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
````
