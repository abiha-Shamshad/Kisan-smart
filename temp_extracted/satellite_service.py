"""
services/satellite_service.py
==============================
Sentinel-2 field health monitoring service for Kisan Smart.

Data source: Copernicus Data Space Ecosystem (CDSE) via Sentinel Hub API
Coverage:    Global, 10m resolution, 3–5 day revisit
Cost:        FREE tier — 30,000 processing units/month
             (1 field × weekly NDVI = ~52 PU/year → supports ~570 fields free)

Indices computed:
  NDVI  — Normalized Difference Vegetation Index  (B08-B04)/(B08+B04)
           Range -1 to 1. Healthy crops: 0.4–0.9
  NDWI  — Normalized Difference Water Index       (B03-B08)/(B03+B08)
           Range -1 to 1. Water stress: < 0.0
  EVI   — Enhanced Vegetation Index               2.5*(B08-B04)/(B08+6*B04-7.5*B02+1)
           Better than NDVI for dense canopy

Setup:
  1. Register free at: https://dataspace.copernicus.eu
  2. Go to User Settings → OAuth clients → Create new client
  3. Copy client_id and client_secret to .env
  pip install sentinelhub shapely
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── Sentinel Hub config ───────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_sh_config():
    """Build and cache Sentinel Hub config from environment variables."""
    try:
        from sentinelhub import SHConfig
    except ImportError:
        raise ImportError("Install sentinelhub: pip install sentinelhub")

    client_id     = os.environ.get("SENTINEL_HUB_CLIENT_ID")
    client_secret = os.environ.get("SENTINEL_HUB_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "SENTINEL_HUB_CLIENT_ID and SENTINEL_HUB_CLIENT_SECRET must be set.\n"
            "Register free at https://dataspace.copernicus.eu"
        )

    config = SHConfig()
    config.sh_client_id     = client_id
    config.sh_client_secret = client_secret
    # Use CDSE endpoint (free tier)
    config.sh_base_url = "https://sh.dataspace.copernicus.eu"
    config.sh_token_url = (
        "https://identity.dataspace.copernicus.eu"
        "/auth/realms/CDSE/protocol/openid-connect/token"
    )
    return config


# ── Evalscripts (JavaScript sent to Sentinel Hub cloud processor) ─────────────
# These run IN THE CLOUD — only statistics come back, not raw imagery.
# This is what makes the free tier viable: you pay per pixel processed,
# not per image downloaded.

EVALSCRIPT_NDVI = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "dataMask"] }],
    output: [
      { id: "ndvi",     bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1, sampleType: "UINT8" }
    ]
  };
}
function evaluatePixel(s) {
  let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + 0.0001);
  return {
    ndvi:     [ndvi],
    dataMask: [s.dataMask]
  };
}
"""

EVALSCRIPT_MULTI = """
//VERSION=3
// Computes NDVI, NDWI, EVI in a single request (saves processing units)
function setup() {
  return {
    input: [{ bands: ["B02", "B03", "B04", "B08", "dataMask"] }],
    output: [
      { id: "indices", bands: 3, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1, sampleType: "UINT8" }
    ]
  };
}
function evaluatePixel(s) {
  let eps  = 0.0001;
  let ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + eps);
  let ndwi = (s.B03 - s.B08) / (s.B03 + s.B08 + eps);
  let evi  = 2.5 * (s.B08 - s.B04) / (s.B08 + 6*s.B04 - 7.5*s.B02 + 1 + eps);
  return {
    indices:  [ndvi, ndwi, evi],
    dataMask: [s.dataMask]
  };
}
"""


# ── Index bands mapping (output band index → name) ───────────────────────────
INDEX_BANDS = {0: "ndvi", 1: "ndwi", 2: "evi"}

# ── Health classification thresholds (agronomic) ──────────────────────────────
NDVI_CLASSES = [
    (0.7,  1.0,  "Excellent",  "#1a7c1a"),
    (0.5,  0.7,  "Good",       "#5cb85c"),
    (0.3,  0.5,  "Moderate",   "#f0ad4e"),
    (0.1,  0.3,  "Poor",       "#d9534f"),
    (-1.0, 0.1,  "Bare/Stress","#8B4513"),
]

