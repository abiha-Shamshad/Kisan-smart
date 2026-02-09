from flask import Blueprint, request
from .controllers import get_prediction, get_batch_prediction, validate_input
from flask_jwt_extended import jwt_required

predict_api = Blueprint("predict_api", __name__)


@predict_api.route("", methods=["POST"])
@jwt_required(optional=True)  # Allow guest predictions but track if logged in
def predict():
    return get_prediction()


@predict_api.route("/batch", methods=["POST"])
@jwt_required()
def predict_batch():
    return get_batch_prediction()


@predict_api.route("/validate", methods=["POST"])
def validate():
    return validate_input()
