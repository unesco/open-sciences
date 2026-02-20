#!/bin/bash
set -e

echo "======================================================================="
echo "InvenioRDM Docker Entrypoint"
echo "======================================================================="
echo ""

INVENIO_INSTANCE_PATH="${INVENIO_INSTANCE_PATH:-/opt/invenio/var/instance}"
TEMPLATE_FILE="/opt/invenio/src/invenio.cfg.template"
CONFIG_FILE="${INVENIO_INSTANCE_PATH}/invenio.cfg"

echo "Configuration:"
echo "  Template: ${TEMPLATE_FILE}"
echo "  Output: ${CONFIG_FILE}"
echo ""

# Check if template exists
if [ ! -f "${TEMPLATE_FILE}" ]; then
    echo "ERROR: Template file not found: ${TEMPLATE_FILE}"
    exit 1
fi

# Verify required environment variables
REQUIRED_VARS=(
    "ADMIN_EMAIL"
    "DOMAIN"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
    "S3_ACCESS_KEY_ID"
    "S3_SECRET_ACCESS_KEY"
    "S3_ENDPOINT_URL"
    "SECRET_KEY"
)

echo "Checking required environment variables..."
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo ""
    echo "ERROR: Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please ensure all required variables are set in Kubernetes/k3s deployment."
    exit 1
fi

echo "All required variables present ✓"
echo ""

# Export derived variables (same logic as Makefile and CI pipeline)
export SITE_UI_URL="${SITE_PROTOCOL:-https}://${DOMAIN}"
export SITE_API_URL="${SITE_PROTOCOL:-https}://${DOMAIN}/api"
export APP_RDM_ADMIN_EMAIL_RECIPIENT="${APP_RDM_ADMIN_EMAIL_RECIPIENT:-${ADMIN_EMAIL}}"
export SQLALCHEMY_DATABASE_URI="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgresql:5432/${POSTGRES_DB}"

echo "Derived variables:"
echo "  SITE_UI_URL = ${SITE_UI_URL}"
echo "  SITE_API_URL = ${SITE_API_URL}"
echo "  APP_RDM_ADMIN_EMAIL_RECIPIENT = ${APP_RDM_ADMIN_EMAIL_RECIPIENT}"
echo "  SQLALCHEMY_DATABASE_URI = postgresql://${POSTGRES_USER}:****@postgresql:5432/${POSTGRES_DB}"
echo ""

# Generate invenio.cfg from template
echo "Generating ${CONFIG_FILE} from template..."
envsubst < "${TEMPLATE_FILE}" > "${CONFIG_FILE}"

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "ERROR: Failed to generate configuration file"
    exit 1
fi

echo "Configuration file generated successfully ✓"
echo "  Size: $(wc -c < ${CONFIG_FILE}) bytes"
echo "  Lines: $(wc -l < ${CONFIG_FILE})"
echo ""
echo "======================================================================="
echo "Starting InvenioRDM..."
echo "======================================================================="
echo ""

# Execute the command passed to docker run
exec "$@"
