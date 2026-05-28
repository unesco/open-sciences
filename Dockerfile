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

# Declare proxy build arguments
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG http_proxy
ARG https_proxy
ARG no_proxy

# Set proxy environment variables for pip/pipenv
ENV HTTP_PROXY=${HTTP_PROXY} \
    HTTPS_PROXY=${HTTPS_PROXY} \
    NO_PROXY=${NO_PROXY} \
    http_proxy=${http_proxy} \
    https_proxy=${https_proxy} \
    no_proxy=${no_proxy}

# Install Python 3.12 and update alternatives
RUN dnf install -y python3.12 python3.12-pip python3.12-devel && \
    alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    alternatives --set python3 /usr/bin/python3.12 && \
    python3 -m pip install --upgrade pip pipenv

COPY site ./site
COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
# Copy environment-specific invenio.cfg (generated from invenio.cfg.template by 'make render-config')
# This file contains all S3, database, and app configuration for the target environment
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}/invenio.cfg
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations/ ${INVENIO_INSTANCE_PATH}/translations/
COPY ./ .

RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose  && \
    invenio webpack buildall

ENTRYPOINT [ "bash", "-c"]
