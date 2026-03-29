from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    current_app,
)
from urllib.parse import urlparse
from .models import User, Role
from . import db, bcrypt, limiter
from .forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
from .utils import send_verification_email, send_reset_email, verify_token
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))
    form = RegistrationForm()
    if form.validate_on_submit():
        role = Role.query.filter_by(role_name="Farmer").first()
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            full_name=form.full_name.data,
            phone_number=form.phone_number.data,
            role_id=role.role_id if role else 2,
        )
        db.session.add(user)
        db.session.commit()

        try:
            send_verification_email(user)
            flash(
                "Account created! A verification email has been sent to your email address.",
                "success",
            )
        except Exception as e:
            flash(
                "Account created, but we failed to send the verification email. Please contact support.",
                "warning",
            )
            current_app.logger.error(f"Mail error: {e}")

        return redirect(url_for("auth.login"))
    return render_template(
        "register.html", title="Register", form=form, user=current_user
    )


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            # Check for lockout
            if user.is_locked and user.locked_until > datetime.utcnow():
                flash(
                    f'Account locked due to multiple failed attempts. Try again after {user.locked_until.strftime("%H:%M:%S")}',
                    "error",
                )
                return render_template(
                    "login.html", title="Login", form=form, user=current_user
                )

            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                if not user.is_verified:
                    flash(
                        "Please verify your email address before logging in.", "warning"
                    )
                    return redirect(url_for("auth.login"))

                # Reset failed attempts on success
                user.failed_login_attempts = 0
                user.is_locked = False
                user.last_login_attempt = datetime.utcnow()
                db.session.commit()

                login_user(user, remember=form.remember.data)
                next_page = request.args.get("next")
                # Only follow next if it's a safe relative URL and not just "/"
                # (visiting "/" unauthenticated sets next="/" which would
                # double-redirect through views.home → views.dashboard)
                parsed = urlparse(next_page) if next_page else None
                is_safe_next = (
                    parsed
                    and not parsed.netloc  # no external domain
                    and parsed.path not in ("/", "")
                )
                return redirect(next_page if is_safe_next else url_for("views.dashboard"))
            else:
                # Increment failed attempts
                user.failed_login_attempts += 1
                user.last_login_attempt = datetime.utcnow()
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                    flash(
                        "Account locked for 30 minutes due to multiple failed attempts.",
                        "error",
                    )
                else:
                    flash(
                        "Login Unsuccessful. Please check email and password", "error"
                    )
                db.session.commit()
        else:
            flash("Login Unsuccessful. Please check email and password", "error")

    return render_template("login.html", title="Login", form=form, user=current_user)


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("views.about"))


@auth.route("/verify-email/<token>")
def verify_email(token):
    email = verify_token(token, salt="email-confirm", expiration=86400)  # 24 hours
    if email is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("auth.register"))
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.session.commit()
        flash("Your email has been verified! You are now able to log in", "success")
    return redirect(url_for("auth.login"))


@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash(
            "An email has been sent with instructions to reset your password.", "info"
        )
        return redirect(url_for("auth.login"))
    return render_template(
        "forgot_password.html", title="Reset Password", form=form, user=current_user
    )


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))
    email = verify_token(token, salt="password-reset", expiration=3600)  # 1 hour
    if email is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("auth.forgot_password"))
    user = User.query.filter_by(email=email).first()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user.password_hash = hashed_password
        db.session.commit()
        flash("Your password has been updated! You are now able to log in", "success")
        return redirect(url_for("auth.login"))
    return render_template(
        "reset_password.html", title="Reset Password", form=form, user=current_user
    )
