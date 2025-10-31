# 📊 Deployment Strategy Summary - UNESCO Science Portal

## 🎯 Overview

Questa guida riassume la strategia completa di deployment per InvenioRDM su Kubernetes e Docker.

---

## 📦 Cosa È Stato Configurato

### 1. **Dockerfile Ottimizzato** (`Dockerfile`)

- ✅ Base image: `registry.cern.ch/inveniosoftware/almalinux:1`
- ✅ Support per build args (`PIPENV_INSTALL_DEV`)
- ✅ Health checks integrati
- ✅ Labels per metadata
- ✅ Ottimizzato per produzione

### 2. **Docker Compose Full Stack** (`docker-compose.full.yml`)

- ✅ Nginx frontend (porta 80, 443)
- ✅ Web-UI (uWSGI)
- ✅ Web-API (uWSGI)
- ✅ Celery Worker
- ✅ Celery Scheduler
- ✅ PostgreSQL
- ✅ OpenSearch
- ✅ Redis
- ✅ RabbitMQ

### 3. **Makefile Commands**

Nuovi comandi aggiunti:

#### Build & Release

- `make docker-build` - Build immagine produzione
- `make docker-build-dev` - Build immagine development
- `make docker-tag` - Tag per registry
- `make docker-push` - Push al registry
- `make docker-release` - Build + Tag + Push (workflow completo)

#### Stack Management

- `make docker-up` - Avvia stack completo
- `make docker-down` - Ferma stack
- `make docker-restart` - Restart stack
- `make docker-init` - Inizializza database
- `make docker-demo` - Crea dati demo
- `make docker-clean` - Pulizia completa (⚠️ distruttivo)

#### Monitoring & Debug

- `make docker-logs` - Logs tutti i servizi
- `make docker-logs-service SERVICE=name` - Logs servizio specifico
- `make docker-status` - Status containers
- `make docker-shell` - Shell nel container
- `make docker-exec CMD='command'` - Esegui comando

### 4. **Kubernetes Deployment Files** (`k8s/`)

#### `values-production.yaml`

Configurazione Helm completa con:

- 📦 Image repository e tag
- 🔢 Replica count per ogni componente
- 💾 Resource limits (CPU, memory)
- 🌐 Ingress con SSL
- 🗄️ PostgreSQL config
- 🔍 OpenSearch config (3 replicas HA)
- 🚀 Redis config
- 📬 RabbitMQ config
- 💿 Persistent volumes
- 🔐 Security contexts
- 📊 Monitoring config

#### `setup.sh`

Script automatico che:

- ✅ Crea namespace Kubernetes
- ✅ Genera secrets random sicuri
- ✅ Crea registry credentials
- ✅ Crea ConfigMaps
- ✅ Aggiunge Helm repositories
- ✅ Salva credentials in `.k8s-secrets`

### 5. **Documentation**

#### `DEPLOYMENT.md` (Root)

Guida completa con:

- 📋 Architettura del sistema
- 🐳 Build Docker images
- 🧪 Test locale con Docker
- ☸️ Deploy su Kubernetes step-by-step
- 🔧 Configurazione avanzata (HPA, Network Policies, etc.)
- 📊 Monitoring & troubleshooting
- 🔄 Update e rollback procedures

#### `k8s/README.md`

Guida specifica per Kubernetes:

- 🚀 Quick start
- 📝 File configuration
- 🔐 Gestione secrets
- 🔄 Procedure di update
- 📊 Monitoring commands
- 🧹 Cleanup procedures
- 🔧 Troubleshooting guide

### 6. **Security Files**

#### `.dockerignore`

Ottimizzato per build veloci:

- Exclude `.venv/`, `logs/`, `docs/`
- Exclude `.git/`, test files
- Exclude sensitive files

#### `.gitignore`

Aggiunto:

- `.k8s-secrets` (⚠️ CRITICO!)
- `k8s/values-production.local.yaml`
- `k8s/secrets/`

---

## 🎮 Workflow Completo

### 🧪 Fase 1: Test Locale con Docker

```bash
# 1. Build immagine
make docker-build

# 2. Avvia stack completo
make docker-up

# 3. Inizializza database
make docker-init

# 4. Test applicazione
open http://localhost

# 5. Verifica logs
make docker-logs

# 6. Stop
make docker-down
```

**Risultato**: Stack completo funzionante in locale con tutti i servizi.

---

### 🏗️ Fase 2: Build per Produzione

```bash
# 1. Build immagine production
make docker-build DOCKER_IMAGE_TAG=v1.0.0

# 2. Tag per registry
make docker-tag \
  DOCKER_REGISTRY=registry.example.com \
  DOCKER_IMAGE_TAG=v1.0.0

# 3. Push al registry
make docker-push \
  DOCKER_REGISTRY=registry.example.com \
  DOCKER_IMAGE_TAG=v1.0.0

# O tutto insieme:
make docker-release \
  DOCKER_REGISTRY=registry.example.com \
  DOCKER_IMAGE_TAG=v1.0.0
```

