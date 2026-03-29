from flask import Blueprint, request
from .controllers import get_prediction, get_batch_prediction, validate_input
from flask_jwt_extended import jwt_required

predict_api = Blueprint("predict_api", __name__)


@predict_api.route("", methods=["POST"])
def predict():
    return get_prediction()


@predict_api.route("/batch", methods=["POST"])
def predict_batch():
    return get_batch_prediction()


@predict_api.route("/calculate-npk", methods=["POST"])
def calculate_npk():
    from .controllers import get_npk_formula_prediction
    return get_npk_formula_prediction()


@predict_api.route("/budget-optimize", methods=["POST"])
def budget_optimize():
    from .controllers import get_budget_optimization
    return get_budget_optimization()


@predict_api.route("/generate-schedule", methods=["POST"])
def generate_schedule():
    from .controllers import get_schedule
    return get_schedule()


@predict_api.route("/ai-scan", methods=["POST"])
def ai_scan():
    from .controllers import get_ai_scan
    return get_ai_scan()


@predict_api.route("/validate", methods=["POST"])
def validate():
    return validate_input()
