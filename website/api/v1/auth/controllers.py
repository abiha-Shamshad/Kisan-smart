from flask import request, current_app
from flask_login import login_user as flask_login_user

from website.models import User, db
from website import bcrypt
from .schemas import RegisterSchema, LoginSchema, UserSchema
from website.api.v1.utils.responses import success_response, error_response
from flask_jwt_extended import create_access_token, get_jwt_identity
import website.utils
import datetime

register_schema = RegisterSchema()
login_schema = LoginSchema()
user_schema = UserSchema()


def register_user():
    data = request.get_json()
    errors = register_schema.validate(data)
    if errors:
        return error_response("Validation failed", "VALIDATION_ERROR", errors, 422)

    if User.query.filter_by(email=data["email"]).first():
        return error_response(
            "Email already registered", "EMAIL_ALREADY_EXISTS", None, 400
        )

    hashed_pw = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user = User(
        username=data.get("username"),
        full_name=data.get("full_name"),
        email=data["email"],
        password_hash=hashed_pw,
        phone_number=data.get("phone_number"),
        is_verified=False,  # Should trigger email verification in real app
    )

    db.session.add(new_user)
    db.session.commit()

    # Send verification email
    website.utils.send_verification_email(new_user)

    return success_response(
        user_schema.dump(new_user), "User registered successfully", 201
    )


def login_user():
    data = request.get_json()
    errors = login_schema.validate(data)
    if errors:
        return error_response("Validation failed", "VALIDATION_ERROR", errors, 422)

    user = User.query.filter_by(email=data["email"]).first()

    if user and bcrypt.check_password_hash(user.password_hash, data["password"]):
        if not user.is_active:
            return error_response(
                "Account is deactivated", "ACCOUNT_DEACTIVATED", None, 403
            )
        if user.is_locked:
            return error_response("Account is locked", "ACCOUNT_LOCKED", None, 403)

        if not user.is_verified:
            return error_response(
                "Please verify your email address before logging in.",
                "EMAIL_NOT_VERIFIED",
                None,
                401,
            )

        access_token = create_access_token(identity=str(user.id))
        # Establish Flask-Login session for template-based routes (like /dashboard)
        flask_login_user(user, remember=data.get("remember_me", False))
        
        return success_response(

            {"access_token": access_token, "user": user_schema.dump(user)},
            "Login successful",
        )

    return error_response("Invalid email or password", "INVALID_CREDENTIALS", None, 401)


def logout_user():
    # JWT is stateless, client should discard token.
    # For server-side logout, we could use a blocklist in Redis.
    return success_response(None, "Logged out successfully (Please discard your token)")


def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", "USER_NOT_FOUND", None, 404)
    return success_response(user_schema.dump(user), "User profile retrieved")


def verify_email(token):
    email = website.utils.verify_token(token, salt="email-confirm")
    if not email:
        return error_response(
            "Invalid or expired verification link", "INVALID_TOKEN", None, 400
        )

    user = User.query.filter_by(email=email).first()
    if not user:
        return error_response("User not found", "USER_NOT_FOUND", None, 404)

    user.is_verified = True
    db.session.commit()

    return success_response(None, "Email verified successfully")


def forgot_password():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return error_response("Email is required", "EMAIL_REQUIRED", None, 400)

    user = User.query.filter_by(email=email).first()
    if user:
        website.utils.send_reset_email(user)

    return success_response(None, "Password reset email sent if account exists")


def reset_password():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        return error_response(
            "Token and password are required", "MISSING_FIELDS", None, 400
        )

    email = website.utils.verify_token(token, salt="password-reset")
    if not email:
        return error_response(
            "Invalid or expired reset link", "INVALID_TOKEN", None, 400
        )

    user = User.query.filter_by(email=email).first()
    if not user:
        return error_response("User not found", "USER_NOT_FOUND", None, 404)

    user.set_password(new_password)
    db.session.commit()

    return success_response(None, "Password reset successfully")
