# 🚀 UNESCO Open Science Portal - Kind Deployment Guide

Complete guide for deploying InvenioRDM on **Kind (Kubernetes in Docker)** for local development and testing.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [Data Import](#data-import)
5. [Daily Operations](#daily-operations)
6. [Troubleshooting](#troubleshooting)
7. [Architecture](#architecture)

---

## 🎯 Overview

This deployment uses:

- **Kind**: Local Kubernetes cluster running in Docker
- **Official Helm Chart**: InvenioRDM from `inveniosoftware/helm-invenio` (v0.8.1)
- **External Services**: PostgreSQL, Redis, RabbitMQ, OpenSearch with public images
- **Custom Image**: Your customized InvenioRDM with compiled assets
- **HTTP Mode**: Simplified for local development (no TLS)
- **Pinned Versions**: Helm chart versions are fixed to prevent breaking changes

### Why This Approach?

✅ **Production-ready**: Uses official Helm chart  
✅ **No registry issues**: Public images instead of Bitnami registry  
✅ **Fast iteration**: Rebuild and redeploy quickly  
✅ **Complete control**: Full access to all components  
✅ **Easy cleanup**: Delete and recreate in minutes

---

## 📦 Prerequisites

### Required Tools

Install these tools before starting:

```bash
# macOS
brew install kind kubectl helm docker

# Verify installation
kind version
kubectl version --client
helm version
docker --version
```

### System Requirements

- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 10GB free space
- **Docker**: Running with at least 6GB memory allocated

### Check Everything

From the `k8s` directory:

```bash
cd k8s
make kind-check
```

This verifies all tools are installed and shows their versions.

---

## 📖 Step-by-Step Guide

Following the steps to deploy the app.

### Step 1: Create Kind Cluster

```bash
make kind-create
```

**What it does:**

- Creates Kind cluster named `unesco-rdm`
- Sets up port mappings (80→8080, 443→8443)
- Installs Ingress NGINX controller
- Creates persistent volume directories

**Time:** ~2 minutes

**Verify:**

```bash
kind get clusters
kubectl cluster-info --context kind-unesco-rdm
```

---

### Step 2: Deploy External Services

```bash
make kind-deploy-services
```

**What it does:**

- Creates `unesco-rdm` namespace
- Deploys PostgreSQL (database)
- Deploys Redis (cache)
- Deploys RabbitMQ (message queue)
- Deploys OpenSearch (search engine)
- Waits for all services to be ready

**Time:** ~2-3 minutes

**Verify:**

```bash
kubectl get pods -n unesco-rdm
# All pods should show "Running"
```

---

### Step 3: Build and Load Docker Image

```bash
make kind-load-image
```

**What it does:**

- Builds custom InvenioRDM image from `Dockerfile`
- Compiles webpack assets during build
- Loads image into Kind cluster
- Tags as `sc-openscience:latest`

**Time:** ~5-10 minutes (first build)

**Verify:**

```bash
docker exec -it unesco-rdm-control-plane crictl images | grep sc-openscience
```

---

### Step 4: Deploy InvenioRDM with Helm

```bash
make kind-deploy-helm
```

**What it does:**

- Adds InvenioRDM Helm repository
- Installs chart with custom values (`values.yaml`)
- Deploys web, workers, and beat pods
- Configures to use external services
- Sets HTTP-only mode for local dev

**Time:** ~2-3 minutes

**Verify:**

```bash
kubectl get pods -n unesco-rdm
# Should see: web, worker (2 replicas), worker-beat
```

---

### Step 5: Initialize System

```bash
make kind-init
```

**What it does:**

- Loads InvenioRDM vocabularies (resource types, languages, licenses, etc.)
- Creates database tables
- Sets up search indices
- Creates file storage location
- **Important**: Vocabularies are loaded by workers in background (~2-3 minutes)

**Time:** ~3-5 minutes

**Verify:**

```bash
# Check vocabularies loaded
kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
  invenio shell -c "from invenio_vocabularies.proxies import current_service; print(current_service.read_all(identity=system_identity, type='resourcetypes').total)"
# Should show: 45
```

---

### Step 6: Create Admin User

```bash
make kind-create-admin
```

**What it does:**

- Creates user `admin@unesco.org` with password `admin123`
- Assigns admin role and superuser permissions
- Generates API token
- Saves token to `../openscience-tools/config/.env.kind`

**Time:** ~30 seconds

**Credentials:**

- Email: `admin@unesco.org`
- Password: `admin123`

---

### Step 7: Access Application

```bash
# Start port forwarding (keep this running)
make kind-port-forward
```

**Access URLs:**

- Web UI: http://localhost:8080
- API: http://localhost:8080/api

**Login** with admin credentials above.

---

## 📥 Data Import

### Quick Reset with Lens Data

Delete all records and import 26 publications from Lens.org:

```bash
make kind-reset-lens
```

**Time:** ~2-3 minutes

### Import from Other Sources

```bash
# From CSV
make kind-tools-import-lens FILE='../openscience-tools/src/sources/csv/data/publications.csv'

# From Zenodo (single record)
make kind-tools-import-zenodo RECORD_ID='17462748'

# From Zenodo (search)
make kind-tools-import-zenodo QUERY='climate data' MAX=5
```

---

## 🔧 Daily Operations

### Check Status

```bash
# Overall status
make kind-status

# Just pods
kubectl get pods -n unesco-rdm

# Watch pods (live updates)
kubectl get pods -n unesco-rdm -w
```

### View Logs

```bash
# Web logs (follow mode)
make kind-logs

# Worker logs
kubectl logs -f deployment/unesco-rdm-invenio-worker -n unesco-rdm

# Beat logs
kubectl logs -f deployment/unesco-rdm-invenio-worker-beat -n unesco-rdm

# Specific pod
kubectl logs <pod-name> -n unesco-rdm --all-containers
```

### Restart Application

```bash
# Restart all deployments
make kind-restart

# Restart specific component
kubectl rollout restart deployment/unesco-rdm-invenio-web -n unesco-rdm
kubectl rollout restart deployment/unesco-rdm-invenio-worker -n unesco-rdm
```

### Execute Commands

```bash
# Open shell in web pod
make kind-shell

# Run single command
kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- invenio --help

# Create user
kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
  invenio users create test@example.com --password test123 --active

# List records
kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
  invenio shell -c "from invenio_rdm_records.proxies import current_rdm_records_service; print(current_rdm_records_service.search(system_identity).total)"
```

### Rebuild After Code Changes

```bash
# 1. Make your code changes in parent directory
cd ..
# edit files...

# 2. Rebuild and reload image
cd k8s
make kind-load-image

# 3. Restart pods to use new image
make kind-restart

# 4. Check if running
make kind-status
```

---

### Remove Deployment (Keep Cluster)

```bash
make kind-clean
```

This removes the Helm release and namespace but keeps the Kind cluster. Useful for quick redeployment.

---

### Complete Cleanup

```bash
make kind-down
```

This deletes the entire Kind cluster. All data is lost.

---

## 🏗️ Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Kind Cluster: unesco-rdm                  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          Namespace: unesco-rdm                        │  │
│  │                                                        │  │
│  │  External Services (Public Images):                   │  │
│  │  ┌──────────┐ ┌────────────┐ ┌──────────┐           │  │
│  │  │  Redis   │ │ PostgreSQL │ │ RabbitMQ │           │  │
│  │  │ :7-alpine│ │    :15     │ │:3-mgmt   │           │  │
│  │  └──────────┘ └────────────┘ └──────────┘           │  │
│  │  ┌────────────┐                                      │  │
│  │  │ OpenSearch │                                      │  │
│  │  │   :2.11.1  │                                      │  │
│  │  └────────────┘                                      │  │
│  │                                                        │  │
│  │  InvenioRDM (Official Helm Chart):                   │  │
│  │  ┌───────────────────────────────────────────────┐  │  │
│  │  │  Web Pod (2 containers)                       │  │  │
│  │  │  - nginx (frontend)                           │  │  │
│  │  │  - uwsgi (application)                        │  │  │
│  │  │  Resources: 1Gi-2Gi RAM                       │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  │  ┌───────────────────────────────────────────────┐  │  │
│  │  │  Worker Pods (2 replicas)                     │  │  │
│  │  │  - Celery workers                             │  │  │
│  │  │  - Process background tasks                   │  │  │
│  │  │  Resources: 512Mi-1Gi RAM each                │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  │  ┌───────────────────────────────────────────────┐  │  │
│  │  │  Worker-Beat Pod                              │  │  │
│  │  │  - Celery beat scheduler                      │  │  │
│  │  │  - Periodic tasks                             │  │  │
│  │  │  Resources: 512Mi-1Gi RAM                     │  │  │
│  │  └───────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Port Forward
                          │ 8080:5000
                          ▼
                 http://localhost:8080
```

### Resource Allocation

| Component   | CPU Request  | CPU Limit  | Memory Request | Memory Limit |
| ----------- | ------------ | ---------- | -------------- | ------------ |
| Web         | 500m         | 1000m      | 1Gi            | 2Gi          |
| Worker (×2) | 250m         | 500m       | 512Mi          | 1Gi          |
| Worker-Beat | 200m         | 500m       | 512Mi          | 1Gi          |
| PostgreSQL  | 250m         | 500m       | 512Mi          | 1Gi          |
| Redis       | 100m         | 200m       | 256Mi          | 512Mi        |
| RabbitMQ    | 200m         | 500m       | 512Mi          | 1Gi          |
| OpenSearch  | 500m         | 1000m      | 1Gi            | 2Gi          |
| **Total**   | **~2.5 CPU** | **~5 CPU** | **~4.5Gi**     | **~9.5Gi**   |

**Recommendation:** Allocate at least 8GB RAM to Docker Desktop.

---

## 📝 Configuration Files

### `kind-config.yaml`

- Kind cluster configuration
- Port mappings (80→8080, 443→8443)
- Node settings

### `external-services.yaml`

- Deployments for PostgreSQL, Redis, RabbitMQ, OpenSearch
- Uses public Docker images
- Single replica with emptyDir volumes (not persistent)

### `values.yaml`

- Helm chart overrides
- HTTP-only configuration
- External service connections
- Resource limits
- Probe configurations (disabled/adjusted)

### `Makefile`

- All deployment commands
- Encapsulates kubectl and helm operations
- Provides convenient targets

---

## 🎓 Make Targets Reference

### Setup & Deployment

| Command                     | Description                         |
| --------------------------- | ----------------------------------- |
| `make kind-check`           | Verify all tools installed          |
| `make kind-create`          | Create Kind cluster                 |
| `make kind-deploy-services` | Deploy external services            |
| `make kind-load-image`      | Build and load Docker image         |
| `make kind-deploy-helm`     | Install Helm chart                  |
| `make kind-init`            | Initialize database & vocabularies  |
| `make kind-create-admin`    | Create admin user                   |
| `make kind-full-deploy`     | **Complete deployment** (all above) |

### Operations

| Command                  | Description              |
| ------------------------ | ------------------------ |
| `make kind-status`       | Show cluster status      |
| `make kind-logs`         | Follow web pod logs      |
| `make kind-shell`        | Open shell in web pod    |
| `make kind-port-forward` | Forward port 8080 → 5000 |
| `make kind-restart`      | Restart all deployments  |

### Data Management

| Command                                  | Description                   |
| ---------------------------------------- | ----------------------------- |
| `make kind-reset-lens`                   | Delete all + import Lens data |
| `make kind-scripts-delete-all`           | Delete all records            |
| `make kind-scripts-import-lens FILE=...` | Import from Lens file         |

### Version Management

| Command                   | Description                         |
| ------------------------- | ----------------------------------- |
| `make kind-helm-versions` | Check available Helm chart versions |

### Cleanup

| Command            | Description                       |
| ------------------ | --------------------------------- |
| `make kind-clean`  | Remove deployment (keep cluster)  |
| `make kind-delete` | Delete Kind cluster               |
| `make kind-down`   | Complete cleanup (clean + delete) |

---

## 📚 Additional Resources

- [Version History](VERSIONS.md) - Helm chart versions and upgrade notes
- [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/)
- [Helm Chart Repository](https://github.com/inveniosoftware/helm-invenio)
- [Kind Documentation](https://kind.sigs.k8s.io/)
- [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)

---

## 🆘 Getting Help

1. **Check logs**: `make kind-logs`
2. **Check status**: `make kind-status`
3. **Check InvenioRDM docs**: https://inveniordm.docs.cern.ch/

---

**Happy deploying! 🚀**
