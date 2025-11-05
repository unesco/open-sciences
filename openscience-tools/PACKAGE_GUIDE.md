# OpenScience Tools - Guida Completa

## ✅ Trasformazione Completata

Il progetto `openscience-tools` è stato trasformato con successo da container Docker a **package Python installabile**.

## 📦 Struttura del Package

```
openscience-tools/
├── pyproject.toml          # Configurazione moderna del package (PEP 621)
├── setup.py                 # Backward compatibility
├── MANIFEST.in              # File da includere nella distribuzione
├── LICENSE                  # MIT License
├── README.md                # Documentazione principale
├── INSTALL.md               # Guida all'installazione
├── requirements.txt         # Dipendenze
├── .gitlab-ci.yml          # CI/CD per GitLab
├── .gitignore              # Ignora build artifacts
├── src/                    # Codice sorgente (package openscience_tools)
│   ├── __init__.py
│   ├── cli.py              # CLI principale
│   ├── invenio_client.py
│   ├── tools/
│   └── sources/
└── dist/                   # Package builds
    ├── openscience_tools-0.1.0.tar.gz
    └── openscience_tools-0.1.0-py3-none-any.whl
```

## 🚀 Installazione e Test Locale

### 1. Build del Package

```bash
cd openscience-tools

# Installa tool di build
pip install --upgrade build

# Builda il package (crea wheel e source distribution)
python -m build
```

### 2. Test in Virtualenv

```bash
# Crea virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Installa in modalità editable (sviluppo)
pip install -e .

# Verifica installazione
python -c "from openscience_tools import __version__; print(f'✅ v{__version__}')"

# Testa CLI
openscience-tools --version
```

### 3. Test Comandi CLI

```bash
# Help generale
openscience-tools --help

# Comandi specifici
openscience-tools search --help
openscience-tools view --help
openscience-tools stats --help
openscience-tools cleanup --help

# Oppure comandi diretti
ost-search --help
ost-view --help
ost-stats --help
```

## 📤 Pubblicazione su GitLab Package Registry

### Manuale (Prima Volta)

```bash
# Installa twine
pip install twine

# Build del package
python -m build

# Upload a GitLab Package Registry
TWINE_PASSWORD=<YOUR_GITLAB_TOKEN> TWINE_USERNAME=<YOUR_USERNAME> \
python -m twine upload \
  --repository-url https://repository.unesco.org/api/v4/projects/<PROJECT_ID>/packages/pypi \
  dist/*
```

### Automatico (GitLab CI/CD)

Il file `.gitlab-ci.yml` è già configurato con 3 stage:

1. **test**: Esegue tests e linting
2. **build**: Crea i package
3. **publish**: Pubblica su GitLab Package Registry (manuale o su tag)

#### Trigger Manuale

```bash
# Commit e push
git add openscience-tools/
git commit -m "feat: transform to Python package"
git push origin UNESC-10

# Vai su GitLab → CI/CD → Pipelines
# Clicca sul job "publish" per pubblicarlo manualmente
```

#### Publish Automatico con Tag

```bash
# Crea un tag release
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Il job "publish:release" partirà automaticamente
```

## 📥 Installazione da GitLab Package Registry

Una volta pubblicato:

```bash
# Installazione con token GitLab
pip install openscience-tools \
  --index-url https://<token-name>:<token>@repository.unesco.org/api/v4/projects/<PROJECT_ID>/packages/pypi/simple

# In requirements.txt
--index-url https://repository.unesco.org/api/v4/projects/<PROJECT_ID>/packages/pypi/simple
openscience-tools>=0.1.0
```

## 🔧 Configurare Token GitLab

### 1. Creare Personal Access Token

1. GitLab → Settings → Access Tokens
2. Nome: `openscience-tools-registry`
3. Scopes: `api`, `read_api`, `write_repository`
4. Crea token e salvalo

### 2. Configurare pip

```bash
# In ~/.pip/pip.conf (Linux/macOS) o %APPDATA%\pip\pip.ini (Windows)
[global]
index-url = https://<token-name>:<token>@repository.unesco.org/api/v4/projects/<PROJECT_ID>/packages/pypi/simple
```

## 🔄 Workflow di Sviluppo

### Sviluppo Locale

```bash
cd openscience-tools

# Attiva virtualenv
source .venv/bin/activate

# Installa in modalità editable
pip install -e ".[dev]"

# Sviluppa e testa
python -m openscience_tools.tools.search -q "test"

# Oppure usa i comandi CLI
openscience-tools search -q "test"
```

### Aggiornare Versione

```python
# In pyproject.toml e src/__init__.py
version = "0.2.0"
```

```bash
# Build e publish
python -m build
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

## 📚 Uso del Package

### Python API

```python
from openscience_tools import InvenioRDMClient

client = InvenioRDMClient(
    base_url="https://127.0.0.1:5000",
    token="your-token"
)

# Search
results = client.search_records(q="climate", size=10)

# Get record
record = client.get_record("abc-123")

# Create draft
draft = client.create_draft(metadata)
client.publish_draft(draft["id"])
```

### CLI

```bash
# Search
ost-search -q "machine learning" -s 10 --detailed

# View record
ost-view abc-123 --format json

# Import from sources
ost-import-lens data/publications.json --limit 10
ost-import-csv data/records.csv
ost-import-zenodo --record-id 17462748

# Statistics
ost-stats --record-id abc-123

# Cleanup
ost-cleanup --dry-run
```

## 🎯 Vantaggi della Trasformazione

### Prima (Docker)

❌ Dipendenza da Docker  
❌ Overhead di container  
❌ Difficile da integrare in altri progetti  
❌ No versionamento package

### Dopo (Python Package)

✅ Installabile con `pip install`  
✅ Riutilizzabile in qualsiasi progetto Python  
✅ Versionamento semantico  
✅ Pubblicato su GitLab Package Registry  
✅ CI/CD automatico  
✅ Comandi CLI globali

## 🐛 Troubleshooting

### Import Errors

```bash
# Reinstalla package
pip install --force-reinstall -e .
```

### CLI Commands Not Found

```bash
# Verifica che il virtualenv sia attivo
which python
which openscience-tools

# Reinstalla
pip install -e .
```

### Build Errors

```bash
# Pulisci build artifacts
rm -rf dist/ build/ *.egg-info

# Rebuild
python -m build
```

## 📖 Documentazione

- [README.md](README.md) - Documentazione completa
- [INSTALL.md](INSTALL.md) - Guida dettagliata all'installazione
- [pyproject.toml](pyproject.toml) - Configurazione package

## 🤝 Contribuire

1. Fork il repository
2. Crea feature branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Apri Pull Request

## 📄 License

MIT License - Vedi [LICENSE](LICENSE)

## 📞 Support

- Issues: https://repository.unesco.org/gitlab/sc/sc-openscience/-/issues
- Email: info@unesco-science-portal.org
