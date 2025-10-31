# 🎯 Kubernetes Deployment Files

Questa directory contiene tutti i file necessari per il deployment su Kubernetes.

## 📁 Struttura

```
k8s/
├── README.md                    # Questa guida
├── setup.sh                     # Script di setup automatico
├── values-production.yaml       # Configurazione Helm per produzione
├── values-staging.yaml          # (da creare) Configurazione per staging
└── manifests/                   # (opzionale) Manifest K8s custom
```

## 🚀 Quick Start

### 1. Setup Iniziale

```bash
# Imposta le variabili d'ambiente
export NAMESPACE=unesco-rdm
export DOCKER_REGISTRY=registry.example.com
export REGISTRY_USER=your-username
export REGISTRY_PASS=your-password
export REGISTRY_EMAIL=your-email@example.com

# Esegui lo script di setup
./k8s/setup.sh
```

Lo script:

- ✅ Crea il namespace
- ✅ Genera secrets random per sicurezza
- ✅ Crea registry credentials
- ✅ Crea ConfigMap
- ✅ Aggiunge repository Helm
- ✅ Salva credenziali in `.k8s-secrets` (⚠️ non committare!)

### 2. Deploy

```bash
# Deploy con Helm
helm install unesco-rdm invenio/invenio \
  -f k8s/values-production.yaml \
  --namespace unesco-rdm

# Verifica lo stato
helm status unesco-rdm -n unesco-rdm
kubectl get pods -n unesco-rdm
```

### 3. Inizializzazione Database

```bash
# Aspetta che i pod siano ready
kubectl wait --for=condition=Ready pods --all -n unesco-rdm --timeout=300s

# Inizializza
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- invenio db init
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- invenio db create
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- invenio index init
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- invenio files location create --default 'default-location' /opt/invenio/var/instance/data
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- invenio roles create admin
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- invenio access allow superuser-access role admin
```

## 📝 File Configurazione

### values-production.yaml

Configurazione principale per il deployment di produzione. Contiene:

- **Image**: Repository e tag dell'immagine Docker
- **Replicas**: Numero di pod per ogni componente
- **Resources**: Limiti CPU e memoria
- **Ingress**: Configurazione dominio e SSL
- **PostgreSQL**: Config database
- **OpenSearch**: Config search engine
- **Redis**: Config cache
- **RabbitMQ**: Config message queue
- **Persistence**: Config volumi persistenti

#### Sezioni da Personalizzare

```yaml
# 1. Immagine Docker
image:
  repository: YOUR_REGISTRY/unesco/sc-openscience
  tag: "v1.0.0"

# 2. Dominio
ingress:
  hosts:
    - host: YOUR_DOMAIN.com

# 3. Password (usa valori da .k8s-secrets)
postgresql:
  auth:
    password: "FROM_.K8S-SECRETS"

redis:
  auth:
    password: "FROM_.K8S-SECRETS"

rabbitmq:
  auth:
    password: "FROM_.K8S-SECRETS"
```

## 🔐 Gestione Secrets

### File .k8s-secrets

Dopo aver eseguito `setup.sh`, trovi le credenziali in `.k8s-secrets`:

```bash
# Visualizza secrets
cat .k8s-secrets

# Usa per aggiornare values.yaml
# NON committare questo file!
```

### Secrets in Kubernetes

```bash
# Lista secrets
kubectl get secrets -n unesco-rdm

# Visualizza un secret
kubectl get secret unesco-rdm-secrets -n unesco-rdm -o yaml

# Aggiorna un secret
kubectl create secret generic unesco-rdm-secrets \
  --from-literal=KEY=VALUE \
  --dry-run=client -o yaml | kubectl apply -f -
```

## 🔄 Aggiornamenti

### Update dell'Applicazione

```bash
# 1. Build e push nuova immagine
cd ..
make docker-build DOCKER_IMAGE_TAG=v1.1.0
make docker-push DOCKER_REGISTRY=$DOCKER_REGISTRY DOCKER_IMAGE_TAG=v1.1.0

# 2. Aggiorna deployment
helm upgrade unesco-rdm invenio/invenio \
  -f k8s/values-production.yaml \
  --set image.tag=v1.1.0 \
  --namespace unesco-rdm

# 3. Verifica rollout
kubectl rollout status deployment/unesco-rdm-web-ui -n unesco-rdm
```

