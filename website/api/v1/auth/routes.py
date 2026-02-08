from flask import Blueprint, request
from .controllers import (
    register_user,
    login_user,
    logout_user,
    get_current_user,
    verify_email,
    forgot_password,
    reset_password,
)
from flask_jwt_extended import jwt_required

from website import limiter

auth_api = Blueprint("auth_api", __name__)


@auth_api.route("/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    return register_user()


@auth_api.route("/login", methods=["POST"])
@limiter.limit("10 per hour")
def login():
    return login_user()


@auth_api.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return logout_user()


@auth_api.route("/me", methods=["GET"])
@jwt_required()
def me():
    return get_current_user()


@auth_api.route("/verify/<token>", methods=["GET"])
def verify(token):
    return verify_email(token)


@auth_api.route("/forgot-password", methods=["POST"])
def forgot():
    return forgot_password()


@auth_api.route("/reset-password", methods=["POST"])
def reset():
    return reset_password()
