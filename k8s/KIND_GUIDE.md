# 🎯 Local Kubernetes with Kind - Quick Start

Questa guida ti mostra come fare il deploy locale su Kubernetes usando **Kind** (Kubernetes in Docker).

## 📋 Prerequisiti

### Installazione Software

```bash
# macOS (usando Homebrew)
brew install kind kubectl helm

# Linux
# Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Verifica Installazione

```bash
# Controlla che tutto sia installato
make kind-check
```

Output atteso:

```
✅ All required tools installed!
   - kind:    kind v0.20.0 go1.20.4 darwin/arm64
   - kubectl: Client Version: v1.28.2
   - helm:    v3.13.0
```

---

## 🚀 Setup Completo (Un Comando)

Il modo più semplice per avviare tutto:

```bash
# Setup completo: crea cluster + build image + deploy + init
make kind-up
```

Questo comando:

1. ✅ Crea un cluster Kind con 3 nodi (1 control-plane + 2 worker)
2. ✅ Installa Ingress NGINX
3. ✅ Builda l'immagine Docker dell'applicazione
4. ✅ Carica l'immagine nel cluster Kind
5. ✅ Deploya InvenioRDM con Helm
6. ✅ Inizializza database e indici
7. ✅ Crea dati demo

**Tempo stimato**: 10-15 minuti

---

## 📝 Setup Passo-Passo (Opzionale)

Se preferisci avere più controllo:

### 1. Crea il Cluster

```bash
# Crea cluster Kind con configurazione custom
make kind-create
```

Questo crea:

- 1 control-plane node
- 2 worker nodes
- Port mapping per HTTP (80) e HTTPS (443)
- Ingress NGINX pre-installato

### 2. Build e Carica l'Immagine

```bash
# Build dell'immagine e caricamento in Kind
make kind-load-image
```

Nota: Questo comando builda l'immagine Docker e la carica direttamente nel cluster Kind (non serve un registry esterno).

### 3. Deploy con Helm

```bash
# Deploy di InvenioRDM
make kind-deploy
```

Questo:

- Configura i repository Helm
- Crea namespace `unesco-rdm`
- Crea secrets
- Deploya con Helm usando `k8s/values-kind.yaml`

### 4. Inizializza Database

```bash
# Inizializza database e crea demo data
make kind-init
```

---

## 🌐 Accesso all'Applicazione

### Metodo 1: Via Ingress (Raccomandato)

```bash
# Apri nel browser
open http://localhost
```

L'Ingress è già configurato e mappato sulla porta 80 del tuo sistema.

### Metodo 2: Via Port-Forward

```bash
# Port-forward del servizio
make kind-port-forward

# Poi apri: http://localhost:5000
```

---

## 📊 Monitoraggio

### Verifica Status

```bash
# Status completo del cluster
make kind-status
```

Output:

```
📊 Checking Kind cluster status...

🔍 Cluster nodes:
NAME                       STATUS   ROLES           AGE     VERSION
unesco-rdm-control-plane   Ready    control-plane   5m      v1.28.0
unesco-rdm-worker          Ready    <none>          4m30s   v1.28.0
unesco-rdm-worker2         Ready    <none>          4m30s   v1.28.0

📦 Pods in unesco-rdm namespace:
NAME                                    READY   STATUS    RESTARTS   AGE
unesco-rdm-web-ui-xxx                   1/1     Running   0          3m
unesco-rdm-web-api-xxx                  1/1     Running   0          3m
unesco-rdm-worker-xxx                   1/1     Running   0          3m
postgresql-xxx                          1/1     Running   0          3m
...
```

### View Logs

```bash
# Logs dell'applicazione
make kind-logs

# O con kubectl direttamente
kubectl logs -f deployment/unesco-rdm-web-ui -n unesco-rdm
```

### Shell nel Pod

```bash
# Apri bash nel container web-ui
make kind-shell

# Comandi utili dentro il pod:
invenio shell                    # Python shell
invenio users list              # Lista utenti
invenio records list            # Lista record
```

---

## 🔄 Aggiornamenti

### Ricarica Nuova Immagine

Dopo aver modificato il codice:

```bash
# 1. Rebuild e reload immagine
make kind-load-image

# 2. Restart deployment per usare nuova immagine
make kind-restart

# 3. Aspetta che i pod siano ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=web-ui -n unesco-rdm
```

### Update Configurazione Helm

```bash
# Modifica k8s/values-kind.yaml

# Aggiorna deployment
helm upgrade unesco-rdm invenio/invenio \
  -f k8s/values-kind.yaml \
  -n unesco-rdm

# Verifica
make kind-status
```

---

## 🧪 Testing e Debug

### Esegui Comandi nel Pod

```bash
# Verifica versione
kubectl exec deployment/unesco-rdm-web-ui -n unesco-rdm -- invenio --version

# Test connessione database
kubectl exec deployment/unesco-rdm-web-ui -n unesco-rdm -- \
  invenio shell -c "from invenio_db import db; print(db.engine.execute('SELECT 1').scalar())"

# Crea utente admin
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- \
  invenio users create admin@test.com --password=123456 --active

# Assegna ruolo admin
kubectl exec deployment/unesco-rdm-web-ui -n unesco-rdm -- \
  invenio roles add admin@test.com admin
```

### Verifica Servizi Backend

```bash
# PostgreSQL
kubectl exec -it deployment/postgresql -n unesco-rdm -- \
  psql -U invenio -d invenio -c "\dt"

