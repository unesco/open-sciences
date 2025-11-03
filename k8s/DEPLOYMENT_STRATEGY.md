# Strategia: Helm Chart con Servizi Esterni

## Problema Identificato

Il Helm chart ufficiale di InvenioRDM dipende da 4 subchart Bitnami:

- `opensearch:1.4.0`
- `postgresql:14.3.3`
- `rabbitmq:12.9.3`
- `redis:18.12.0`

Questi subchart richiedono immagini dal registro `registry-1.docker.io/bitnamicharts` che **non è più pubblicamente accessibile** (spostato a Broadcom con autenticazione richiesta).

## Soluzione: Servizi Esterni

Il chart supporta **nativamente** la configurazione di servizi esterni tramite le sezioni `*External` nei values:

### Pattern del Chart

Ogni servizio ha una condizione nel `Chart.yaml`:

```yaml
dependencies:
  - name: redis
    condition: redis.enabled # ← Se false, usa redisExternal
```

E nei template (`_helpers.tpl`), il chart decide quale configurazione usare:

```go
{{- if .Values.redis.enabled }}
  {{- /* usa subchart Bitnami */ -}}
{{- else }}
  {{- required "Missing .Values.redisExternal.hostname" .Values.redisExternal.hostname }}
{{- end }}
```

### Servizi Esterni Supportati

1. **Redis**: `redisExternal.hostname`
2. **PostgreSQL**: `postgresqlExternal.{hostname,port,username,password,database}`
3. **RabbitMQ**: `rabbitmqExternal.{hostname,username,password,amqpPort,managementPort,protocol,vhost}`
4. **OpenSearch**: `opensearchExternal.hostname`

## Implementazione

### File 1: `k8s/external-services.yaml`

Deploy dei servizi con **immagini pubbliche ufficiali**:

- **Redis**: `redis:7-alpine` (ufficiale Docker Hub)
- **PostgreSQL**: `postgres:15` (ufficiale Docker Hub)
- **RabbitMQ**: `rabbitmq:3-management-alpine` (ufficiale Docker Hub)
- **OpenSearch**: `opensearchproject/opensearch:2.11.1` (ufficiale OpenSearch Project)

Tutti i servizi sono configurati per Kind (single replica, emptyDir volumes).

### File 2: `k8s/values-unesco.yaml`

Configurazione Helm che:

1. **Disabilita** tutti i subchart Bitnami:

   ```yaml
   redis:
     enabled: false
   postgresql:
     enabled: false
   rabbitmq:
     enabled: false
   opensearch:
     enabled: false
   ```

2. **Configura** i servizi esterni:

   ```yaml
   redisExternal:
     hostname: "redis"

   postgresqlExternal:
     hostname: "postgresql"
     port: 5432
     username: "unesco_rdm"
     password: "unesco_rdm_password"
     database: "unesco_rdm"

   rabbitmqExternal:
     hostname: "rabbitmq"
     username: "guest"
     password: "guest"
     amqpPort: 5672
     managementPort: 15672
     protocol: "amqp"
     vhost: ""

   opensearchExternal:
     hostname: "opensearch"
   ```

3. Usa l'immagine custom:
   ```yaml
   image:
     registry: "docker.io"
     repository: sc-openscience
     tag: latest
     pullPolicy: Never # Immagine già caricata in Kind
   ```

## Deployment

### Step 1: Creare Kind Cluster

```bash
kind create cluster
```

### Step 2: Caricare Immagine Custom

```bash
kind load docker-image sc-openscience:latest
```

### Step 3: Deployare Servizi Esterni

```bash
kubectl apply -f k8s/external-services.yaml
```

Questo crea:

- Namespace `unesco-rdm`
- 4 Deployments (redis, postgresql, rabbitmq, opensearch)
- 4 Services per l'accesso interno

### Step 4: Aspettare che i Servizi Siano Ready

```bash
kubectl wait --for=condition=ready pod -l app=redis -n unesco-rdm --timeout=120s
kubectl wait --for=condition=ready pod -l app=postgresql -n unesco-rdm --timeout=120s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n unesco-rdm --timeout=120s
kubectl wait --for=condition=ready pod -l app=opensearch -n unesco-rdm --timeout=180s
```

### Step 5: Installare InvenioRDM con Helm

```bash
cd k8s/helm-invenio-master/charts/invenio
helm install unesco-rdm . \
  --namespace unesco-rdm \
  --values /Users/francescosasso/Documents/ICC/repositories/sc-openscience/k8s/values-unesco.yaml
```

## Vantaggi di Questa Strategia

1. ✅ **Nessuna dipendenza da Bitnami**: usa solo immagini pubbliche ufficiali
2. ✅ **Supporto nativo del chart**: usa le feature `*External` già presenti
3. ✅ **Nessuna modifica al chart**: il chart ufficiale rimane intatto
4. ✅ **Flessibilità**: possiamo aggiornare i servizi indipendentemente
5. ✅ **Semplicità**: deployment in 2 step (servizi + app)

## Svantaggi e Limitazioni

1. ⚠️ **Due deployment separati**: servizi e app non in un unico Helm release
2. ⚠️ **Configurazione password in plaintext**: per dev va bene, in prod usare secrets
3. ⚠️ **EmptyDir volumes**: dati persi al restart (ok per Kind, non per prod)

## Alternative Considerate

### Opzione B: Modificare Chart.yaml

Sostituire le dipendenze Bitnami con chart pubblici o creare subchart custom.

- **Pro**: deployment unificato
- **Contro**: richiede manutenzione del chart, più complesso

### Opzione C: Subchart Custom

Creare subchart custom con immagini pubbliche.

- **Pro**: deployment unificato, configurazione consistente
- **Contro**: molto lavoro, duplicazione del codice Bitnami

## Prossimi Passi

1. Creare Kind cluster
2. Testare deployment servizi esterni
3. Testare deployment Helm con values-unesco.yaml
4. Verificare che i Celery workers funzionino correttamente
5. Caricare vocabularies: `invenio rdm-records fixtures`
6. Importare dati: `make kind-scripts-import-lens`

## Note di Produzione

Per un deployment di produzione, considerare:

1. **Secrets Management**: usare Kubernetes Secrets o vault esterni
2. **Persistent Storage**: PVC con storage class appropriato
3. **High Availability**: replica > 1 per i servizi critici
4. **Monitoring**: Prometheus, Grafana, AlertManager
5. **Backup**: backup automatici dei database e files
6. **Resource Limits**: ottimizzare in base al carico reale
7. **Security**: network policies, RBAC, TLS
