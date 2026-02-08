from flask import jsonify, current_app
import time


def success_response(data=None, message="Operation successful", status_code=200):
    """Returns a standardized success response."""
    response = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": time.time(),
        "api_version": current_app.config.get("API_VERSION", "v1"),
    }
    return jsonify(response), status_code


def error_response(
    message="An error occurred",
    error_code="INTERNAL_SERVER_ERROR",
    details=None,
    status_code=500,
):
    """Returns a standardized error response."""
    response = {
        "success": False,
        "error": {"code": error_code, "message": message, "details": details},
        "timestamp": time.time(),
        "api_version": current_app.config.get("API_VERSION", "v1"),
    }
    return jsonify(response), status_code
