from flask import request
from website.api.v1.utils.responses import success_response, error_response
from website.models import User, db
from website import bcrypt
from website.api.v1.auth.schemas import UserSchema
from flask_jwt_extended import get_jwt_identity

user_schema = UserSchema()


def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response("User not found", "NOT_FOUND", None, 404)
    return success_response(user_schema.dump(user), "Profile retrieved")


def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response("User not found", "NOT_FOUND", None, 404)

    data = request.get_json()
    fields_to_update = ["full_name", "phone_number", "fcm_token", "lat", "lon", "crop", "phone"]
    
    for field in fields_to_update:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return success_response(user_schema.dump(user), "Profile updated")


def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response("User not found", "NOT_FOUND", None, 404)

    data = request.get_json()
    old_pw = data.get("old_password")
    new_pw = data.get("new_password")

    if not old_pw or not new_pw:
        return error_response(
            "Old and new passwords required", "VALIDATION_ERROR", None, 400
        )

    if not bcrypt.check_password_hash(user.password_hash, old_pw):
        return error_response("Invalid old password", "AUTH_ERROR", None, 401)

    user.password_hash = bcrypt.generate_password_hash(new_pw).decode("utf-8")
    db.session.commit()
    return success_response(None, "Password changed successfully")


def delete_account():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response("User not found", "NOT_FOUND", None, 404)

    # We'll do a soft delete for safety
    user.is_active = False
    db.session.commit()
    return success_response(None, "Account deactivated successfully")