**Risultato**: Immagine Docker disponibile nel registry aziendale.

---

### ☸️ Fase 3: Deploy su Kubernetes

#### Step 1: Setup Iniziale

```bash
# Imposta variabili
export NAMESPACE=unesco-rdm
export DOCKER_REGISTRY=registry.example.com
export REGISTRY_USER=your-username
export REGISTRY_PASS=your-password

# Esegui setup
cd k8s
./setup.sh
```

**Output**:

- ✅ Namespace creato
- ✅ Secrets generati
- ✅ ConfigMaps creati
- ✅ File `.k8s-secrets` con credenziali

#### Step 2: Configura values.yaml

```bash
# Copia e modifica
cp k8s/values-production.yaml k8s/values-production.local.yaml

# Aggiorna:
# - image.repository
# - ingress.hosts
# - Password da .k8s-secrets
```

#### Step 3: Deploy con Helm

```bash
# Deploy
helm install unesco-rdm invenio/invenio \
  -f k8s/values-production.local.yaml \
  --namespace unesco-rdm

# Verifica
kubectl get pods -n unesco-rdm
```

#### Step 4: Inizializza Database

```bash
# Aspetta che pod siano ready
kubectl wait --for=condition=Ready pods --all -n unesco-rdm --timeout=300s

# Inizializza
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- \
  bash -c "
    invenio db init && \
    invenio db create && \
    invenio index init && \
    invenio files location create --default 'default-location' /opt/invenio/var/instance/data && \
    invenio roles create admin && \
    invenio access allow superuser-access role admin
  "
```

#### Step 5: Verifica Deployment

```bash
# Status
helm status unesco-rdm -n unesco-rdm

# Pods
kubectl get pods -n unesco-rdm

# Logs
kubectl logs -f deployment/unesco-rdm-web-ui -n unesco-rdm

# Test accesso
# Se hai Ingress configurato:
curl https://openscience.unesco.org

# Altrimenti port-forward:
kubectl port-forward service/unesco-rdm-web-ui 5000:5000 -n unesco-rdm
# Poi: open http://localhost:5000
```

**Risultato**: Applicazione funzionante su Kubernetes!

---

## 📊 Architettura Kubernetes

```
┌─────────────────────────────────────────────────────────┐
│                    Ingress Controller                    │
│              (openscience.unesco.org)                   │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴──────────┐
         │                      │
    ┌────▼────┐          ┌─────▼─────┐
    │ Web-UI  │          │  Web-API  │
    │ (x2)    │          │   (x2)    │
    └────┬────┘          └─────┬─────┘
         │                      │
         └──────────┬───────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼────┐         ┌─────▼─────┐
    │ Worker  │         │ Scheduler │
    │  (x3)   │         │    (x1)   │
    └────┬────┘         └─────┬─────┘
         │                     │
         └──────────┬──────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼────┐   ┌─────▼──────┐   ┌───▼────────┐
│ Redis  │   │PostgreSQL  │   │OpenSearch  │
│        │   │            │   │   (x3)     │
└────────┘   └────────────┘   └────────────┘
                    │
             ┌──────▼──────┐
             │  RabbitMQ   │
             └─────────────┘

Persistent Volumes:
├── uploads (200Gi)
├── archive (100Gi)
├── postgresql-data (50Gi)
└── opensearch-data (100Gi x3)
```

---

## 🔐 Security Checklist

### Prima del Deploy

- [ ] Cambia tutte le password in `values-production.yaml`
- [ ] Usa Kubernetes Secrets per credenziali sensibili
- [ ] Configura TLS/SSL con cert-manager
- [ ] Review `securityContext` in values.yaml
- [ ] Configura Network Policies
- [ ] Abilita RBAC
- [ ] Configura Resource Quotas

### Secrets Management

```bash
# ❌ MAI così:
postgresql:
  auth:
    password: "mypassword123"

# ✅ Usa così:
# 1. Crea secret
kubectl create secret generic postgres-secret \
  --from-literal=password=$(openssl rand -base64 32) \
  -n unesco-rdm

# 2. Riferisci in values.yaml
postgresql:
  auth:
    existingSecret: postgres-secret
    secretKeys:
      adminPasswordKey: password
```

---

## 🚨 Production Checklist

### Infrastructure

- [ ] Kubernetes cluster >= 3 nodi
- [ ] Storage class configurato (RWX per uploads)
- [ ] Backup strategy per PVC
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Logging aggregation (Loki/ELK)
- [ ] Alerting configurato

### Application

