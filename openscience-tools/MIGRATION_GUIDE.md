# Migration Guide: Docker Container → Python Package

Questa guida descrive il cambio di architettura da container Docker a package Python installabile.

## Cosa è cambiato

### Prima (Container Docker)

```bash
# Costruire il container
make tools-build

# Eseguire comandi nel container
make tools-run CMD='python -m src.tools.search -q test'

# Shell interattiva nel container
make tools-shell
```

### Ora (Package Python)

```bash
# Installare il package (solo una volta, o quando cambia il codice)
make tools-install

# Usare i comandi direttamente
make tools-search QUERY='test'
make tools-view RECORD_ID='abc-123'
make tools-cleanup OPTS='--dry-run'
make tools-import-lens FILE='data/publications.json'
```

## Vantaggi del nuovo approccio

1. **Più veloce**: Nessun overhead del container Docker
2. **Più semplice**: Comandi diretti senza wrapper Docker
3. **Migliore integrazione**: Stesso virtualenv di InvenioRDM
4. **Più flessibile**: Può essere installato ovunque come package normale

## Comandi Makefile aggiornati

### Comandi rimossi

- ❌ `tools-build` - Non più necessario (il package viene installato con pip)
- ❌ `tools-up` - Non più necessario (non c'è container da avviare)
- ❌ `tools-stop` - Non più necessario (non c'è container da fermare)
- ❌ `tools-run` - Sostituito da comandi specifici
- ❌ `tools-shell` - Non più necessario (usare direttamente il virtualenv)
- ❌ `tools-status` - Non più necessario (verifica con `openscience-tools --version`)
- ❌ `tools-delete-all` - Rinominato in `tools-cleanup`
- ❌ `tools-reset` - Da implementare se necessario

### Comandi nuovi/modificati

- ✅ `tools-install` - Installa il package nel virtualenv
- ✅ `tools-setup-env` - Genera API token e configura .env
- ✅ `tools-search` - Cerca record (prima era `tools-run CMD='...'`)
- ✅ `tools-view` - Visualizza record (nuovo)
- ✅ `tools-cleanup` - Elimina tutti i record (prima `tools-delete-all`)
- ✅ `tools-import-lens` - Import da Lens.org (modificato per usare il package)
- ✅ `tools-help` - Guida all'uso (aggiornata)

## Esempi di migrazione

### Cercare record

```bash
# Prima
make tools-run CMD='python -m src.tools.search -q "climate data" -s 10'

# Ora
make tools-search QUERY='climate data' OPTS='--size 10'
```

### Visualizzare un record

```bash
# Prima
make tools-run CMD='python -m src.tools.view abc-123'

# Ora
make tools-view RECORD_ID='abc-123'
```

### Eliminare tutti i record

```bash
# Prima
make tools-delete-all OPTS='--confirm'

# Ora
make tools-cleanup OPTS='--confirm'
```

### Import da Lens

```bash
# Prima
make tools-import-lens FILE='src/sources/lens/data/publications.json' OPTS='--limit 10'

# Ora (stesso comando, ma più veloce!)
make tools-import-lens FILE='openscience-tools/src/sources/lens/data/publications.json' OPTS='--limit 10'
```

## Uso diretto (senza Makefile)

Dopo aver eseguito `make tools-setup-env`, puoi usare il comando direttamente:

```bash
# Attivare il virtualenv
source .venv/bin/activate

# Caricare le variabili d'ambiente
export $(cat openscience-tools/config/.env | grep -v '^#' | xargs)

# Usare i comandi
openscience-tools search -q "test"
openscience-tools view abc-123
openscience-tools cleanup --dry-run
openscience-tools import-lens --file data/publications.json
```

## Configurazione

Le variabili d'ambiente rimangono le stesse e sono in `openscience-tools/config/.env`:

```env
INVENIO_BASE_URL=https://127.0.0.1:5000
INVENIO_TOKEN=<generated-token>
```

Il token viene generato automaticamente con `make tools-setup-env`.

## Troubleshooting

### "Command not found: openscience-tools"

```bash
# Assicurati che il package sia installato
make tools-install

# Verifica l'installazione
source .venv/bin/activate
openscience-tools --version
```

### "Configuration not found"

```bash
# Genera la configurazione e il token
make tools-setup-env
```

### "Error: Missing option '--base-url' / '--token'"

```bash
# Assicurati che il file .env esista e contenga le credenziali
cat openscience-tools/config/.env

# Se manca, genera la configurazione
make tools-setup-env
```

## Note per sviluppatori

### Sviluppo del package

Il package è installato in modalità "editable" (`pip install -e .`), quindi le modifiche al codice sono immediatamente disponibili senza reinstallazione.

### Debugging

```bash
# Attiva il virtualenv
source .venv/bin/activate

# Carica le variabili d'ambiente
export $(cat openscience-tools/config/.env | grep -v '^#' | xargs)

# Esegui con verbose
openscience-tools search -q "test" --verbose

# O con Python direttamente
python -m openscience_tools.cli search -q "test"
```

### Testing

```bash
# Attiva il virtualenv
source .venv/bin/activate

# Esegui i test
cd openscience-tools
pytest
```

## File rimasti (da valutare se rimuovere)

Questi file Docker non sono più utilizzati ma potrebbero essere mantenuti per reference:

- `openscience-tools/Dockerfile` - Non più usato
- `docker-compose.openscience-tools.yml` - Non più usato
- `openscience-tools/setup_env.py` - Ancora usato per generare il token

## Prossimi passi

1. ✅ Package installato e funzionante
2. ✅ Comandi Makefile aggiornati
3. ✅ Documentazione aggiornata (README.md)
4. ⏳ Valutare se rimuovere i file Docker non più usati
5. ⏳ Aggiungere tests automatici per il package
6. ⏳ Pubblicare il package su GitLab Package Registry (se necessario)
