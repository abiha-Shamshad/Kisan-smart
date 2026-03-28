from flask import Blueprint, request
from .controllers import (
    get_history,
    get_prediction_detail,
    delete_prediction,
    export_history,
    get_history_stats,
)
history_api = Blueprint("history_api", __name__)


@history_api.route("", methods=["GET"])
def list_history():
    return get_history()


@history_api.route("/stats", methods=["GET"])
def history_stats():
    return get_history_stats()


@history_api.route("/<prediction_id>", methods=["GET"])
def detail(prediction_id):
    return get_prediction_detail(prediction_id)


@history_api.route("/<prediction_id>", methods=["DELETE"])
def delete(prediction_id):
    return delete_prediction(prediction_id)


@history_api.route("/export", methods=["GET"])
def export():
    return export_history()