### Rollback

```bash
# Lista revisioni
helm history unesco-rdm -n unesco-rdm

# Rollback
helm rollback unesco-rdm <revision> -n unesco-rdm
```

## 📊 Monitoring

### Logs

```bash
# Tutti i logs
kubectl logs -f -l app=unesco-rdm -n unesco-rdm --all-containers=true

# Logs specifici
kubectl logs -f deployment/unesco-rdm-web-ui -n unesco-rdm
kubectl logs -f deployment/unesco-rdm-worker -n unesco-rdm

# Logs con stern (se installato)
stern unesco-rdm -n unesco-rdm
```

### Metriche

```bash
# Resource usage
kubectl top pods -n unesco-rdm
kubectl top nodes

# Eventi
kubectl get events -n unesco-rdm --sort-by='.lastTimestamp'
```

### Debug

```bash
# Describe pod
kubectl describe pod <pod-name> -n unesco-rdm

# Shell nel pod
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- bash

# Port-forward per test
kubectl port-forward service/unesco-rdm-web-ui 5000:5000 -n unesco-rdm
```

## 🧹 Cleanup

### Rimozione Completa

```bash
# Disinstalla Helm release
helm uninstall unesco-rdm -n unesco-rdm

# Elimina PVC (⚠️ dati persi!)
kubectl delete pvc --all -n unesco-rdm

# Elimina namespace
kubectl delete namespace unesco-rdm
```

### Pulizia Parziale

```bash
# Solo l'applicazione (mantiene dati)
helm uninstall unesco-rdm -n unesco-rdm

# Reinstalla senza perdere dati
helm install unesco-rdm invenio/invenio -f k8s/values-production.yaml -n unesco-rdm
```

## 🎓 Comandi Utili

```bash
# Status generale
kubectl get all -n unesco-rdm

# Verifica HPA
kubectl get hpa -n unesco-rdm

# Verifica PV/PVC
kubectl get pv,pvc -n unesco-rdm

# Verifica Ingress
kubectl get ingress -n unesco-rdm
kubectl describe ingress unesco-rdm -n unesco-rdm

# Test connettività interna
kubectl run -it --rm debug --image=alpine --restart=Never -n unesco-rdm -- sh
# Dentro al pod: apk add curl && curl http://unesco-rdm-web-ui:5000/ping
```

## 🔧 Troubleshooting

### Pod in CrashLoopBackOff

```bash
# Vedi i logs
kubectl logs <pod-name> --previous -n unesco-rdm

# Describe per dettagli
kubectl describe pod <pod-name> -n unesco-rdm
```

### ImagePullBackOff

```bash
# Verifica secret registry
kubectl get secret registry-credentials -n unesco-rdm -o yaml

# Testa manualmente
docker login registry.example.com
docker pull registry.example.com/unesco/sc-openscience:latest
```

### Database Connection Issues

```bash
# Verifica secret database
kubectl get secret unesco-rdm-secrets -n unesco-rdm -o jsonpath='{.data.SQLALCHEMY_DATABASE_URI}' | base64 -d

# Test connessione
kubectl exec -it deployment/unesco-rdm-web-ui -n unesco-rdm -- psql "$SQLALCHEMY_DATABASE_URI"
```

### Persistence Issues

```bash
# Verifica PVC
kubectl get pvc -n unesco-rdm

# Describe PVC
kubectl describe pvc <pvc-name> -n unesco-rdm

# Verifica storage class
kubectl get storageclass
```

## 📚 References

- [Helm Charts Ufficiali](https://github.com/inveniosoftware/helm-invenio)
- [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Helm Documentation](https://helm.sh/docs/)

## 🆘 Support

Per problemi:

1. Controlla i logs: `kubectl logs -f deployment/unesco-rdm-web-ui -n unesco-rdm`
2. Verifica events: `kubectl get events -n unesco-rdm`
3. Consulta [DEPLOYMENT.md](../DEPLOYMENT.md) nella root del progetto
4. Contatta il team di sviluppo

---

**Happy deploying! 🚀**