def classify_ndvi(ndvi: float) -> dict:
    for lo, hi, label, color in NDVI_CLASSES:
        if lo <= ndvi < hi:
            return {"label": label, "color": color}
    return {"label": "Unknown", "color": "#888888"}


# ── Core statistics fetcher ───────────────────────────────────────────────────

def fetch_field_stats(
    geojson_polygon: dict,
    start_date:      str,        # "YYYY-MM-DD"
    end_date:        str,        # "YYYY-MM-DD"
    max_cloud_pct:   int = 20,   # reject scenes with >20% cloud cover
    interval_days:   int = 10,   # aggregate per 10-day window
) -> list[dict]:
    """
    Fetch multi-index statistics (NDVI, NDWI, EVI) for a field polygon
    over a time range.

    Uses the Statistical API — no raw imagery downloaded, just mean/std/min/max
    per time interval. Very efficient on processing units.

    Args:
        geojson_polygon: GeoJSON Polygon or MultiPolygon dict
        start_date:      ISO date string e.g. "2025-03-01"
        end_date:        ISO date string e.g. "2025-03-28"
        max_cloud_pct:   Max cloud coverage % to include (default 20)
        interval_days:   Statistics aggregation window in days (default 10)

    Returns:
        List of dicts, one per time interval:
        [
          {
            "date":    "2025-03-01",
            "ndvi":    {"mean": 0.62, "std": 0.08, "min": 0.41, "max": 0.79},
            "ndwi":    {"mean": -0.12, ...},
            "evi":     {"mean": 0.48, ...},
            "cloud_pct": 8.2,
            "health":  {"label": "Good", "color": "#5cb85c"}
          },
          ...
        ]
    """
    try:
        from sentinelhub import (
            SentinelHubStatistical, DataCollection,
            Geometry, CRS, BBox,
        )
        from shapely.geometry import shape as sh_shape
    except ImportError:
        raise ImportError("Install sentinelhub and shapely: pip install sentinelhub shapely")

    config = _get_sh_config()

    # Convert GeoJSON polygon → Sentinel Hub Geometry
    shapely_geom = sh_shape(geojson_polygon)
    geometry = Geometry(geometry=geojson_polygon, crs=CRS.WGS84)

    # Build aggregation interval string (ISO 8601 duration)
    agg_interval = f"P{interval_days}D"

    # Construct Statistical API request
    request = SentinelHubStatistical(
        aggregation=SentinelHubStatistical.aggregation(
            evalscript       = EVALSCRIPT_MULTI,
            time_interval    = (f"{start_date}T00:00:00Z", f"{end_date}T23:59:59Z"),
            aggregation_interval = agg_interval,
            resolution       = (10, 10),    # 10m Sentinel-2 native resolution
        ),
        input_data=[
            SentinelHubStatistical.input_data(
                DataCollection.SENTINEL2_L2A.define_from(
                    name        = "s2l2a",
                    service_url = "https://sh.dataspace.copernicus.eu",
                ),
                other_args={
                    "dataFilter": {
                        "maxCloudCoverage": max_cloud_pct,
                        "mosaickingOrder":  "leastCC",   # use least-cloudy pixels
                    }
                },
            )
        ],
        geometry  = geometry,
        config    = config,
        calculations = {
            # Request full stats for each of our 3 output bands
            "indices": {
                "statistics": {
                    "default": {
                        "percentiles": {"bins": [25, 50, 75]},
                    }
                }
            }
        },
    )

    raw_data = request.get_data()
    return _parse_stats_response(raw_data)