# Redis
kubectl exec -it deployment/redis -n unesco-rdm -- \
  redis-cli ping

# RabbitMQ
kubectl exec -it deployment/rabbitmq -n unesco-rdm -- \
  rabbitmqctl status
```

### Port-Forward Servizi Backend

```bash
# OpenSearch
kubectl port-forward svc/opensearch -n unesco-rdm 9200:9200
# Poi: curl http://localhost:9200

# RabbitMQ Management
kubectl port-forward svc/rabbitmq -n unesco-rdm 15672:15672
# Poi: http://localhost:15672 (invenio/invenio123)

# PostgreSQL
kubectl port-forward svc/postgresql -n unesco-rdm 5432:5432
# Poi: psql -h localhost -U invenio -d invenio
```

---

## 🧹 Pulizia

### Rimuovi Deployment (Mantieni Cluster)

```bash
# Rimuove solo l'applicazione
make kind-clean
```

Questo elimina:

- Helm release
- Namespace `unesco-rdm`
- Tutti i pod e PVC

### Elimina Cluster Completo

```bash
# Elimina tutto il cluster Kind
make kind-delete
```

### Teardown Completo

```bash
# Clean + Delete in un comando
make kind-down
```

---

## ⚙️ Configurazione

### File Importanti

- **k8s/kind-config.yaml**: Configurazione cluster Kind
- **k8s/values-kind.yaml**: Valori Helm per deployment locale
- **Makefile**: Comandi automatizzati

### Personalizzazione values-kind.yaml

```yaml
# Modifica risorse se hai limitazioni hardware
resources:
  web-ui:
    requests:
      memory: "256Mi" # Ridotto da 512Mi
      cpu: "100m" # Ridotto da 250m

# Disabilita servizi se non necessari
opensearch:
  enabled: false # Usa un search engine esterno

# Cambia numero di replicas
replicaCount:
  web-ui: 2 # Aumenta per HA
```

---

## 🐛 Troubleshooting

### Pod in CrashLoopBackOff

```bash
# Vedi logs del pod
kubectl logs <pod-name> --previous -n unesco-rdm

# Describe per dettagli
kubectl describe pod <pod-name> -n unesco-rdm
```

### Immagine non Trovata

```bash
# Verifica che l'immagine sia caricata
docker exec -it unesco-rdm-control-plane crictl images | grep sc-openscience

# Ricarica se necessario
make kind-load-image
```

### Ingress non Funziona

```bash
# Verifica Ingress NGINX
kubectl get pods -n ingress-nginx

# Verifica Ingress rules
kubectl get ingress -n unesco-rdm -o yaml

# Test diretto (bypass ingress)
make kind-port-forward
```

### Database Connection Issues

```bash
# Verifica secret
kubectl get secret unesco-rdm-secrets -n unesco-rdm -o jsonpath='{.data.SQLALCHEMY_DATABASE_URI}' | base64 -d

# Test connessione
kubectl exec deployment/unesco-rdm-web-ui -n unesco-rdm -- \
  bash -c 'echo "SELECT 1" | psql $SQLALCHEMY_DATABASE_URI'
```

### Out of Resources

```bash
# Riduci replicas in values-kind.yaml
replicaCount:
  web-ui: 1
  web-api: 1
  worker: 1

# Riduci risorse
resources:
  web-ui:
    requests:
      memory: "256Mi"
      cpu: "100m"

# Rideploy
helm upgrade unesco-rdm invenio/invenio -f k8s/values-kind.yaml -n unesco-rdm
```

---

## 📚 Comandi Utili

```bash
# Verifica tutto funzioni
make kind-check         # Check tools
make kind-status        # Cluster status
make kind-logs          # App logs

# Gestione cluster
make kind-create        # Crea cluster
make kind-delete        # Elimina cluster
make kind-up            # Setup completo
make kind-down          # Teardown completo

# Gestione applicazione
make kind-deploy        # Deploy app
make kind-init          # Init DB
make kind-restart       # Restart app
make kind-clean         # Remove app

# Debug
make kind-shell         # Shell nel pod
make kind-port-forward  # Port forwarding

# Aggiornamenti
make kind-load-image    # Reload immagine
make kind-restart       # Restart dopo reload
```

---

## 🎓 Tips & Best Practices

### Performance

- **Memory**: Assegna almeno 8GB a Docker Desktop
- **CPU**: Almeno 4 cores raccomandati
- **Disk**: Usa SSD per performance migliori

### Development Workflow

```bash
# 1. Setup iniziale (una volta)
make kind-up

# 2. Sviluppa codice...

# 3. Test modifiche
make kind-load-image
make kind-restart
make kind-logs

# 4. Debug se necessario
make kind-shell
make kind-port-forward

# 5. Cleanup quando finito
make kind-down
```

### Monitoring Continuo

```bash
# Terminal 1: Logs
make kind-logs

# Terminal 2: Watch pods
watch kubectl get pods -n unesco-rdm

# Terminal 3: Development
# ... fai modifiche al codice ...
```

---

## 🆘 Help

Per problemi:

1. **Check status**: `make kind-status`
2. **Check logs**: `make kind-logs`
3. **Check events**: `kubectl get events -n unesco-rdm --sort-by='.lastTimestamp'`
4. **Descrivi pod**: `kubectl describe pod <pod-name> -n unesco-rdm`
5. **Consulta documentazione**: `docs/DEPLOYMENT.md`

---

**Happy local Kubernetes deployment! 🚀**
