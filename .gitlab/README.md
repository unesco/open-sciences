# GitLab CI/CD Setup for openscience_tools

## Overview

This directory contains the GitLab CI/CD configuration for building and publishing the `openscience_tools` package to the GitLab Package Registry.

## Pipeline Stages

The pipeline consists of 4 stages:

1. **prepare** - Builds a custom Docker image with twine pre-installed
2. **test** - Runs tests and linting (manual, optional)
3. **build** - Creates distribution packages (.whl and .tar.gz)
4. **publish** - Uploads packages to GitLab Package Registry (manual)

## Custom Docker Image

### Why a custom image?

The GitLab runner in this environment experiences persistent network connectivity issues when trying to install packages from PyPI. This manifests as `Connection reset by peer` errors when running `pip install`.

**Root Cause**: The runner is behind the UNESCO proxy (`http://proxy.unesco.org:8080`), which requires proper proxy configuration for external internet access.

To work around this, we use a custom Docker image (`Dockerfile.publish`) that has `twine` pre-installed. This image is built once (with proper proxy configuration) and then reused for all publish jobs.

### Proxy Configuration

The pipeline uses the UNESCO proxy for all external internet access:

- **HTTP/HTTPS Proxy**: `http://proxy.unesco.org:8080`
- **No Proxy (internal domains)**: `localhost,127.0.0.1,docker,*.unesco.org,unesco.org,repository.unesco.org,registry.gitlab.com`

These settings are configured in:

1. The `build-publish-image` job (Docker build arguments)
2. The `Dockerfile.publish` (build-time ARGs and ENV variables)
3. The `build` job (runtime environment variables)

### Building the publish image

The `build-publish-image` job is **manual** and only needs to be run when:

- The Dockerfile.publish is modified
- You need to update the twine version
- The image is not available in the registry

To build the image:

1. Go to your GitLab project's CI/CD Pipelines
2. Click "Run pipeline"
3. Manually trigger the `build-publish-image` job

The image will be pushed to: `${CI_REGISTRY_IMAGE}/publish-tool:latest`

## Usage

### Building the package

The `build` stage runs automatically on every push to branches and tags. It:

- Uses pre-installed Python build tools (no network required)
- Fallback to `setup.py` if `python -m build` is not available
- Creates artifacts in `openscience_tools/dist/`
- Artifacts expire after 1 week

### Publishing to GitLab Package Registry

The `publish` stage is **manual only**. To publish:

1. Go to your GitLab project's CI/CD Pipelines
2. Find a successful pipeline with build artifacts
3. Click the play button ▶️ on the `publish` job
4. Wait for the job to complete

The package will be uploaded to: `${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/pypi`

### Installing the published package

Once published, users can install with:

```bash
pip install openscience_tools --index-url https://gitlab.com/api/v4/projects/${CI_PROJECT_ID}/packages/pypi/simple
```

Or add to `pip.conf` / `~/.pip/pip.conf`:

```ini
[global]
index-url = https://gitlab.com/api/v4/projects/${CI_PROJECT_ID}/packages/pypi/simple
```

## Files

- `Dockerfile.publish` - Custom Docker image with twine pre-installed
- `../.gitlab-ci.yml` - Main CI/CD pipeline configuration (in project root)

## Troubleshooting

### Publish job fails with "image not found"

The custom publish image hasn't been built yet. Run the `build-publish-image` job first.

### Build job fails

The build job uses only pre-installed tools and shouldn't require network access. If it fails:

- Check that `openscience_tools/setup.py` is present
- Verify the package structure is correct
- The proxy variables are set for compatibility but shouldn't be needed for `--no-isolation` builds

### Network errors during image build

The `build-publish-image` job requires network access to install twine. If it fails with "Connection reset by peer":

- **Check proxy configuration**: Ensure the UNESCO proxy settings are correct in `.gitlab-ci.yml`
- Retry the job (network issues may be temporary)
- Verify the proxy is accessible: `http://proxy.unesco.org:8080`
- Check if PyPI is accessible through the proxy

The `build-publish-image` job requires network access to install twine. If it fails:

- Retry the job (network issues may be temporary)
- Check if PyPI is accessible from the runner

## Notes

- The publish job uses `CI_JOB_TOKEN` for authentication (no manual token setup required)
- All manual jobs prevent accidental publishing
- Build artifacts are automatically passed to the publish stage
- The test stage is optional and allows failures (due to network issues installing dev dependencies)