def _parse_stats_response(raw_data: list) -> list[dict]:
    """Parse Sentinel Hub Statistical API response into clean dicts."""
    results = []

    for interval in raw_data[0].get("data", []):
        date_str = interval["interval"]["from"][:10]

        outputs = interval.get("outputs", {})
        indices_bands = outputs.get("indices", {}).get("bands", {})

        # Band names from our evalscript: B0=NDVI, B1=NDWI, B2=EVI
        band_map = {"B0": "ndvi", "B1": "ndwi", "B2": "evi"}

        entry = {"date": date_str}

        for band_key, index_name in band_map.items():
            band_stats = indices_bands.get(band_key, {}).get("statistics", {})
            if band_stats:
                entry[index_name] = {
                    "mean": round(band_stats.get("mean",  0.0), 4),
                    "std":  round(band_stats.get("stDev", 0.0), 4),
                    "min":  round(band_stats.get("min",   0.0), 4),
                    "max":  round(band_stats.get("max",   0.0), 4),
                    "p25":  round(band_stats.get("percentile_25", 0.0), 4),
                    "p50":  round(band_stats.get("percentile_50", 0.0), 4),
                    "p75":  round(band_stats.get("percentile_75", 0.0), 4),
                }

        # Add health classification from NDVI mean
        ndvi_mean = entry.get("ndvi", {}).get("mean", 0.0)
        entry["health"] = classify_ndvi(ndvi_mean)

        # Sample count as proxy for cloud coverage
        sample_count = indices_bands.get("B0", {}).get("statistics", {}).get("sampleCount", 0)
        no_data      = indices_bands.get("B0", {}).get("statistics", {}).get("noDataCount", 0)
        if sample_count > 0:
            entry["cloud_pct"] = round(no_data / sample_count * 100, 1)
        else:
            entry["cloud_pct"] = 100.0   # fully cloudy

        results.append(entry)

    # Sort chronologically
    results.sort(key=lambda x: x["date"])
    return results


# ── Trend analysis ────────────────────────────────────────────────────────────

def compute_trend(time_series: list[dict], index: str = "ndvi") -> dict:
    """
    Compute linear trend and change detection for an index time series.

    Returns:
        {
          "trend":        "improving" | "declining" | "stable",
          "change_pct":   float,        # % change from first to last observation
          "alert":        bool,         # True if significant decline detected
          "alert_msg":    str | None,
        }
    """
    values = [
        r[index]["mean"]
        for r in time_series
        if index in r and r[index]["mean"] is not None
    ]
    if len(values) < 2:
        return {"trend": "insufficient_data", "change_pct": 0.0, "alert": False, "alert_msg": None}

    first, last = values[0], values[-1]
    change_pct  = round((last - first) / (abs(first) + 1e-6) * 100, 1)

    # Trend label
    if change_pct > 5:   trend = "improving"
    elif change_pct < -10: trend = "declining"
    else:                  trend = "stable"

    # Alert: NDVI drop > 20% from season peak
    peak   = max(values)
    drop   = (peak - last) / (peak + 1e-6)
    alert  = (drop > 0.20) and (index == "ndvi")
    alert_msg = (
        f"⚠️ NDVI dropped {drop*100:.0f}% from season peak ({peak:.2f} → {last:.2f}). "
        "Check for pest damage, water stress, or disease."
    ) if alert else None

    return {
        "trend":      trend,
        "change_pct": change_pct,
        "alert":      alert,
        "alert_msg":  alert_msg,
    }


# ── Season summary ────────────────────────────────────────────────────────────

def get_season_summary(time_series: list[dict]) -> dict:
    """
    Compute growing-season summary statistics from a full NDVI time series.
    """
    ndvi_vals = [r["ndvi"]["mean"] for r in time_series if "ndvi" in r]
    if not ndvi_vals:
        return {}

    return {
        "peak_ndvi":    round(max(ndvi_vals), 3),
        "mean_ndvi":    round(sum(ndvi_vals) / len(ndvi_vals), 3),
        "min_ndvi":     round(min(ndvi_vals), 3),
        "n_observations": len(ndvi_vals),
        "peak_date":    time_series[ndvi_vals.index(max(ndvi_vals))]["date"],
        "overall_health": classify_ndvi(sum(ndvi_vals) / len(ndvi_vals)),
        "trend":        compute_trend(time_series),
    }
