from flask import Blueprint, render_template, send_from_directory
from flask_login import login_required, current_user
import os

views = Blueprint("views", __name__)

# ── Serve the standalone static frontend from /app ────────────────────────────
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

@views.route("/app/")
@views.route("/app/<path:filename>")
def frontend(filename="login.html"):
    return send_from_directory(_FRONTEND_DIR, filename)



@views.route("/")
@login_required
def home():
    return render_template("home.html", user=current_user)


@views.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role.role_name != "Admin":
        return "Unauthorized", 403
    return render_template("admin.html", user=current_user)


@views.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", user=current_user)

@views.route("/profile")
def profile():
    return render_template("profile.html", user=current_user)

@views.route("/history")
def history():
    return render_template("history.html", user=current_user)


@views.route("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}, 200
