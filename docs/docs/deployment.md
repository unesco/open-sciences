# UNESCO Open Science Portal - Production Deployment Guide

This guide covers deploying the UNESCO Open Science Portal (InvenioRDM) to production or staging environments.

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Steps](#deployment-steps)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Rollback Procedure](#rollback-procedure)
7. [Quick Reference](#quick-reference)

---

## Overview

The UNESCO Open Science Portal includes:

**CMS System:**
- Database-driven Content Management System
- Static pages management (About, Privacy, Natural Sciences Family, etc.)
- Admin interface at `/administration/cms`
- Multilingual support with fixtures

**Custom Fields & Facets:**
- `publication:year` - Publication year for faceted search
- `publication:country` - Countries from author affiliations
- `publication:funding_org` - Funding organizations
- `publication:is_open_access` - Boolean flag for open access status
- `publication:open_access_colour` - Color category (gold, green, hybrid, bronze)

**Technical Stack:**
- InvenioRDM with custom site package
- Docker Compose for container orchestration
- PostgreSQL database with Alembic migrations
- Swiper.js for carousels (loaded from CDN)

---

## Pre-Deployment Checklist

Before starting deployment, ensure you have:

- [ ] SSH access to the deployment server
- [ ] Docker and Docker Compose installed and running
- [ ] Database backup completed (see below)
- [ ] Sufficient disk space (minimum 5GB free)
- [ ] Access to environment variables and secrets

**Create Database Backup:**

```bash
# Create timestamped database backup
docker compose exec db pg_dump -U invenio invenio | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Verify backup file exists and has size > 0
ls -lh backup_*.sql.gz
```

---

## Deployment Steps

### Step 1: Pull Latest Changes

SSH into the server and pull the latest code:

```bash
# SSH into the server
ssh <server>

# Navigate to the project directory
cd /opt/unesco-science-portal  # or your DEPLOY_PATH

# Pull the latest changes
git fetch origin
git checkout dev  # or main/production depending on your branch
git pull origin dev
```

---

### Step 2: Update Configuration

⚠️ **CRITICAL NOTES:**
- The `invenio.cfg` file contains environment-specific secrets and is **NOT** tracked in Git
- The file is typically a **bind mount** from the host filesystem (e.g., `/opt/dockerapps/sc-openscience-dev/invenio.cfg` → `/opt/invenio/var/instance/invenio.cfg`)
- Always backup the **host file** before making changes
- After pulling new code, you must manually update this file on the server

#### 2.1 Backup Current Configuration

**Always backup before making changes:**

```bash
# Create timestamped backup inside the container
docker compose exec web-ui cp /opt/invenio/var/instance/invenio.cfg \
    /opt/invenio/var/instance/invenio.cfg.backup_$(date +%Y%m%d_%H%M%S)

# Verify backup was created
docker compose exec web-ui ls -la /opt/invenio/var/instance/invenio.cfg*

# Optional: Copy backup to local machine for extra safety
docker cp $(docker compose ps -q web-ui):/opt/invenio/var/instance/invenio.cfg \
    ./invenio.cfg.backup_$(date +%Y%m%d_%H%M%S)
```

💡 **Keep note of the backup filename** - you'll need it if you need to rollback!

#### 2.2 Update Configuration

Choose the appropriate method:

**Option A: Generate from Template (Fresh Deployments)**

If you have environment variables set up:

```bash
# Generate invenio.cfg from template with environment variable substitution
envsubst < invenio.cfg.template > invenio.cfg.NEW

# Review the generated file to ensure secrets were substituted correctly
grep -E "DATABASE|SECRET|PASSWORD" invenio.cfg.NEW | head -5

# Copy to container if secrets look correct
docker cp invenio.cfg.NEW $(docker compose ps -q web-ui):/opt/invenio/var/instance/invenio.cfg

# Clean up
rm invenio.cfg.NEW
```

**Option B: Manually Patch Existing Config (Existing Deployments)**

If you have a working configuration with secrets already in place:

**Step B.1:** Enter the container and edit the config:

```bash
# Enter the container
docker compose exec web-ui bash

# Edit the config file (use vim, nano, or preferred editor)
vi /opt/invenio/var/instance/invenio.cfg
```

**Step B.2:** Edit what you want to change

**Step B.3:** Save and exit (in vim: `ESC` → `:wq` → `Enter`)

**Step B.4:** Exit container and verify:

```bash
exit

# Verify configuration was updated
docker compose exec web-ui grep "cdn.jsdelivr.net" /opt/invenio/var/instance/invenio.cfg
```

---

### Step 3: Rebuild Docker Images

```bash
# Rebuild the application images
docker compose build web-ui web-api

# OR if using pre-built CI images:
docker compose pull
```

---

### Step 4: Update Database Schema

This step creates the CMS database tables if they don't exist.

```bash
# Step 4.1: Reinstall the site package
docker compose exec web-ui pip install -e /opt/invenio/src/site/

# Step 4.2: Check current migration status
docker compose exec web-ui invenio alembic current

# Step 4.3: Stamp base dependency (if needed)
docker compose exec web-ui invenio alembic stamp dbdbc1b19cf2 || true

# Step 4.4: Check if CMS tables already exist
docker compose exec web-ui invenio shell -c "
from invenio_db import db
result = db.session.execute(db.text(\"SELECT COUNT(*) FROM pg_tables WHERE tablename='cms_content'\"))
print('CMS table exists:', result.scalar() == 1)
"

# Step 4.5: Apply CMS migrations
# If CMS tables DO NOT exist (new deployment):
docker compose exec web-ui invenio alembic upgrade my_site@head

# If CMS tables ALREADY exist (update deployment):
docker compose exec web-ui invenio alembic stamp my_site@head
```

**Verify CMS tables were created:**

```bash
docker compose exec web-ui invenio shell -c "
from invenio_db import db
result = db.session.execute(db.text(\"SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'cms_%'\"))
for row in result:
    print(row[0])
"
```

**Expected output:**
```
cms_content
```

---

### Step 5: Initialize Custom Fields

⚠️ **CRITICAL STEP:** This registers new custom fields in the database.

```bash
# Initialize custom fields (required for new publication:* fields)
docker compose exec web-ui invenio rdm-records custom-fields init
```

**Expected output:**
```
Initializing custom fields...
✓ lens:id
✓ lens:open_access
✓ lens:external_ids
✓ lens:source
✓ lens:references
✓ lens:mesh_terms
✓ lens:scholarly_citations
✓ lens:chemicals
✓ publication:open_access_colour
✓ publication:is_open_access
✓ publication:year
✓ publication:country
✓ publication:funding_org
Custom fields initialized successfully.
```

---

### Step 6: Rebuild Search Indices

⚠️ **CRITICAL STEP:** New facets require updated index mappings.

```bash
# 1. Destroy existing indices (removes old mappings)
docker compose exec web-ui invenio index destroy --force --yes-i-know

# 2. Create indices with new mappings
docker compose exec web-ui invenio index init

# 3. Rebuild all record indices (re-index all records)
docker compose exec web-ui invenio rdm-records rebuild-index
```

⚠️ **Note:** Step 3 may take several minutes depending on record count. Search will be unavailable during this process.

**Verify indices:**
```bash
# List indices
docker compose exec web-ui invenio index list

# Check if records were indexed
docker compose exec web-ui invenio shell -c "from invenio_search import current_search_client; print(current_search_client.count(index='*records*'))"
```

---

### Step 7: Load CMS Content

Load default content for footer, header, and static pages:

```bash
# Load CMS fixtures (overwrites existing content)
docker compose exec web-ui invenio cms load-fixtures --force
```

**Verify fixtures were loaded:**
```bash
docker compose exec web-ui invenio shell -c "
from invenio_db import db
result = db.session.execute(db.text(\"SELECT resource_type, lang, COUNT(*) FROM cms_content GROUP BY resource_type, lang\"))
for row in result:
    print(f'{row[0]} ({row[1]}): {row[2]} entries')
"
```

**Expected output:**
```
header_frontpage (en): 1 entries
footer (en): 1 entries
static_page (en): 3 entries
```

---

### Step 8: Build Frontend Assets

```bash
# Build CSS and JavaScript assets (use invenio, not invenio-cli in containers)
docker compose exec web-ui invenio webpack buildall
docker compose exec web-ui invenio-cli assets build
```

**If assets fail to build:**

```bash
# Clean and rebuild
docker compose exec web-ui invenio webpack clean
docker compose exec web-ui invenio webpack buildall

# If you encounter memory issues (exit code -9), increase Node.js memory:
docker compose exec \
  -e NODE_OPTIONS="--max-old-space-size=3072" \
  web-ui invenio webpack buildall
```

---

### Step 9: Collect Static Files

```bash
docker compose exec web-ui invenio collect -v
```

---

### Step 10: Restart Services

```bash
# Restart all InvenioRDM services
docker compose restart web-ui web-api worker

# OR perform full restart
docker compose down
docker compose up -d
```

---

## Verification

### Check Custom Fields Configuration

```bash
# Verify custom fields are registered
docker compose exec web-ui invenio shell -c "from flask import current_app; print([f.name for f in current_app.config.get('RDM_CUSTOM_FIELDS', [])])"
```

**Expected:** Should list all custom fields including `publication:year`, `publication:country`, `publication:funding_org`, `publication:is_open_access`, `publication:open_access_colour`
   
### Check Facets in API

```bash
# Test facets/aggregations
curl -s "https://your-domain.org/api/records?size=1" | jq '.aggregations'
```

**Expected:** Should include aggregations for:
- `publication_year`
- `publication_country`
- `funding_org`
- `is_open_access`

### Check Services Health

```bash
# Check all containers are running
docker compose ps

# Check logs for errors
docker compose logs --tail=50 web-ui
docker compose logs --tail=50 web-api
docker compose logs --tail=50 worker
```

### Verify Frontend Changes

Open in browser and verify:

1. **Homepage:** `https://your-domain.org/`
   - UNESCO-styled page with carousels
   - Highlight cards carousel works (Swiper.js)
   - Research cards carousel works

2. **Search Page:** `https://your-domain.org/search`
   - Custom facets displayed in left sidebar
   - Open Access toggle works
   - Facets: Resource Type, Year, Country, Funding Organization

3. **Record Detail:** Click on any record
   - Collapsible metadata panels display
   - UNESCO styling applied

### Verify Static Pages

```bash
# Test About page
curl -s "https://your-domain.org/pages/about" | grep -i "unesco" | head -5

# Test Privacy page
curl -s "https://your-domain.org/pages/privacy" | grep -i "privacy" | head -5
```

---

## Troubleshooting Guide

### Issue: Swiper.js Carousel Not Working

**Symptoms:** Carousels not sliding, console shows CSP errors

**Solution:** Verify CSP headers include `https://cdn.jsdelivr.net`

```bash
docker compose exec web-ui grep -A 20 "content_security_policy" /opt/invenio/var/instance/invenio.cfg
```

### Issue: CMS Migration Fails

**Symptoms:** `alembic upgrade` fails with "relation already exists" or "branch not found"

**Solution:**

```bash
# Check current state
docker compose exec web-ui invenio alembic current

# If my_site branch doesn't exist, create it
docker compose exec web-ui invenio alembic stamp --purge my_site@head

# If tables already exist but migration thinks they don't
docker compose exec web-ui invenio alembic stamp my_site@head
```

### Issue: Static Pages Return 404

**Symptoms:** `/pages/about` returns 404

**Solution:** Check if fixtures were loaded

```bash
# Check loaded pages
docker compose exec web-ui invenio shell -c "
from my_site.models.cms import CMSContent
from invenio_db import db
pages = db.session.query(CMSContent).filter_by(resource_type='static_page').all()
for p in pages:
    print(f'{p.slug}: {p.title}')
"

# If empty, reload fixtures
docker compose exec web-ui invenio cms load-fixtures --force
```

### Issue: Assets Not Loading (404 on CSS/JS)

**Symptoms:** Page loads but looks unstyled

**Solution:** Rebuild and collect assets

```bash
# Rebuild and collect assets
docker compose exec web-ui invenio webpack clean
docker compose exec web-ui invenio webpack buildall
docker compose exec web-ui invenio collect -v

# Restart nginx if used
docker compose restart nginx
```

### Issue: Database Connection Errors

**Symptoms:** Application fails to start, database connection refused

**Solution:**

```bash
# Check PostgreSQL is running
docker compose ps db

# Check database logs
docker compose logs db

# Restart database
docker compose restart db

# Wait for database to be ready
docker compose exec web-ui invenio db init
```

---

## Rollback Procedure

If something goes wrong during deployment:

### Rollback Configuration

```bash
# Restore previous configuration (use your backup timestamp)
docker compose exec web-ui cp \
    /opt/invenio/var/instance/invenio.cfg.backup_YYYYMMDD_HHMMSS \
    /opt/invenio/var/instance/invenio.cfg
```

### Rollback Code

```bash
# Revert to previous git commit
git log --oneline -10  # Find the previous commit hash
git checkout <previous-commit-hash>

# Rebuild images
docker compose build web-ui web-api

# Restart services
docker compose restart web-ui web-api worker
```

### Rollback Database Migration

```bash
# Rollback last migration
docker compose exec web-ui invenio alembic downgrade my_site@-1

# Rollback to specific revision
docker compose exec web-ui invenio alembic downgrade <revision-id>
```

### Restore Database from Backup

```bash
# Stop services
docker compose down

# Restore database
gunzip < backup_YYYYMMDD_HHMMSS.sql.gz | docker compose exec -T db psql -U invenio invenio

# Start services
docker compose up -d
```

---

## Quick Reference

### Complete Deployment Sequence

Copy-paste friendly command sequence for standard deployment:

```bash
# Navigate to project
cd /opt/unesco-science-portal

# Pull latest code
git pull origin dev

# Backup configuration
docker compose exec web-ui cp /opt/invenio/var/instance/invenio.cfg \
    /opt/invenio/var/instance/invenio.cfg.backup_$(date +%Y%m%d_%H%M%S)

# Update configuration (if needed)
# ... manually edit or use envsubst ...

# Rebuild images
docker compose build web-ui web-api

# Update site package and database
docker compose exec web-ui pip install -e /opt/invenio/src/site/
docker compose exec web-ui invenio alembic upgrade my_site@head

# Initialize custom fields (CRITICAL!)
docker compose exec web-ui invenio rdm-records custom-fields init

# Rebuild search indices (CRITICAL!)
docker compose exec web-ui invenio index destroy --force --yes-i-know
docker compose exec web-ui invenio index init
docker compose exec web-ui invenio rdm-records rebuild-index

# Load CMS content
docker compose exec web-ui invenio cms load-fixtures --force

# Build assets
docker compose exec web-ui invenio webpack buildall
docker compose exec web-ui invenio collect -v

# Restart services
docker compose restart web-ui web-api worker

# Verify deployment
docker compose ps
docker compose logs --tail=20 web-ui
```

### Useful Commands

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f web-ui
docker compose logs -f worker

# Enter web container
docker compose exec web-ui bash

# Run Invenio commands
docker compose exec web-ui invenio <command>

# Database shell
docker compose exec web-ui invenio shell

# Check migration status
docker compose exec web-ui invenio alembic current
docker compose exec web-ui invenio alembic history

# Rebuild assets
docker compose exec web-ui invenio webpack clean
docker compose exec web-ui invenio webpack buildall
docker compose exec web-ui invenio collect -v
```

---
