# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on Almalinux (https://github.com/inveniosoftware/docker-invenio)
# and includes Pip, Pipenv, Node.js, NPM and some few standard libraries
# Invenio usually needs.
#
# Note: It is important to keep the commands in this file in sync with your
# bootstrap script located in ./scripts/bootstrap.

FROM registry.cern.ch/inveniosoftware/almalinux:1

# Build arguments
ARG PIPENV_INSTALL_DEV=false

# Labels for image metadata
LABEL maintainer="UNESCO Science Portal Team"
LABEL description="InvenioRDM instance for UNESCO Science Portal"
LABEL org.opencontainers.image.source="https://github.com/your-org/sc-openscience"

# Install Python dependencies
COPY site ./site
COPY Pipfile Pipfile.lock ./

# Install dependencies (skip dev dependencies in production)
RUN echo "🔍 Python version: $(python --version)" && \
    echo "📦 Installing dependencies with pipenv..." && \
    pip install --upgrade pip setuptools wheel pipenv && \
    if [ "$PIPENV_INSTALL_DEV" = "true" ]; then \
        echo "📦 Installing all dependencies (including dev)..."; \
        pipenv install --deploy --system --dev --skip-lock; \
    else \
        echo "📦 Installing production dependencies only..."; \
        pipenv install --deploy --system --skip-lock; \
    fi && \
    echo "✅ Dependencies installed successfully" && \
    python -c "import click; print('✅ Click module available')"

# Copy configuration and templates
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations/ ${INVENIO_INSTANCE_PATH}/translations/

# Copy application code
COPY ./ .

# Copy static assets and templates directly to instance path
# This must happen AFTER copying application code to ensure correct paths
RUN echo "📦 Copying static assets and templates to instance path..." && \
    mkdir -p ${INVENIO_INSTANCE_PATH}/assets/templates ${INVENIO_INSTANCE_PATH}/assets/less && \
    if [ -d ./assets/templates ]; then cp -rv ./assets/templates ${INVENIO_INSTANCE_PATH}/assets/; fi && \
    if [ -d ./assets/less ]; then cp -rv ./assets/less ${INVENIO_INSTANCE_PATH}/assets/; fi && \
    if [ -d ./assets/js ]; then cp -rv ./assets/js ${INVENIO_INSTANCE_PATH}/assets/; fi && \
    if [ -d ./static ]; then cp -rv ./static/. ${INVENIO_INSTANCE_PATH}/static/; fi && \
    echo "📋 Listing what was copied:" && \
    ls -la ${INVENIO_INSTANCE_PATH}/assets/ && \
    echo "✅ Assets copied. Webpack build will happen at container startup."

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ping || exit 1

ENTRYPOINT [ "bash", "-c"]
