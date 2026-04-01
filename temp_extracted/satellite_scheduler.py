"""
services/satellite_scheduler.py
=================================
Celery Beat task that runs every Monday at 5 AM PKT,
fetches fresh Sentinel-2 stats for all active fields,
and alerts farmers whose NDVI has dropped significantly.

Start alongside your existing pest alert scheduler:
  celery -A services.satellite_scheduler worker --beat --loglevel=info
"""

import logging
from datetime import datetime, timedelta, timezone
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

REDIS_URL = __import__("os").environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("kisan_satellite", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    timezone        = "Asia/Karachi",
    enable_utc      = True,
    task_serializer = "json",
    beat_schedule   = {
        "weekly-field-health-check": {
            "task":     "services.satellite_scheduler.run_weekly_field_checks",
            "schedule": crontab(hour=5, minute=0, day_of_week="monday"),
        },
    },
)


@celery_app.task(
    name        = "services.satellite_scheduler.run_weekly_field_checks",
    bind        = True,
    max_retries = 3,
    default_retry_delay = 600,
)
def run_weekly_field_checks(self):
    """
    Weekly task: refresh NDVI for all active fields and alert on significant drops.
    """
    from website import create_app, db
    from models.field_models import Field, SatelliteCache
    from services.satellite_service import fetch_field_stats, compute_trend
    from services.notification_service import send_push_notification, send_whatsapp_alert

    app = create_app()
    with app.app_context():
        fields = db.session.query(Field).filter(
            Field.is_active == True
        ).all()

        logger.info(f"Weekly satellite check: {len(fields)} active fields")
        updated = errors = alerted = 0

        end_date   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")

        for field in fields:
            try:
                stats = fetch_field_stats(
                    geojson_polygon = field.get_geojson_polygon(),
                    start_date      = start_date,
                    end_date        = end_date,
                    max_cloud_pct   = 40,   # slightly lenient for automation
                    interval_days   = 10,
                )

                if not stats:
                    logger.debug(f"Field {field.id}: no cloud-free imagery this week")
                    continue

                latest = stats[-1]

                # Save to cache
                entry = SatelliteCache(
                    field_id     = field.id,
                    date         = latest["date"],
                    ndvi_mean    = latest.get("ndvi", {}).get("mean"),
                    ndvi_std     = latest.get("ndvi", {}).get("std"),
                    ndvi_min     = latest.get("ndvi", {}).get("min"),
                    ndvi_max     = latest.get("ndvi", {}).get("max"),
                    ndwi_mean    = latest.get("ndwi", {}).get("mean"),
                    evi_mean     = latest.get("evi",  {}).get("mean"),
                    cloud_pct    = latest.get("cloud_pct"),
                    health_label = latest.get("health", {}).get("label"),
                    health_color = latest.get("health", {}).get("color"),
                )
                db.session.add(entry)
                db.session.commit()
                updated += 1

                # Trend check for alerts
                all_cached = (
                    db.session.query(SatelliteCache)
                    .filter(SatelliteCache.field_id == field.id)
                    .order_by(SatelliteCache.date.asc())
                    .all()
                )
                series = [r.to_dict() for r in all_cached]
                trend  = compute_trend(series)

                if trend.get("alert") and field.owner:
                    farmer = field.owner
                    msg = (
                        f"🛰 *Kisan Smart Satellite Alert*\n\n"
                        f"کھیت: *{field.name}* ({field.crop})\n"
                        f"{trend['alert_msg']}\n\n"
                        "مزید معلومات کے لیے ایپ کھولیں۔"
                    )
                    if farmer.fcm_token:
                        send_push_notification(
                            token  = farmer.fcm_token,
                            title  = f"🛰 {field.name}: NDVI گر رہا ہے",
                            body   = f"NDVI: {latest.get('ndvi',{}).get('mean',0):.2f} — {trend['alert_msg'][:60]}",
                            data   = {"type": "satellite_alert", "field_id": str(field.id)},
                        )
                    if farmer.phone:
                        send_whatsapp_alert(phone=farmer.phone, message=msg)
                    alerted += 1

            except Exception as e:
                logger.error(f"Field {field.id} satellite check failed: {e}")
                errors += 1

        logger.info(
            f"Weekly satellite done — updated:{updated} alerted:{alerted} errors:{errors}"
        )
        return {"updated": updated, "alerted": alerted, "errors": errors}
