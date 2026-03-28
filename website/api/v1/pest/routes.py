"""
website/api/v1/pest/routes.py
============================
Flask Blueprint for pest & disease outbreak alert endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone

from .services.engine import assess_risk
from .services.notifications import send_push_notification, send_whatsapp_alert
from website.models import User, PestAlertLog
from website import db

pest_api = Blueprint("pest_api", __name__)


@pest_api.route("/assess", methods=["GET"])
def assess():
    lat  = request.args.get("lat",  type=float)
    lon  = request.args.get("lon",  type=float)
    crop = request.args.get("crop", type=str)
    days = request.args.get("days", default=7, type=int)

    if lat is None or lon is None or not crop:
        return jsonify({"error": "lat, lon, and crop are required"}), 400

    try:
        risks = assess_risk(lat, lon, crop, forecast_days=days)
    except Exception as e:
        current_app.logger.error(f"Risk assessment failed: {e}")
        return jsonify({"error": "Weather data unavailable."}), 503

    return jsonify({
        "location": {"lat": lat, "lon": lon},
        "crop":     crop,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "risks": [
            {
                "pest":         r.pest_name,
                "urdu_name":    r.urdu_name,
                "score":        r.score,
                "severity":     r.severity,
                "triggered_by": r.triggered_by,
                "treatment":    r.treatment,
                "pesticide":    r.pesticide,
            }
            for r in risks
        ],
    })


@pest_api.route("/report", methods=["POST"])
def report_sighting():
    user_id = getattr(current_user, 'id', 1) if current_user.is_authenticated else 1
    data    = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body required"}), 400

    required = ["crop", "pest_name", "lat", "lon", "severity"]
    missing  = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    log = PestAlertLog(
        user_id   = user_id,
        crop      = data["crop"],
        pest_name = data["pest_name"],
        lat       = data["lat"],
        lon       = data["lon"],
        severity  = data["severity"],
        photo_url = data.get("photo_url"),
        reported_at = datetime.now(timezone.utc),
    )
    db.session.add(log)
    db.session.commit()

    _maybe_broadcast_district_alert(data["crop"], data["pest_name"], data["lat"], data["lon"])

    return jsonify({"message": "Report submitted. Thank you!", "report_id": log.id}), 201


@pest_api.route("/district-alerts", methods=["GET"])
def district_alerts():
    lat  = request.args.get("lat",  type=float)
    lon  = request.args.get("lon",  type=float)
    crop = request.args.get("crop", type=str)

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400

    radius = 0.45
    query = db.session.query(PestAlertLog).filter(
        PestAlertLog.lat.between(lat - radius, lat + radius),
        PestAlertLog.lon.between(lon - radius, lon + radius),
        PestAlertLog.reported_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0),
    )
    if crop:
        query = query.filter(PestAlertLog.crop == crop)

    reports = query.all()

    grouped = {}
    for r in reports:
        key = r.pest_name
        if key not in grouped:
            grouped[key] = {"count": 0, "crop": r.crop, "pest": key, "severities": []}
        grouped[key]["count"] += 1
        grouped[key]["severities"].append(r.severity)

    alerts = []
    for pest, info in grouped.items():
        max_sev = max(info["severities"], key=lambda s: ["Low","Medium","High","Critical"].index(s))
        alerts.append({
            "pest":        pest,
            "crop":        info["crop"],
            "report_count": info["count"],
            "max_severity": max_sev,
            "confirmed":   info["count"] >= 3,
        })

    return jsonify({
        "location": {"lat": lat, "lon": lon},
        "radius_km": 50,
        "alerts": sorted(alerts, key=lambda a: -a["report_count"]),
    })


@pest_api.route("/weather", methods=["GET"])
def get_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    days = request.args.get("days", default=7, type=int)

    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400

    from .services.engine import fetch_weather
    try:
        w = fetch_weather(lat, lon, days=days)
        
        # Generate some weather-specific alerts based on the window
        alerts = []
        if w.rain_total_mm > 30:
            alerts.append({"type": "warning", "title": "Heavy Rain Forecast", "body": f"Total expected rainfall: {w.rain_total_mm:.1f}mm. Avoid spraying."})
        if w.temp_max > 42:
            alerts.append({"type": "critical", "title": "Extreme Heatwave", "body": f"Temps reaching {w.temp_max:.1f}°C. Ensure adequate irrigation."})
        if w.rh_mean > 85:
            alerts.append({"type": "info", "title": "High Humidity", "body": "Ideal conditions for fungal growth. Monitor crops closely."})

        return jsonify({
            "summary": {
                "temp_min": w.temp_min,
                "temp_max": w.temp_max,
                "temp_mean": w.temp_mean,
                "rain_total": w.rain_total_mm,
                "humidity_avg": w.rh_mean
            },
            "alerts": alerts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 503


def _maybe_broadcast_district_alert(crop, pest_name, lat, lon):
    radius = 0.45
    count = db.session.query(PestAlertLog).filter(
        PestAlertLog.pest_name == pest_name,
        PestAlertLog.lat.between(lat - radius, lat + radius),
        PestAlertLog.lon.between(lon - radius, lon + radius),
    ).count()

    if count >= 3:
        nearby_users = db.session.query(User).filter(
            User.lat.between(lat - radius, lat + radius),
            User.lon.between(lon - radius, lon + radius),
        ).all()

        for user in nearby_users:
            if user.fcm_token:
                send_push_notification(
                    token   = user.fcm_token,
                    title   = f"⚠️ {pest_name} outbreak near you!",
                    body    = f"{count} farmers in your area reported {pest_name} on {crop}.",
                    data    = {"type": "pest_alert", "pest": pest_name, "crop": crop},
                )
            if user.phone:
                send_whatsapp_alert(
                    phone   = user.phone,
                    message = f"*Kisan Smart Alert* ⚠️\n*{pest_name}* outbreak reported near you!\nCrop: {crop}",
                )
