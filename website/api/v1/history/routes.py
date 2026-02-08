from flask import Blueprint, request
from .controllers import (
    get_history,
    get_prediction_detail,
    delete_prediction,
    export_history,
)
from flask_jwt_extended import jwt_required

history_api = Blueprint("history_api", __name__)


@history_api.route("/", methods=["GET"])
@jwt_required()
def list_history():
    return get_history()


@history_api.route("/<prediction_id>", methods=["GET"])
@jwt_required()
def detail(prediction_id):
    return get_prediction_detail(prediction_id)


@history_api.route("/<prediction_id>", methods=["DELETE"])
@jwt_required()
def delete(prediction_id):
    return delete_prediction(prediction_id)


@history_api.route("/export", methods=["GET"])
@jwt_required()
def export():
    return export_history()
