"""
routes/satellite.py
====================
Flask Blueprint for satellite field health monitoring endpoints.

Endpoints:
  POST   /api/satellite/fields          — Save field boundary polygon
  GET    /api/satellite/fields          — List all user's fields
  DELETE /api/satellite/fields/<id>     — Delete a field
  GET    /api/satellite/fields/<id>/health  — Get current health (cached NDVI)
  GET    /api/satellite/fields/<id>/timeseries — Get NDVI time series
  GET    /api/satellite/fields/<id>/summary   — Season summary + trend

Mount in create_app():
  from routes.satellite import satellite_bp
  app.register_blueprint(satellite_bp, url_prefix='/api/satellite')
"""

import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from website import db
from models.field_models import Field, SatelliteCache
from services.satellite_service import (
    fetch_field_stats, compute_trend, get_season_summary
)

logger = logging.getLogger(__name__)
satellite_bp = Blueprint("satellite", __name__)

# Max fields per user on free tier (processing unit budget)
MAX_FIELDS_FREE = 10


# ── POST /api/satellite/fields ────────────────────────────────────────────────

@satellite_bp.route("/fields", methods=["POST"])
@jwt_required()
def create_field():
    """
    Save a new field boundary drawn by the farmer on the map.

    Body JSON:
        {
          "name": "Home Field",
          "crop": "Wheat",
          "geometry": {
            "type": "Polygon",
            "coordinates": [[[74.1, 32.5], [74.2, 32.5], [74.2, 32.6], [74.1, 32.6], [74.1, 32.5]]]
          }
        }

    Response 201:
        { "field_id": 42, "area_ha": 1.23, "message": "Field saved" }
    """
    user_id = get_jwt_identity()
    data    = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "JSON body required"}), 400

    geometry = data.get("geometry")
    name     = data.get("name", "My Field").strip()
    crop     = data.get("crop", "").strip()

    if not geometry or geometry.get("type") != "Polygon":
        return jsonify({"error": "GeoJSON Polygon geometry required"}), 400

    # Check field count limit
    count = db.session.query(func.count(Field.id)).filter(
        Field.user_id == user_id, Field.is_active == True
    ).scalar()
    if count >= MAX_FIELDS_FREE:
        return jsonify({
            "error": f"Maximum {MAX_FIELDS_FREE} fields per account. "
                     "Delete an existing field to add a new one."
        }), 429

    try:
        field = Field.from_geojson(
            user_id          = user_id,
            name             = name,
            crop             = crop,
            geojson_geometry = geometry,
        )
        field.season_start = datetime.now(timezone.utc)
        db.session.add(field)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Field save failed: {e}", exc_info=True)
        return jsonify({"error": "Failed to save field boundary"}), 500

    return jsonify({
        "field_id": field.id,
        "area_ha":  field.area_ha,
        "message":  "Field saved successfully",
    }), 201


# ── GET /api/satellite/fields ─────────────────────────────────────────────────

@satellite_bp.route("/fields", methods=["GET"])
@jwt_required()
def list_fields():
    """Return all active fields for the current user as GeoJSON FeatureCollection."""
    user_id = get_jwt_identity()
    fields  = db.session.query(Field).filter(
        Field.user_id == user_id,
        Field.is_active == True,
    ).all()

    features = []
    for f in fields:
        feat = f.to_geojson()
        # Attach latest NDVI from cache if available
        latest = (
            db.session.query(SatelliteCache)
            .filter(SatelliteCache.field_id == f.id)
            .order_by(SatelliteCache.date.desc())
            .first()
        )
        if latest:
            feat["properties"]["latest_ndvi"]   = latest.ndvi_mean
            feat["properties"]["latest_date"]   = latest.date
            feat["properties"]["health_label"]  = latest.health_label
            feat["properties"]["health_color"]  = latest.health_color

        features.append(feat)

    return jsonify({
        "type":     "FeatureCollection",
        "features": features,
    })


# ── DELETE /api/satellite/fields/<field_id> ────────────────────────────────────

@satellite_bp.route("/fields/<int:field_id>", methods=["DELETE"])
@jwt_required()
def delete_field(field_id):
    user_id = get_jwt_identity()
    field   = db.session.get(Field, field_id)

    if not field or field.user_id != user_id:
        return jsonify({"error": "Field not found"}), 404

    field.is_active = False   # soft delete
    db.session.commit()
    return jsonify({"message": "Field deleted"}), 200


# ── GET /api/satellite/fields/<field_id>/health ───────────────────────────────

