# 🚀 UNESCO Open Science Portal - Kind Deployment Guide

Complete guide for deploying InvenioRDM on **Kind (Kubernetes in Docker)** for local development and testing.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Data Import](#data-import)
6. [Daily Operations](#daily-operations)
7. [Troubleshooting](#troubleshooting)
8. [Architecture](#architecture)

---

## 🎯 Overview

This deployment uses:

- **Kind**: Local Kubernetes cluster running in Docker
- **Official Helm Chart**: InvenioRDM from `inveniosoftware/helm-invenio`
- **External Services**: PostgreSQL, Redis, RabbitMQ, OpenSearch with public images
- **Custom Image**: Your customized InvenioRDM with compiled assets
- **HTTP Mode**: Simplified for local development (no TLS)

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

## ⚡ Quick Start

The fastest way to get everything running:

```bash
cd k8s

# 1. Deploy everything (takes ~10 minutes)
make kind-full-deploy

# 2. In another terminal, start port forwarding
make kind-port-forward

# 3. Open browser at http://localhost:8080

# 4. Login with:
#    Email: admin@unesco.org
#    Password: admin123

# 5. Import sample data
make kind-reset-lens
```

**Done!** You now have a fully functional InvenioRDM instance with 26 publications.

---

## 📖 Step-by-Step Guide

For more control, deploy step by step:

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

- Builds custom InvenioRDM image from `../Dockerfile`
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
- Installs chart with custom values (`values-unesco.yaml`)
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
- Saves token to `../scripts/config/.env.kind`

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
make kind-scripts-import-lens FILE='../scripts/src/sources/csv/data/publications.csv'

# From Zenodo (single record)
make kind-scripts-import-zenodo RECORD_ID='17462748'

# From Zenodo (search)
make kind-scripts-import-zenodo QUERY='climate data' MAX=5
```

### Manual Import Steps

```bash
# 1. Delete all existing records
make kind-scripts-delete-all

# 2. Import specific file
make kind-scripts-import-lens FILE='../scripts/src/sources/lens/data/publications.json'
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

## 🐛 Troubleshooting

### Pods Not Starting

**Symptoms:** Pods in `Pending`, `CrashLoopBackOff`, or `Error` state

**Diagnose:**

```bash
# Check pod details
kubectl describe pod <pod-name> -n unesco-rdm

# Check logs
kubectl logs <pod-name> -n unesco-rdm --previous

# Check events
kubectl get events -n unesco-rdm --sort-by='.lastTimestamp' | tail -20
```

**Common fixes:**

1. Increase Docker memory (Settings → Resources → Memory: 8GB)
2. Wait for external services to be ready: `kubectl get pods -n unesco-rdm`
3. Restart: `make kind-restart`

---

### Import Fails: "Invalid value"

**Error:** `Invalid value publication-article` or similar

**Cause:** Vocabularies not loaded yet

**Fix:**

```bash
# Re-run initialization
make kind-init

# Wait 2 minutes for workers to process

# Verify vocabularies loaded
kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
  invenio vocabularies search resourcetypes | head -20
```

---

### Port Already in Use

**Error:** Port 8080 already allocated

**Fix:**

```bash
# Find what's using the port
lsof -ti:8080

# Kill it
kill -9 $(lsof -ti:8080)

# Or use different port
kubectl port-forward -n unesco-rdm svc/unesco-rdm-invenio 9000:5000
```

---

### Cannot Access Application

**Symptoms:** http://localhost:8080 not responding

**Checks:**

```bash
# 1. Is port-forward running?
# Should see: "Forwarding from 127.0.0.1:8080 -> 5000"
# If not, run: make kind-port-forward

# 2. Are pods running?
kubectl get pods -n unesco-rdm
# Web pod should be "Running" with "2/2" ready

# 3. Check web logs
make kind-logs
```

---

### Web Pod Killed (Exit Code 137)

**Cause:** Out of memory (OOM)

**Fix:**

1. Increase Docker memory allocation to 8-10GB
2. Or edit `values-unesco.yaml`:

```yaml
web:
  resources:
    limits:
      memory: "3Gi" # Increase from 2Gi
```

3. Redeploy: `make kind-deploy-helm`

---

### Database Connection Errors

**Symptoms:** Cannot connect to PostgreSQL

**Fix:**

```bash
# Check PostgreSQL pod
kubectl get pod -n unesco-rdm postgresql-0

# Check logs
kubectl logs -n unesco-rdm postgresql-0

# Restart if needed
kubectl delete pod -n unesco-rdm postgresql-0
# It will automatically recreate
```

---

### Workers Not Processing Tasks

**Symptoms:** Background tasks stuck

**Fix:**

```bash
# Check worker pods
kubectl get pods -n unesco-rdm | grep worker

# Check logs
kubectl logs -f deployment/unesco-rdm-invenio-worker -n unesco-rdm

# Check RabbitMQ
kubectl exec -n unesco-rdm deployment/rabbitmq -- rabbitmqctl list_queues

# Restart workers
kubectl rollout restart deployment/unesco-rdm-invenio-worker -n unesco-rdm
kubectl rollout restart deployment/unesco-rdm-invenio-worker-beat -n unesco-rdm
```

---

### Search Not Working

**Symptoms:** No results or search errors

**Fix:**

```bash
# Check OpenSearch
kubectl get pod -n unesco-rdm opensearch-0

# Check indices
kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
  invenio index list

# Reindex all records
kubectl exec -n unesco-rdm deployment/unesco-rdm-invenio-web -c web -- \
  invenio index reindex --yes
```

---

## 🧹 Cleanup

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

### Start Fresh

```bash
# Complete removal
make kind-down

# Full redeployment
make kind-full-deploy
```

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

### `values-unesco.yaml`

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

### Cleanup

| Command            | Description                       |
| ------------------ | --------------------------------- |
| `make kind-clean`  | Remove deployment (keep cluster)  |
| `make kind-delete` | Delete Kind cluster               |
| `make kind-down`   | Complete cleanup (clean + delete) |

---

## 🚦 Best Practices

### Development Workflow

1. **Start fresh**: `make kind-full-deploy`
2. **Make changes**: Edit code in parent directory
3. **Rebuild**: `make kind-load-image`
4. **Restart**: `make kind-restart`
5. **Test**: Access at http://localhost:8080
6. **Import data**: `make kind-reset-lens`
7. **Check logs**: `make kind-logs`

### Resource Management

- Monitor usage: `kubectl top pods -n unesco-rdm`
- Adjust limits in `values-unesco.yaml` if needed
- Keep Docker memory allocation ≥ 8GB

### Data Management

- Always test imports with `--limit 10` first
- Use `kind-scripts-delete-all` before large imports
- Keep backup of data files outside cluster

---

## 📚 Additional Resources

- [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/)
- [Helm Chart Repository](https://github.com/inveniosoftware/helm-invenio)
- [Kind Documentation](https://kind.sigs.k8s.io/)
- [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)

---

## 🆘 Getting Help

1. **Check logs**: `make kind-logs`
2. **Check status**: `make kind-status`
3. **Review this guide**: Especially [Troubleshooting](#troubleshooting)
4. **Check InvenioRDM docs**: https://inveniordm.docs.cern.ch/
5. **Clean and retry**: `make kind-down && make kind-full-deploy`

---

**Happy deploying! 🚀**
