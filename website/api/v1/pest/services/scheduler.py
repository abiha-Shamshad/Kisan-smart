"""
website/api/v1/pest/services/scheduler.py
=========================================
Celery Beat scheduled tasks for automated daily pest risk checks.
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Celery app setup ──────────────────────────────────────────────────────────

REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL or REDIS_URL == "redis://localhost:6379/0":
    # Fallback for Windows/Local Dev without Redis
    # Using SQLAlchemy as a broker (sqlite)
    DB_PATH = os.path.abspath(os.path.join(os.getcwd(), "instance", "celery_broker.db"))
    BROKER_URL = f"sqla+sqlite:///{DB_PATH}"
    logger.info(f"Redis not found or default. Using SQLite broker: {BROKER_URL}")
else:
    BROKER_URL = REDIS_URL

celery_app = Celery(
    "kisan_smart",
    broker=BROKER_URL,
    backend="db+sqlite:///instance/celery_results.db",
)

celery_app.conf.update(
    task_serializer    = "json",
    result_serializer  = "json",
    accept_content     = ["json"],
    timezone           = "Asia/Karachi",
    enable_utc         = True,

    beat_schedule = {
        "daily-pest-risk-check": {
            "task":     "website.api.v1.pest.services.scheduler.run_daily_pest_checks",
            "schedule": crontab(hour=6, minute=0),
        },
        "weekly-district-summary": {
            "task":     "website.api.v1.pest.services.scheduler.send_weekly_district_summary",
            "schedule": crontab(hour=7, minute=0, day_of_week="monday"),
        },
    },
)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@celery_app.task(
    name    = "website.api.v1.pest.services.scheduler.run_daily_pest_checks",
    bind    = True,
    max_retries = 3,
    default_retry_delay = 300,
)
def run_daily_pest_checks(self):
    from website import create_app, db
    from website.models import User
    from .engine import get_high_risk_alerts
    from .notifications import send_push_notification, send_whatsapp_alert

    app = create_app()
    with app.app_context():
        farmers = db.session.query(User).filter(
            User.lat.isnot(None),
            User.lon.isnot(None),
            User.crop.isnot(None),
            User.role_id == 2,
        ).all()

        logger.info(f"Daily pest check: processing {len(farmers)} farmers")
        sent = skipped = errors = 0

        for farmer in farmers:
            try:
                alerts = get_high_risk_alerts(
                    lat       = float(farmer.lat),
                    lon       = float(farmer.lon),
                    crop      = farmer.crop,
                    threshold = 50,
                )

                if not alerts:
                    skipped += 1
                    continue

                critical = [a for a in alerts if a.severity in ("High", "Critical")]
                if not critical:
                    skipped += 1
                    continue

                top_alert = critical[0]
                title = f"⚠️ {top_alert.severity} Risk: {top_alert.pest_name}"
                body  = (
                    f"Risk score: {top_alert.score:.0f}/100\n"
                    f"Cause: {', '.join(top_alert.triggered_by[:2])}\n"
                    f"Action: {top_alert.treatment[:80]}..."
                )
                wa_body = (
                    f"*Kisan Smart - فصل انتباہ* ⚠️\n\n"
                    f"*{top_alert.urdu_name}* ({top_alert.pest_name})\n"
                    f"شدت: *{top_alert.severity}* — اسکور: {top_alert.score:.0f}/100\n\n"
                    f"*وجہ:* {', '.join(top_alert.triggered_by[:2])}\n\n"
                    f"*علاج:* {top_alert.treatment}\n"
                    f"*دوائی:* {top_alert.pesticide}"
                )

                if farmer.fcm_token:
                    send_push_notification(
                        token = farmer.fcm_token,
                        title = title,
                        body  = body,
                        data  = {
                            "type":      "pest_alert",
                            "pest":      top_alert.pest_name,
                            "crop":      farmer.crop,
                            "score":     str(top_alert.score),
                            "severity":  top_alert.severity,
                        },
                    )

                if farmer.phone:
                    send_whatsapp_alert(phone=farmer.phone, message=wa_body)

                sent += 1

            except Exception as e:
                logger.error(f"Failed for user {farmer.id}: {e}")
                errors += 1

        return {"sent": sent, "skipped": skipped, "errors": errors}


@celery_app.task(name="website.api.v1.pest.services.scheduler.send_weekly_district_summary")
def send_weekly_district_summary():
    from website import create_app, db
    from website.models import User, PestAlertLog
    from .notifications import send_whatsapp_alert
    from sqlalchemy import func
    from datetime import timedelta

    app = create_app()
    with app.app_context():
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)

        top_pests = (
            db.session.query(
                PestAlertLog.pest_name,
                PestAlertLog.crop,
                func.count(PestAlertLog.id).label("reports"),
            )
            .filter(PestAlertLog.reported_at >= week_ago)
            .group_by(PestAlertLog.pest_name, PestAlertLog.crop)
            .order_by(func.count(PestAlertLog.id).desc())
            .limit(3)
            .all()
        )

        if not top_pests:
            return

        summary_lines = [f"  • {p.pest_name} ({p.crop}): {p.reports} رپورٹ" for p in top_pests]
        message = (
            f"*Kisan Smart - ہفتہ وار خلاصہ* 📋\n\n"
            f"اس ہفتے آپ کے علاقے میں:\n"
            + "\n".join(summary_lines)
            + "\n\n"
            "اپنی فصل کا معائنہ کریں اور مقامی زرعی افسر سے رابطہ کریں۔"
        )

        farmers_with_wa = db.session.query(User).filter(
            User.phone.isnot(None),
            User.role_id == 2,
        ).all()

        for farmer in farmers_with_wa:
            send_whatsapp_alert(phone=farmer.phone, message=message)


@celery_app.task(name="website.api.v1.pest.services.scheduler.check_single_farmer")
def check_single_farmer(user_id: int):
    from website import create_app, db
    from website.models import User
    from .engine import assess_risk

    app = create_app()
    with app.app_context():
        farmer = db.session.get(User, user_id)
        if not farmer or not farmer.lat or not farmer.crop:
            return {"error": "Farmer data incomplete"}

        risks = assess_risk(float(farmer.lat), float(farmer.lon), farmer.crop)
        return {
            "user_id": user_id,
            "risks": [
                {"pest": r.pest_name, "score": r.score, "severity": r.severity}
                for r in risks
            ],
        }
