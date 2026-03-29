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


@views.route("/firebase-messaging-sw.js")
def service_worker():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'firebase-messaging-sw.js')



@views.route("/")
@login_required
def home():
    from flask import redirect, url_for
    return redirect(url_for("views.dashboard"))


@views.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role.role_name != "Admin":
        return "Unauthorized", 403
    return render_template("admin.html", user=current_user)


@views.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@views.route("/npk-calculator")
@login_required
def calculator():
    return render_template("calculator.html", user=current_user)

@views.route("/budget-optimizer")
@login_required
def optimizer():
    return render_template("optimizer.html", user=current_user)

@views.route("/schedule")
@login_required
def schedule():
    return render_template("schedule.html", user=current_user)

@views.route("/ai-scan")
@login_required
def scan():
    return render_template("scan.html", user=current_user)

@views.route("/field-history")
@login_required
def field_history():
    return render_template("history_trends.html", user=current_user)

@views.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)

@views.route("/pest-alerts")
@login_required
def pest_alerts():
    return render_template("pest_alerts.html", user=current_user)


@views.route("/weather-alerts")
@login_required
def weather_alerts():
    return render_template("weather_alerts.html", user=current_user)


@views.route("/about")
def about():
    return render_template("about.html", user=current_user)


@views.route("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}, 200

@views.route("/voice")
def voice():
    return render_template("voice_dashboard.html")
