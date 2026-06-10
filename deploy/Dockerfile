# Dockerfile.k8s - Optimized for Kind deployment
#
# This Dockerfile is specifically designed for Kubernetes/Kind deployment.
# It builds a production-ready image with all assets pre-compiled.
#
# Based on InvenioRDM official base image with Python, Node.js, and NPM pre-installed.

FROM registry.cern.ch/inveniosoftware/almalinux:1

# Build arguments
ARG PIPENV_INSTALL_DEV=false

# Labels for image metadata
LABEL maintainer="UNESCO Science Portal Team"
LABEL description="InvenioRDM instance for UNESCO Science Portal - Kubernetes/Kind deployment"
LABEL org.opencontainers.image.source="https://github.com/inveniosoftware/sc-openscience"
LABEL version="1.0.0"

# Environment variables for production
ENV INVENIO_INSTANCE_PATH=/opt/invenio/var/instance
ENV INVENIO_STATIC_URL=/static

# Install Python 3.12 and update alternatives
RUN dnf install -y python3.12 python3.12-pip python3.12-devel && \
    alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    alternatives --set python3 /usr/bin/python3.12 && \
    python3 -m pip install --upgrade pip pipenv

# Set working directory
WORKDIR /opt/invenio/src

# Copy site package first (required by Pipfile)
COPY ../site ./site

# Copy Python dependencies
COPY ../Pipfile ../Pipfile.lock ./

# Install Python dependencies (including ./site via Pipfile)
RUN echo "🔍 Python version: $(python --version)" && \
    echo "📦 Installing dependencies with pipenv..." && \
    pip install --upgrade pip "setuptools<82" wheel pipenv && \
    if [ "$PIPENV_INSTALL_DEV" = "true" ]; then \
        echo "📦 Installing all dependencies (including dev)..."; \
        pipenv install --deploy --system --dev; \
    else \
        echo "📦 Installing production dependencies only..."; \
        pipenv install --deploy --system; \
    fi && \
    echo "✅ Dependencies installed successfully"

# Copy application code
COPY ../ ./

# Copy configuration files to instance path
# Note: invenio.cfg will be mounted as Secret from k8s at runtime
COPY ../docker/uwsgi/ ${INVENIO_INSTANCE_PATH}/
COPY ../templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ../app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ../translations/ ${INVENIO_INSTANCE_PATH}/translations/

# Copy static assets and templates
RUN echo "📦 Copying static assets and templates..." && \
    mkdir -p ${INVENIO_INSTANCE_PATH}/assets/templates \
             ${INVENIO_INSTANCE_PATH}/assets/less \
             ${INVENIO_INSTANCE_PATH}/assets/js && \
    if [ -d ./assets/templates ]; then cp -rv ./assets/templates ${INVENIO_INSTANCE_PATH}/assets/; fi && \
    if [ -d ./assets/less ]; then cp -rv ./assets/less ${INVENIO_INSTANCE_PATH}/assets/; fi && \
    if [ -d ./assets/js ]; then cp -rv ./assets/js ${INVENIO_INSTANCE_PATH}/assets/; fi && \
    if [ -d ./static ]; then cp -rv ./static/. ${INVENIO_INSTANCE_PATH}/static/; fi && \
    echo "✅ Assets copied"

# Make npm resilient to the flaky UNESCO proxy: more retries and longer
# timeouts so a single slow tarball doesn't fail the whole webpack build.
ENV NPM_CONFIG_FETCH_RETRIES=5 \
    NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000 \
    NPM_CONFIG_FETCH_TIMEOUT=600000

# Build webpack assets (pre-compile for production)
RUN echo "🔨 Building webpack assets..." && \
    invenio webpack buildall && \
    invenio collect -v && \
    echo "✅ Webpack assets built and collected"

# Create directories for runtime data
RUN mkdir -p ${INVENIO_INSTANCE_PATH}/data \
             ${INVENIO_INSTANCE_PATH}/archive \
             ${INVENIO_INSTANCE_PATH}/logs && \
    chmod -R 755 ${INVENIO_INSTANCE_PATH}

# Health check for Kubernetes probes
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ping || exit 1

# Default command (can be overridden by Kubernetes)
ENTRYPOINT [ "bash", "-c"]
