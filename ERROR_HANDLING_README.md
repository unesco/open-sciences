# Error Handling Documentation

Complete guide to custom error handling in the InvenioRDM UNESCO Science Portal.

## 📚 Table of Contents

- [What's Implemented](#-whats-implemented)
- [Error Codes Reference](#-error-codes-reference)  
- [Error Response Examples](#-error-response-examples)
- [Quick Start](#-quick-start)
- [Where the Code Lives](#-where-the-code-lives)
- [Testing](#-testing)
- [What Changed](#-what-changed)
- [Developer Guide](#-developer-guide)
- [Technical Implementation](#-technical-implementation)
- [Troubleshooting](#-troubleshooting)
- [Additional Resources](#-additional-resources)
- [Change Log](#-change-log)

## ✅ What's Implemented

Your InvenioRDM instance now handles **multiple types of errors** with custom HTTP status codes:

### 1. **Timeout Errors** → HTTP 524 (Publications) / 504 (External)
- Publication operations that take too long
- External service (Lens.org) timeouts

### 2. **Large Payload Errors** → HTTP 413 / 502
- Response exceeds 50MB limit → **413 Payload Too Large**
- Connection drops while reading large response → **502 Bad Gateway**

### 3. **JSON Parsing Errors** → HTTP 502
- "Expecting value: line 1 column 1 (char 0)" → **502 Bad Gateway**
- Incomplete/truncated responses
- Chunked encoding errors

## 🎯 Error Codes Reference

| HTTP Code | Error Type | What Triggers It | Category |
|-----------|------------|------------------|----------|
| **408** | Request Timeout | Generic operation timeout | Client Error |
| **413** | Payload Too Large | Response > 50MB | Client Error |
| **502** | Bad Gateway | JSON parse error, incomplete response | Server Error |
| **504** | Gateway Timeout | Standard external service timeout | Server Error |
| **524** | Origin Timeout | Publication-specific timeout | Server Error (Cloudflare-style) |

## 📋 Error Response Examples

### When Response is Too Large
```json
{
  "error": "Response payload too large",
  "error_type": "payload_too_large",
  "status": 413,
  "size_mb": 52.3,
  "suggestion": "Try reducing the size parameter or use pagination"
}
```

### When JSON Parsing Fails
```json
{
  "error": "Failed to parse JSON response",
  "error_type": "json_decode_error",
  "status": 502,
  "details": "Expecting value: line 1 column 1 (char 0)",
  "suggestion": "The response data is incomplete or malformed. This often happens with very large responses. Try reducing the request size or using pagination."
}
```

### When Connection Drops Mid-Response
```json
{
  "error": "Incomplete response from Lens.org",
  "error_type": "chunked_encoding_error",
  "status": 502,
  "details": "Connection broken: Invalid chunk encoding",
  "suggestion": "The response was truncated. Try reducing the size parameter."
}
```

### When Publication Times Out
```json
{
  "error": "Publication operation timed out",
  "error_type": "publication_timeout",
  "status": 524,
  "suggestion": "The publication service is taking longer than expected. Please try again or reduce the request size."
}
```

## 🚀 Quick Start

Simply restart your server to activate all error handlers:

```bash
make stop
make up
```

**That's it!** All error handlers are automatically registered on startup.

All your existing `make` commands work automatically with error handling:

```bash
make up                 # Starts with error handlers
make tools-import-lens  # Uses error handlers
make tools-reset        # Uses error handlers
```

## 📍 Where the Code Lives

1. **Error Handlers**: [site/my_site/error_handlers.py](site/my_site/error_handlers.py)
   - Custom exception classes
   - Flask error handlers
   - Automatic error response formatting

2. **Lens.org Proxy**: [site/my_site/api/lens_proxy.py](site/my_site/api/lens_proxy.py)
   - Streams large responses
   - Checks payload size (50MB limit)
   - Catches JSON parsing errors
   - Handles chunked encoding errors

3. **Configuration**: [invenio.cfg](invenio.cfg)
   - Timeout values
   - HTTP status code mappings


## 📝 What Changed

1. **Added 4 new custom exceptions**:
   - `TimeoutError` (408)
   - `PublicationTimeoutError` (524)
   - `PayloadTooLargeError` (413)
   - `JSONParseError` (502)

2. **Enhanced Lens.org proxy**:
   - Streams responses instead of loading in memory
   - Checks content-length header (50MB limit)
   - Catches read errors for incomplete responses
   - Handles `ChunkedEncodingError` for truncated data

3. **Error handlers catch**:
   - `json.JSONDecodeError` → "Expecting value: line 1 column 1 (char 0)"
   - `requests.exceptions.ChunkedEncodingError` → Incomplete chunks
   - `Exception` during content reading → Truncated responses

## 💡 Developer Guide

### Raise Custom Errors in Your Code

```python
from my_site import PublicationTimeoutError, PayloadTooLargeError, JSONParseError

# In your API endpoint
if operation_took_too_long():
    raise PublicationTimeoutError("Data import timed out after 60s")

if response_size > MAX_SIZE:
    raise PayloadTooLargeError(f"Response is {size_mb}MB, max is 50MB")

if not json_is_valid:
    raise JSONParseError("Failed to parse publication data", original_error=e)
```

### All Errors Return Consistent JSON

Every error includes:
- `error`: Human-readable message
- `error_type`: Machine-readable identifier
- `status`: HTTP status code
- `suggestion`: How to fix it
- `details`: (optional) Technical details

## 🔧 Technical Implementation

### How Error Handlers are Registered

Error handlers are automatically registered when the Flask application starts through the blueprint initialization in [site/my_site/blueprints.py](site/my_site/blueprints.py):

```python
def create_blueprint(app):
    """Register blueprint for this application."""
    from my_site.error_handlers import register_error_handlers
    register_error_handlers(app)
    # ... rest of blueprint setup
```

### Custom Exception Classes

All custom exceptions inherit from Python's base `Exception` class and include:
- `message`: Human-readable error description
- `status_code`: HTTP status code to return
- `original_error`: (optional) The underlying exception that triggered this error

### Error Handler Flow

1. **Exception is raised** somewhere in your code (e.g., `raise PublicationTimeoutError()`)
2. **Flask catches the exception** using the registered `@app.errorhandler()` decorator
3. **Handler formats the response** as JSON with consistent structure
4. **HTTP status code is set** on the response object
5. **Response is returned** to the client

### Status Code Mappings

| Exception Class | Default Status | Can Override? |
|----------------|---------------|---------------|
| `TimeoutError` | 408 | Yes (via constructor) |
| `PublicationTimeoutError` | 524 | Yes (via constructor) |
| `PayloadTooLargeError` | 413 | Yes (via constructor) |
| `JSONParseError` | 502 | Yes (via constructor) |
| `json.JSONDecodeError` | 502 | No (fixed) |
| `requests.Timeout` | 504 or 524 | No (context-based) |

### Configuration Reference

Key settings in [invenio.cfg](invenio.cfg):

```python
# Timeout settings (if configured)
LENS_API_TIMEOUT = 60  # seconds
PUBLICATION_TIMEOUT = 120  # seconds

# Payload size limits
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
```

## 📋 Complete Status Code Reference

### 4xx Client Errors
- **408 Request Timeout**: Generic operation timeout, client should retry
- **413 Payload Too Large**: Response exceeds size limit, reduce request size

### 5xx Server Errors
- **502 Bad Gateway**: Upstream server returned invalid response (JSON parse errors, incomplete data)
- **504 Gateway Timeout**: Upstream server failed to respond in time (external services)
- **524 Origin Timeout**: Origin server timeout (publication operations, not standard HTTP but used by Cloudflare)