- [ ] Image taggate con semantic versioning (non `latest`)
- [ ] Resource limits configurati
- [ ] Health checks attivi
- [ ] Horizontal Pod Autoscaler configurato
- [ ] Pod Disruption Budget impostato
- [ ] Ingress con SSL valido

### Database

- [ ] Backup automatici configurati
- [ ] Replication attiva (se HA)
- [ ] Connection pooling ottimizzato
- [ ] Monitoring queries lente

### Search (OpenSearch)

- [ ] Cluster con 3+ nodi per HA
- [ ] Snapshots automatici
- [ ] Monitoring cluster health
- [ ] Index rotation configurata

---

## 🔄 Workflow CI/CD Suggerito

### GitHub Actions Example

```yaml
name: Build and Deploy

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Registry
        uses: docker/login-action@v2
        with:
          registry: registry.example.com
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_PASS }}

      - name: Build and push
        run: |
          export DOCKER_REGISTRY=registry.example.com
          export DOCKER_IMAGE_TAG=${GITHUB_REF#refs/tags/}
          make docker-release

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          helm upgrade --install unesco-rdm invenio/invenio \
            -f k8s/values-production.yaml \
            --set image.tag=${GITHUB_REF#refs/tags/} \
            --namespace unesco-rdm
```

---

## 📚 Risorse Helm Charts

### Repository Ufficiale

- **URL**: https://github.com/inveniosoftware/helm-invenio
- **Chart**: `invenio/invenio`
- **Documentazione**: https://inveniordm.docs.cern.ch/

### Comandi Utili

```bash
# Aggiungi repo
helm repo add invenio https://inveniosoftware.github.io/helm-invenio/

# Update repos
helm repo update

# Cerca chart
helm search repo invenio

# Scarica chart per customization
helm pull invenio/invenio --untar

# Verifica template
helm template unesco-rdm invenio/invenio -f values-production.yaml

# Dry-run
helm install unesco-rdm invenio/invenio -f values-production.yaml --dry-run --debug

# Install
helm install unesco-rdm invenio/invenio -f values-production.yaml

# Upgrade
helm upgrade unesco-rdm invenio/invenio -f values-production.yaml

# Rollback
helm rollback unesco-rdm

# Uninstall
helm uninstall unesco-rdm
```

---

## 🎓 Best Practices

### 1. Versionamento

```bash
# ✅ Usa semantic versioning
make docker-build DOCKER_IMAGE_TAG=v1.2.3

# ❌ Evita latest in produzione
# make docker-build DOCKER_IMAGE_TAG=latest
```

### 2. Resource Limits

```yaml
# ✅ Sempre specificare requests e limits
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### 3. Monitoring

```bash
# Setup Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Setup Grafana dashboards
# Import dashboard ID: 315 (Kubernetes cluster monitoring)
```

### 4. Backup

```bash
# Backup PostgreSQL
kubectl exec -it postgresql-0 -n unesco-rdm -- \
  pg_dump -U invenio invenio > backup-$(date +%Y%m%d).sql

# Backup PVC
velero backup create unesco-backup --include-namespaces unesco-rdm
```

---

## 🆘 Troubleshooting Quick Reference

| Problema         | Comando Debug                               | Soluzione                     |
| ---------------- | ------------------------------------------- | ----------------------------- |
| Pod CrashLoop    | `kubectl logs <pod> --previous`             | Check logs per errori         |
| ImagePullBackOff | `kubectl describe pod <pod>`                | Verifica registry credentials |
| Pending PVC      | `kubectl describe pvc <pvc>`                | Verifica storage class        |
| DB Connection    | `kubectl exec -it <pod> -- env \| grep SQL` | Verifica secrets              |
| High CPU         | `kubectl top pods`                          | Increase limits o scale       |
| OOM Kill         | `kubectl describe pod <pod>`                | Increase memory limits        |

---

## 📞 Support

Per problemi:

1. **Logs**: `make docker-logs` o `kubectl logs`
2. **Documentation**:
   - Root: `DEPLOYMENT.md`
   - K8s: `k8s/README.md`
3. **Official docs**: https://inveniordm.docs.cern.ch/
4. **Team**: Contatta il team di sviluppo

---

## ✅ Summary

Hai ora a disposizione:

1. ✅ **Docker locale** - Test completo in locale
2. ✅ **Build pipeline** - Comandi Make per CI/CD
3. ✅ **Kubernetes deploy** - Helm charts + scripts
4. ✅ **Documentation** - Guide complete step-by-step
5. ✅ **Security** - Best practices e checklist
6. ✅ **Monitoring** - Setup per observability
7. ✅ **Troubleshooting** - Guide e comandi

**Prossimi passi:**

1. Testa in locale: `make docker-up`
2. Build immagine: `make docker-build`
3. Setup K8s: `cd k8s && ./setup.sh`
4. Deploy: `helm install`

**Good luck! 🚀**