@satellite_bp.route("/fields/<int:field_id>/health", methods=["GET"])
@jwt_required()
def get_field_health(field_id):
    """
    Get current field health.
    Returns cached result if fresh (<7 days old), otherwise fetches from Sentinel Hub.

    Response:
        {
          "field_id":    42,
          "field_name":  "Home Field",
          "crop":        "Wheat",
          "area_ha":     1.23,
          "date":        "2025-03-22",
          "ndvi":        {"mean": 0.62, "std": 0.08, "min": 0.41, "max": 0.79},
          "ndwi":        {"mean": -0.12},
          "evi":         {"mean": 0.48},
          "cloud_pct":   8.2,
          "health":      {"label": "Good", "color": "#5cb85c"},
          "from_cache":  true
        }
    """
    user_id = get_jwt_identity()
    field   = db.session.get(Field, field_id)

    if not field or field.user_id != user_id or not field.is_active:
        return jsonify({"error": "Field not found"}), 404

    # Check cache first
    cached = (
        db.session.query(SatelliteCache)
        .filter(SatelliteCache.field_id == field_id)
        .order_by(SatelliteCache.date.desc())
        .first()
    )

    if cached and not cached.is_stale(max_age_days=7):
        result = cached.to_dict()
        result.update({
            "field_id":   field.id,
            "field_name": field.name,
            "crop":       field.crop,
            "area_ha":    field.area_ha,
            "from_cache": True,
        })
        return jsonify(result)

    # Cache stale or empty — fetch fresh data from Sentinel Hub
    try:
        end_date   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")

        stats = fetch_field_stats(
            geojson_polygon = field.get_geojson_polygon(),
            start_date      = start_date,
            end_date        = end_date,
            max_cloud_pct   = 30,
            interval_days   = 10,
        )

        if not stats:
            return jsonify({"error": "No cloud-free imagery available for this period"}), 404

        latest = stats[-1]  # most recent observation

        # Save/update cache
        cache_entry = SatelliteCache(
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
            full_stats_json = latest,
        )
        db.session.add(cache_entry)
        db.session.commit()

        latest.update({
            "field_id":   field.id,
            "field_name": field.name,
            "crop":       field.crop,
            "area_ha":    field.area_ha,
            "from_cache": False,
        })
        return jsonify(latest)

    except Exception as e:
        logger.error(f"Sentinel Hub fetch failed for field {field_id}: {e}", exc_info=True)
        return jsonify({"error": "Satellite data unavailable. Check credentials or try again."}), 503


# ── GET /api/satellite/fields/<field_id>/timeseries ───────────────────────────

@satellite_bp.route("/fields/<int:field_id>/timeseries", methods=["GET"])
@jwt_required()
def get_timeseries(field_id):
    """
    Get NDVI/NDWI/EVI time series for charting.

    Query params:
        days  (int) — how many days back (default 90)

    Response:
        {
          "field_name": "Home Field",
          "series": [
            {"date": "2025-01-01", "ndvi": 0.45, "ndwi": -0.1, "evi": 0.36},
            ...
          ],
          "trend": {"trend": "improving", "change_pct": 12.3, "alert": false}
        }
    """
    user_id = get_jwt_identity()
    field   = db.session.get(Field, field_id)

    if not field or field.user_id != user_id or not field.is_active:
        return jsonify({"error": "Field not found"}), 404

    days       = request.args.get("days", default=90, type=int)
    cutoff     = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    # Pull from cache first
    cached_series = (
        db.session.query(SatelliteCache)
        .filter(
            SatelliteCache.field_id == field_id,
            SatelliteCache.date >= cutoff,
        )
        .order_by(SatelliteCache.date.asc())
        .all()
    )

    if cached_series:
        series = [row.to_dict() for row in cached_series]
    else:
        # Fetch full range from Sentinel Hub
        end_date   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

        try:
            series = fetch_field_stats(
                geojson_polygon = field.get_geojson_polygon(),
                start_date      = start_date,
                end_date        = end_date,
                interval_days   = 10,
            )
            # Bulk-cache the results
            for point in series:
                entry = SatelliteCache(
                    field_id     = field.id,
                    date         = point["date"],
                    ndvi_mean    = point.get("ndvi", {}).get("mean"),
                    ndvi_std     = point.get("ndvi", {}).get("std"),
                    ndvi_min     = point.get("ndvi", {}).get("min"),
                    ndvi_max     = point.get("ndvi", {}).get("max"),
                    ndwi_mean    = point.get("ndwi", {}).get("mean"),
                    evi_mean     = point.get("evi",  {}).get("mean"),
                    cloud_pct    = point.get("cloud_pct"),
                    health_label = point.get("health", {}).get("label"),
                    health_color = point.get("health", {}).get("color"),
                )
                db.session.add(entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Time series fetch failed: {e}")
            return jsonify({"error": "Satellite data unavailable"}), 503

    # Flatten for charting
    chart_series = [
        {
            "date":  row["date"],
            "ndvi":  row.get("ndvi", {}).get("mean"),
            "ndwi":  row.get("ndwi", {}).get("mean"),
            "evi":   row.get("evi",  {}).get("mean"),
            "health_color": row.get("health", {}).get("color"),
        }
        for row in series
    ]

    return jsonify({
        "field_id":   field.id,
        "field_name": field.name,
        "crop":       field.crop,
        "series":     chart_series,
        "trend":      compute_trend(series),
    })


# ── GET /api/satellite/fields/<field_id>/summary ──────────────────────────────

@satellite_bp.route("/fields/<int:field_id>/summary", methods=["GET"])
@jwt_required()
def get_summary(field_id):
    """Return season summary stats (peak NDVI, trend, alerts)."""
    user_id = get_jwt_identity()
    field   = db.session.get(Field, field_id)

    if not field or field.user_id != user_id:
        return jsonify({"error": "Field not found"}), 404

    cached = (
        db.session.query(SatelliteCache)
        .filter(SatelliteCache.field_id == field_id)
        .order_by(SatelliteCache.date.asc())
        .all()
    )

    if not cached:
        return jsonify({"error": "No satellite data yet. Run a health check first."}), 404

    series = [row.to_dict() for row in cached]
    summary = get_season_summary(series)
    summary["field_id"]   = field.id
    summary["field_name"] = field.name
    summary["crop"]       = field.crop
    return jsonify(summary)
