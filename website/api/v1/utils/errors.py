from flask import current_app
from website.api.v1.utils.responses import error_response
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    """Registers global error handlers for the application."""

    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(e):
        return error_response("Validation failed", "VALIDATION_ERROR", e.messages, 422)

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return error_response(e.description, f"HTTP_{e.code}", None, e.code)

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        current_app.logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
        return error_response("An unexpected error occurred", "INTERNAL_SERVER_ERROR", None, 500)

    @app.errorhandler(429)
    def handle_ratelimit_error(e):
        return error_response("Rate limit exceeded", "RATE_LIMIT_EXCEEDED", str(e.description), 429)
