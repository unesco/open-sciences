"""Custom error handlers for InvenioRDM application.

This module provides custom HTTP error responses and handlers for various
error scenarios including timeouts, validation errors, and service errors.
"""

from flask import jsonify, request
from werkzeug.exceptions import HTTPException
import logging
from requests.exceptions import Timeout, RequestException
import json

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom exception for timeout errors."""
    
    def __init__(self, message="Operation timed out", status_code=408):
        """Initialize timeout error.
        
        Args:
            message: Error message
            status_code: HTTP status code (default: 408 Request Timeout)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PublicationTimeoutError(TimeoutError):
    """Specific timeout error for publication operations."""
    
    def __init__(self, message="Publication operation timed out", status_code=524):
        """Initialize publication timeout error.
        
        Args:
            message: Error message
            status_code: HTTP status code (default: 524 Origin Timeout)
        """
        super().__init__(message, status_code)


class PayloadTooLargeError(Exception):
    """Custom exception for payload size errors."""
    
    def __init__(self, message="Response payload too large or malformed", status_code=413):
        """Initialize payload error.
        
        Args:
            message: Error message
            status_code: HTTP status code (default: 413 Payload Too Large)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class JSONParseError(Exception):
    """Custom exception for JSON parsing errors (empty/truncated responses)."""
    
    def __init__(self, message="Failed to parse response data", status_code=502, original_error=None):
        """Initialize JSON parse error.
        
        Args:
            message: Error message
            status_code: HTTP status code (default: 502 Bad Gateway)
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.original_error = original_error


def register_error_handlers(app):
    """Register custom error handlers with Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(TimeoutError)
    def handle_timeout_error(error):
        """Handle custom TimeoutError exceptions."""
        logger.error(f"Timeout error: {error.message}")
        response = jsonify({
            "status": error.status_code,
            "message": error.message,
            "error_type": "timeout"
        })
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(PublicationTimeoutError)
    def handle_publication_timeout(error):
        """Handle publication-specific timeout errors."""
        logger.error(f"Publication timeout: {error.message}")
        response = jsonify({
            "status": error.status_code,
            "message": error.message,
            "error_type": "publication_timeout",
            "retry_after": 60  # Suggest retry after 60 seconds
        })
        response.status_code = error.status_code
        # Add Retry-After header
        response.headers['Retry-After'] = '60'
        return response
    
    @app.errorhandler(PayloadTooLargeError)
    def handle_payload_too_large(error):
        """Handle payload size errors."""
        logger.error(f"Payload too large: {error.message}")
        return jsonify({
            "error": error.message,
            "error_type": "payload_too_large",
            "status": error.status_code,
            "suggestion": "The response data is too large. Try limiting the request size or use pagination."
        }), error.status_code
    
    @app.errorhandler(JSONParseError)
    def handle_json_parse_error(error):
        """Handle JSON parsing errors."""
        logger.error(f"JSON parse error: {error.message}")
        response_data = {
            "error": error.message,
            "error_type": "json_parse_error",
            "status": error.status_code,
            "suggestion": "The response data is incomplete or malformed. This often happens with large payloads. Try reducing the request size."
        }
        if error.original_error:
            response_data["details"] = str(error.original_error)
        return jsonify(response_data), error.status_code
    
    @app.errorhandler(json.JSONDecodeError)
    def handle_json_decode_error(error):
        """Handle standard JSON decode errors (e.g., 'Expecting value: line 1 column 1')."""
        logger.error(f"JSONDecodeError: {str(error)}")
        return jsonify({
            "error": "Failed to parse JSON response",
            "error_type": "json_decode_error",
            "status": 502,
            "details": str(error),
            "suggestion": "The response data is incomplete or malformed. This often happens with very large responses. Try reducing the request size or using pagination."
        }), 502
    
    @app.errorhandler(408)
    def handle_request_timeout(error):
        """Handle 408 Request Timeout errors."""
        logger.error(f"Request timeout: {request.url}")
        return jsonify({
            "status": 408,
            "message": "Request timed out. Please try again.",
            "error_type": "request_timeout"
        }), 408
    
    @app.errorhandler(504)
    def handle_gateway_timeout(error):
        """Handle 504 Gateway Timeout errors."""
        logger.error(f"Gateway timeout: {request.url}")
        return jsonify({
            "status": 504,
            "message": "Gateway timeout. The upstream server did not respond in time.",
            "error_type": "gateway_timeout"
        }), 504
    
    # Note: 524 is not a standard HTTP code, so we only handle it via PublicationTimeoutError exception
    # The PublicationTimeoutError handler above already returns status code 524
    
    # Handle requests library timeouts
    @app.errorhandler(Timeout)
    def handle_requests_timeout(error):
        """Handle requests library Timeout exceptions."""
        logger.error(f"Requests timeout: {str(error)}")
        
        # Check if it's a publication-related endpoint
        if '/records' in request.path or '/api/records' in request.path:
            return handle_publication_timeout(
                PublicationTimeoutError("Publication request timed out")
            )
        
        return jsonify({
            "status": 504,
            "message": "External service timeout",
            "error_type": "external_timeout"
        }), 504
    
    # Generic HTTPException handler
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle generic HTTP exceptions."""
        response = jsonify({
            "status": error.code,
            "message": error.description,
            "error_type": "http_error"
        })
        response.status_code = error.code
        return response
    
    logger.info("Custom error handlers registered")


def configure_timeout_settings(app):
    """Configure timeout-related settings for the application.
    
    Args:
        app: Flask application instance
    """
    # Set request timeout (in seconds)
    app.config.setdefault('REQUEST_TIMEOUT', 30)
    
    # Set publication-specific timeout
    app.config.setdefault('PUBLICATION_TIMEOUT', 60)
    
    # Set external service timeout
    app.config.setdefault('EXTERNAL_SERVICE_TIMEOUT', 45)
    
    # Set custom status codes
    app.config.setdefault('TIMEOUT_STATUS_CODE', 408)
    app.config.setdefault('PUBLICATION_TIMEOUT_STATUS_CODE', 524)
    app.config.setdefault('GATEWAY_TIMEOUT_STATUS_CODE', 504)
    
    logger.info(f"Timeout settings configured: "
                f"REQUEST_TIMEOUT={app.config['REQUEST_TIMEOUT']}s, "
                f"PUBLICATION_TIMEOUT={app.config['PUBLICATION_TIMEOUT']}s")
