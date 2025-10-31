# 🚀 Deployment Guide - UNESCO Science Portal

Guida completa per il deployment di InvenioRDM su Kubernetes usando Helm Charts.

## 📋 Table of Contents

1. [Prerequisiti](#prerequisiti)
2. [Architettura](#architettura)
3. [Build Docker Image](#build-docker-image)
4. [Test Locale con Docker](#test-locale-con-docker)
5. [Deploy su Kubernetes](#deploy-su-kubernetes)
6. [Configurazione Avanzata](#configurazione-avanzata)
7. [Monitoring e Troubleshooting](#monitoring-e-troubleshooting)

---

## 🎯 Prerequisiti

### Software Richiesto

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **kubectl**: >= 1.24
- **Helm**: >= 3.8
- **Make**: installato di default su macOS/Linux

### Conoscenze Richieste

- Concetti base di Docker e containerizzazione
- Kubernetes (Pods, Deployments, Services, ConfigMaps, Secrets)
- Helm Charts
- Networking e DNS

### Accesso Richiesto

- Cluster Kubernetes (fornito dal team infrastruttura)
- Docker Registry per le immagini (es. Harbor, Docker Hub, AWS ECR)
- Credenziali per accedere al cluster (kubeconfig)

---

## 🏗️ Architettura

### Componenti del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Ingress    │──────│    Nginx     │                     │
│  │  Controller  │      │  (Frontend)  │                     │
│  └──────────────┘      └──────────────┘                     │
│         │                      │                             │
│         ├──────────────────────┴──────────────┐             │
│         │                                      │             │
│  ┌──────▼──────┐                      ┌───────▼──────┐     │
│  │   Web-UI    │                      │   Web-API    │     │
│  │   (uWSGI)   │                      │   (uWSGI)    │     │
│  └─────────────┘                      └──────────────┘     │
│         │                                      │             │
│         └──────────────┬───────────────────────┘             │
│                        │                                     │
│         ┌──────────────┴──────────────┐                     │
│         │                              │                     │
│  ┌──────▼──────┐              ┌───────▼──────┐             │
│  │   Worker    │              │  Scheduler   │             │
│  │  (Celery)   │              │(Celery Beat) │             │
│  └─────────────┘              └──────────────┘             │
│         │                              │                     │
│         └──────────────┬───────────────┘                     │
│                        │                                     │
│    ┌───────────────────┼───────────────────┐               │
│    │                   │                   │               │
│ ┌──▼────┐      ┌──────▼──────┐    ┌──────▼──────┐        │
│ │ Redis │      │ PostgreSQL  │    │ OpenSearch  │        │
│ │(Cache)│      │     (DB)    │    │   (Search)  │        │
│ └───────┘      └─────────────┘    └─────────────┘        │
│    │                   │                   │               │
│    └───────────────────┼───────────────────┘               │
│                        │                                     │
│                 ┌──────▼──────┐                             │
│                 │  RabbitMQ   │                             │
│                 │   (Queue)   │                             │
│                 └─────────────┘                             │
│                                                               │
│  Persistent Volumes:                                         │
│  - /opt/invenio/var/instance/data (files)                   │
│  - /opt/invenio/var/instance/archive (archive)              │
│  - PostgreSQL data                                           │
│  - OpenSearch data                                           │
└─────────────────────────────────────────────────────────────┘
```

### Servizi Necessari

| Servizio       | Descrizione                   | Porta       | PVC Required          |
| -------------- | ----------------------------- | ----------- | --------------------- |
| **Nginx**      | Reverse proxy e load balancer | 80, 443     | ❌                    |
| **Web-UI**     | Interfaccia utente (uWSGI)    | 5000        | ✅ (static, uploads)  |
| **Web-API**    | REST API (uWSGI)              | 5000        | ✅ (uploads, archive) |
| **Worker**     | Task asincroni (Celery)       | -           | ✅ (uploads)          |
| **Scheduler**  | Job schedulati (Celery Beat)  | -           | ❌                    |
| **PostgreSQL** | Database relazionale          | 5432        | ✅ (data)             |
| **OpenSearch** | Motore di ricerca             | 9200        | ✅ (indices)          |
| **Redis**      | Cache in-memory               | 6379        | ❌                    |
| **RabbitMQ**   | Message queue                 | 5672, 15672 | ✅ (queue persist)    |

---

## 🐳 Build Docker Image

### 1. Build Locale

```bash
# Build immagine di produzione
make docker-build

# Build immagine di sviluppo (include dev dependencies)
make docker-build-dev

# Verifica l'immagine creata
docker images | grep sc-openscience
```

**Output atteso:**

```
sc-openscience   latest    abc123def456    2 minutes ago    2.1GB
```

### 2. Test dell'Immagine

```bash
# Testa l'immagine localmente
docker run --rm sc-openscience:latest "invenio --version"

# Expected output: InvenioRDM vX.Y.Z
```

### 3. Tag per Registry

```bash
# Imposta il registry (esempio con Harbor)
export DOCKER_REGISTRY="registry.example.com/unesco"

# Tag l'immagine
make docker-tag DOCKER_REGISTRY=$DOCKER_REGISTRY

# Verifica
docker images | grep registry.example.com
```

### 4. Push al Registry

```bash
# Login al registry
docker login registry.example.com

# Push dell'immagine
make docker-push DOCKER_REGISTRY=$DOCKER_REGISTRY
```

**Output atteso:**

```
📤 Pushing image to registry...
The push refers to repository [registry.example.com/unesco/sc-openscience]
abc123: Pushed
def456: Pushed
latest: digest: sha256:... size: 4321
✅ Image pushed!
```

### 5. Build Completo (CI/CD Ready)

```bash
# Build + Tag + Push in un solo comando
make docker-release DOCKER_REGISTRY=$DOCKER_REGISTRY
```

---

## 🧪 Test Locale con Docker

Prima del deploy su Kubernetes, testa tutto in locale con Docker Compose.

### 1. Avvia lo Stack Completo

```bash
# Avvia tutti i servizi (backend + applicazione)
make docker-up
```

**Questo avvia:**

- Frontend (Nginx) su porta 80 e 443
- Web-UI e Web-API (uWSGI)
- Worker e Scheduler (Celery)
- PostgreSQL, OpenSearch, Redis, RabbitMQ

### 2. Inizializza il Database

```bash
# Crea tabelle e indici
make docker-init

# Crea dati demo (opzionale)
make docker-demo
```

### 3. Verifica i Servizi

```bash
# Status di tutti i container
make docker-status

# Logs in tempo reale
make docker-logs

# Logs di un servizio specifico
make docker-logs-service SERVICE=web-ui
```

### 4. Test dell'Applicazione

Apri nel browser:

- **Frontend**: http://localhost
- **OpenSearch Dashboards**: http://localhost:5601
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

### 5. Cleanup

```bash
# Stop dei servizi
make docker-down

# Stop e rimozione volumi (⚠️ dati persi!)
make docker-clean
```

---

## ☸️ Deploy su Kubernetes

### 1. Setup Cluster

Verifica l'accesso al cluster:

```bash
# Controlla la connessione
kubectl cluster-info

# Verifica i nodi
kubectl get nodes

# Crea namespace dedicato
kubectl create namespace unesco-rdm
kubectl config set-context --current --namespace=unesco-rdm
```

### 2. Installa Helm Charts di InvenioRDM

```bash
# Aggiungi il repository Helm di Invenio
helm repo add invenio https://inveniosoftware.github.io/helm-invenio/
helm repo update

# Scarica il chart per personalizzazione
helm pull invenio/invenio --untar
cd invenio
```

### 3. Crea values.yaml Personalizzato

Crea `values-unesco.yaml`:

```yaml
# UNESCO Science Portal - Helm Values

# Image configuration
image:
  repository: registry.example.com/unesco/sc-openscience
  tag: "latest"
  pullPolicy: Always

imagePullSecrets:
  - name: registry-credentials

# Horizontal scaling
replicaCount:
  web-ui: 2
  web-api: 2
  worker: 3

# Resource limits
resources:
  web-ui:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  web-api:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  worker:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"

# Ingress configuration
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
  hosts:
    - host: openscience.unesco.org
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: unesco-rdm-tls
      hosts:
        - openscience.unesco.org

# PostgreSQL configuration
postgresql:
  enabled: true
  auth:
    username: invenio
    password: CHANGEME # Use secret in production!
    database: invenio
  primary:
    persistence:
      enabled: true
      size: 50Gi
      storageClass: standard-rwo

# OpenSearch configuration
opensearch:
  enabled: true
  clusterName: unesco-search
  replicas: 3
  persistence:
    enabled: true
    size: 100Gi
    storageClass: standard-rwo
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"

# Redis configuration
redis:
  enabled: true
  architecture: standalone
  auth:
    enabled: true
    password: CHANGEME # Use secret in production!
  master:
    persistence:
      enabled: false # Cache doesn't need persistence

# RabbitMQ configuration
rabbitmq:
  enabled: true
  auth:
    username: invenio
    password: CHANGEME # Use secret in production!
  persistence:
    enabled: true
    size: 10Gi
    storageClass: standard-rwo

# Persistent volumes for uploads
persistence:
  enabled: true
  uploads:
    size: 200Gi
    storageClass: standard-rwo
  archive:
    size: 100Gi
    storageClass: standard-rwo

# InvenioRDM configuration
invenio:
  secret_key: "CHANGE-ME-TO-RANDOM-STRING" # Use secret in production!
  security:
    login_salt: "CHANGE-ME-RANDOM"
  site:
    name: "UNESCO Science Portal"
    url: "https://openscience.unesco.org"
  theme:
    logo: "/static/images/unesco-logo.svg"

# Extra environment variables from ConfigMap
extraEnvFrom:
  - configMapRef:
      name: unesco-rdm-config

# Extra environment variables from Secret
extraEnvFromSecret:
  - secretRef:
      name: unesco-rdm-secrets
```

### 4. Crea Secrets

**⚠️ NON committare secrets nel repository!**

```bash
# Crea secret per il registry
kubectl create secret docker-registry registry-credentials \
  --docker-server=registry.example.com \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PASSWORD \
  --docker-email=YOUR_EMAIL

# Crea secret per le credenziali dell'applicazione
kubectl create secret generic unesco-rdm-secrets \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=SECURITY_LOGIN_SALT=$(openssl rand -hex 32) \
  --from-literal=SQLALCHEMY_DATABASE_URI="postgresql://invenio:PASSWORD@postgres:5432/invenio" \
  --from-literal=CELERY_BROKER_URL="amqp://invenio:PASSWORD@rabbitmq:5672/" \
  --from-literal=CACHE_REDIS_URL="redis://:PASSWORD@redis:6379/0"

# Verifica i secrets creati
kubectl get secrets
```

### 5. Crea ConfigMap per Configurazione

```bash
# Crea ConfigMap con configurazioni non sensibili
kubectl create configmap unesco-rdm-config \
  --from-literal=INVENIO_SITE_NAME="UNESCO Science Portal" \
  --from-literal=INVENIO_SITE_URL="https://openscience.unesco.org" \
  --from-literal=INVENIO_THEME_LOGO="/static/images/unesco-logo.svg"

# Verifica
kubectl get configmap unesco-rdm-config -o yaml
```

### 6. Deploy con Helm

```bash
# Dry-run per verificare
helm install unesco-rdm invenio/invenio \
  -f values-unesco.yaml \
  --namespace unesco-rdm \
  --dry-run --debug

# Deploy effettivo
helm install unesco-rdm invenio/invenio \
  -f values-unesco.yaml \
  --namespace unesco-rdm

# Verifica lo stato del deploy
helm status unesco-rdm -n unesco-rdm
```

### 7. Verifica i Pod

```bash
# Lista tutti i pod
kubectl get pods

# Attendi che tutti i pod siano Running
kubectl wait --for=condition=Ready pods --all --timeout=300s

# Controlla i logs
kubectl logs -f deployment/unesco-rdm-web-ui
```

### 8. Inizializza il Database

```bash
# Esegui init solo una volta
kubectl exec -it deployment/unesco-rdm-web-ui -- invenio db init
kubectl exec -it deployment/unesco-rdm-web-ui -- invenio db create
kubectl exec -it deployment/unesco-rdm-web-ui -- invenio index init
kubectl exec -it deployment/unesco-rdm-web-ui -- invenio index queue init purge
kubectl exec -it deployment/unesco-rdm-web-ui -- invenio files location create --default 'default-location' /opt/invenio/var/instance/data
kubectl exec -it deployment/unesco-rdm-web-ui -- invenio roles create admin
kubectl exec -it deployment/unesco-rdm-web-ui -- invenio access allow superuser-access role admin

# Crea demo data (opzionale)
kubectl exec -it deployment/unesco-rdm-web-ui -- invenio rdm-records demo
```

### 9. Test dell'Applicazione

```bash
# Port-forward per test locale (se non hai ancora Ingress)
kubectl port-forward service/unesco-rdm-web-ui 5000:5000

# Oppure accedi tramite Ingress
curl https://openscience.unesco.org
```

---

## 🔧 Configurazione Avanzata

### 1. Horizontal Pod Autoscaler (HPA)

```yaml
# hpa-web-ui.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: unesco-rdm-web-ui
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: unesco-rdm-web-ui
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

```bash
kubectl apply -f hpa-web-ui.yaml
kubectl get hpa
```

### 2. Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: unesco-rdm-network-policy
spec:
  podSelector:
    matchLabels:
      app: unesco-rdm
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 5000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgresql
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: opensearch
      ports:
        - protocol: TCP
          port: 9200
```

### 3. Resource Quotas

```yaml
# resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: unesco-rdm-quota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
```

### 4. Pod Disruption Budget

```yaml
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: unesco-rdm-web-ui-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: unesco-rdm-web-ui
```

---

## 📊 Monitoring e Troubleshooting

### 1. Prometheus & Grafana

```bash
# Installa Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# ServiceMonitor per InvenioRDM
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: unesco-rdm-metrics
spec:
  selector:
    matchLabels:
      app: unesco-rdm
  endpoints:
  - port: metrics
    interval: 30s
EOF
```

### 2. Logging con Loki

```bash
# Installa Loki Stack
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --set grafana.enabled=true \
  --namespace monitoring
```

### 3. Troubleshooting Comandi

```bash
# Eventi del cluster
kubectl get events --sort-by='.lastTimestamp'

# Logs di un pod con errori
kubectl logs <pod-name> --previous

# Describe pod per dettagli
kubectl describe pod <pod-name>

# Exec in un pod
kubectl exec -it <pod-name> -- bash

# Port-forward per debug
kubectl port-forward <pod-name> 5000:5000

# Top resources
kubectl top pods
kubectl top nodes
```

### 4. Health Checks

```bash
# Verifica readiness
kubectl get pods -o wide

# Test health endpoint
kubectl exec -it deployment/unesco-rdm-web-ui -- curl localhost:5000/ping
```

---

## 🔄 Aggiornamenti e Rollback

### 1. Aggiornamento dell'Applicazione

```bash
# Build e push nuova versione
make docker-build DOCKER_IMAGE_TAG=v1.1.0
make docker-tag DOCKER_REGISTRY=$DOCKER_REGISTRY DOCKER_IMAGE_TAG=v1.1.0
make docker-push DOCKER_REGISTRY=$DOCKER_REGISTRY DOCKER_IMAGE_TAG=v1.1.0

# Aggiorna il deployment
helm upgrade unesco-rdm invenio/invenio \
  -f values-unesco.yaml \
  --set image.tag=v1.1.0 \
  --namespace unesco-rdm

# Verifica il rollout
kubectl rollout status deployment/unesco-rdm-web-ui
```

### 2. Rollback

```bash
# Lista revisioni
helm history unesco-rdm -n unesco-rdm

# Rollback all'ultima versione funzionante
helm rollback unesco-rdm -n unesco-rdm

# Rollback a una revisione specifica
helm rollback unesco-rdm 3 -n unesco-rdm
```

---

## 📚 Risorse Utili

- **Helm Charts Ufficiali**: https://github.com/inveniosoftware/helm-invenio
- **Documentazione InvenioRDM**: https://inveniordm.docs.cern.ch/
- **Kubernetes Best Practices**: https://kubernetes.io/docs/concepts/configuration/overview/
- **Helm Documentation**: https://helm.sh/docs/

---

## 🆘 Supporto

Per problemi o domande:

1. Controlla i logs: `make docker-logs` o `kubectl logs`
2. Verifica la documentazione in `docs/`
3. Contatta il team di sviluppo

---

**Buon deploy! 🚀**
