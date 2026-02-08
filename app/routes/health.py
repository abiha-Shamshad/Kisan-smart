"""
Health check endpoint for monitoring
"""

from flask import Blueprint, jsonify
from datetime import datetime
from app import db
import os
import shutil

health_bp = Blueprint("health", __name__)


def check_database():
    """Check if database connection is healthy"""
    try:
        # Execute a simple query
        db.session.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False


def check_ml_models():
    """Check if ML models are loaded"""
    try:
        from app.ml.predictor import FertilizerPredictor

        predictor = FertilizerPredictor()
        # Try a simple prediction to verify model works
        test_data = {
            "crop_type": "wheat",
            "nitrogen": 45,
            "phosphorus": 30,
            "potassium": 25,
            "ph": 6.8,
        }
        result = predictor.predict(test_data)
        return "fertilizer_type" in result
    except Exception as e:
        print(f"ML model health check failed: {e}")
        return False


def check_disk_space():
    """Check if adequate disk space is available"""
    try:
        stat = shutil.disk_usage("/")
        # Consider healthy if >10% free space
        free_percent = (stat.free / stat.total) * 100
        return free_percent > 10
    except Exception as e:
        print(f"Disk space check failed: {e}")
        return False


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Comprehensive health check endpoint
    Returns 200 if healthy, 503 if unhealthy
    """
    checks = {
        "database": check_database(),
        "ml_models": check_ml_models(),
        "disk_space": check_disk_space(),
    }

    # Overall health is healthy only if all checks pass
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    status_code = 200 if overall_status == "healthy" else 503

    return (
        jsonify(
            {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": checks,
                "version": "1.0.0",  # Application version
            }
        ),
        status_code,
    )


@health_bp.route("/health/ready", methods=["GET"])
def readiness_check():
    """
    Readiness check - is the application ready to serve requests?
    """
    # Check only critical components
    database_ready = check_database()
    ml_ready = check_ml_models()

    is_ready = database_ready and ml_ready
    status_code = 200 if is_ready else 503

    return (
        jsonify({"ready": is_ready, "database": database_ready, "ml_models": ml_ready}),
        status_code,
    )


@health_bp.route("/health/live", methods=["GET"])
def liveness_check():
    """
    Liveness check - is the application running?
    Simple check that returns 200 if server is responsive
    """
    return jsonify({"alive": True, "timestamp": datetime.utcnow().isoformat()}), 200
