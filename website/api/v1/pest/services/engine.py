"""
website/api/v1/pest/services/engine.py
=====================================
Weather-driven pest & disease risk scoring engine for Pakistan crops.
"""

import requests
import requests_cache
from retry_requests import retry
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ── Open-Meteo client with caching (1-hour TTL) ───────────────────────────────
_cache_session  = requests_cache.CachedSession(".om_cache", expire_after=3600)
_retry_session  = retry(_cache_session, retries=5, backoff_factor=0.2)

OM_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class PestRisk:
    pest_name: str          # e.g. "Yellow Rust"
    crop:      str          # e.g. "Wheat"
    score:     float        # 0–100
    severity:  str          # "Low" | "Medium" | "High" | "Critical"
    triggered_by: list[str] # which weather conditions fired
    urdu_name:    str       # Urdu label for display
    treatment:    str       # recommended action
    pesticide:    str       # recommended product (generic name)


@dataclass
class WeatherWindow:
    """Summarised weather stats over the forecast window."""
    temp_min:     float
    temp_max:     float
    temp_mean:    float
    rh_mean:      float      # relative humidity %
    rh_max:       float
    rain_total_mm: float
    leaf_wet_hrs: int        # hours with RH > 90 (proxy for leaf wetness)
    warm_humid_hrs: int      # hours with temp 15–25 °C AND RH > 75 %
    consecutive_humid_days: int  # days with RH_mean > 80 %


# ── Weather fetcher ───────────────────────────────────────────────────────────

def fetch_weather(lat: float, lon: float, days: int = 7) -> WeatherWindow:
    """
    Pull hourly forecast from Open-Meteo and collapse into a WeatherWindow.
    """
    params = {
        "latitude":       lat,
        "longitude":      lon,
        "hourly":         [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
        ],
        "forecast_days":  days,
        "timezone":       "Asia/Karachi",
    }

    resp = _retry_session.get(OM_FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    hourly = data["hourly"]
    df = pd.DataFrame({
        "temp":  hourly["temperature_2m"],
        "rh":    hourly["relative_humidity_2m"],
        "rain":  hourly["precipitation"],
    })

    # Daily RH means for consecutive-day calculation
    df["day"]    = [t[:10] for t in hourly["time"]]
    daily_rh     = df.groupby("day")["rh"].mean()
    humid_days   = int((daily_rh > 80).sum())

    return WeatherWindow(
        temp_min              = float(df["temp"].min()),
        temp_max              = float(df["temp"].max()),
        temp_mean             = float(df["temp"].mean()),
        rh_mean               = float(df["rh"].mean()),
        rh_max                = float(df["rh"].max()),
        rain_total_mm         = float(df["rain"].sum()),
        leaf_wet_hrs          = int((df["rh"] > 90).sum()),
        warm_humid_hrs        = int(((df["temp"].between(15, 25)) & (df["rh"] > 75)).sum()),
        consecutive_humid_days= humid_days,
    )


# ── Risk rules ────────────────────────────────────────────────────────────────

class RiskRules:

    @staticmethod
    def wheat_yellow_rust(w: WeatherWindow):
        score = 0; triggers = []
        if w.temp_mean < 16:
            score += 35; triggers.append(f"Cool avg temp ({w.temp_mean:.1f}°C < 16°C)")
        if w.rh_mean > 80:
            score += 30; triggers.append(f"High avg humidity ({w.rh_mean:.0f}% > 80%)")
        if w.leaf_wet_hrs > 24:
            score += 20; triggers.append(f"Long leaf wetness ({w.leaf_wet_hrs}h > 24h)")
        if w.rain_total_mm > 10:
            score += 15; triggers.append(f"Rain forecast ({w.rain_total_mm:.0f}mm > 10mm)")
        return min(score, 100), triggers

    @staticmethod
    def wheat_brown_rust(w: WeatherWindow):
        score = 0; triggers = []
        if 14 <= w.temp_mean <= 23:
            score += 35; triggers.append(f"Optimal rust temp ({w.temp_mean:.1f}°C in 14–23°C)")
        if w.rh_mean > 75:
            score += 30; triggers.append(f"High humidity ({w.rh_mean:.0f}% > 75%)")
        if w.leaf_wet_hrs > 18:
            score += 20; triggers.append(f"Leaf wetness ({w.leaf_wet_hrs}h > 18h)")
        if w.rain_total_mm > 5:
            score += 15; triggers.append(f"Rain ({w.rain_total_mm:.0f}mm > 5mm)")
        return min(score, 100), triggers

    @staticmethod
    def rice_blast(w: WeatherWindow):
        score = 0; triggers = []
        if w.warm_humid_hrs > 10:
            score += 45; triggers.append(f"Warm+humid hours ({w.warm_humid_hrs}h)")
        if w.rh_max > 90:
            score += 30; triggers.append(f"Peak humidity ({w.rh_max:.0f}% > 90%)")
        if w.consecutive_humid_days >= 3:
            score += 25; triggers.append(f"Persistent humidity ({w.consecutive_humid_days} days)")
        return min(score, 100), triggers

    @staticmethod
    def cotton_whitefly(w: WeatherWindow):
        score = 0; triggers = []
        if w.temp_max > 35:
            score += 40; triggers.append(f"Hot max temp ({w.temp_max:.0f}°C > 35°C)")
        if w.rh_mean < 50:
            score += 30; triggers.append(f"Low humidity ({w.rh_mean:.0f}% < 50%)")
        if w.rain_total_mm < 5:
            score += 20; triggers.append(f"Dry spell ({w.rain_total_mm:.0f}mm rain)")
        if w.temp_mean > 30:
            score += 10; triggers.append(f"Warm avg temp ({w.temp_mean:.0f}°C > 30°C)")
        return min(score, 100), triggers

    @staticmethod
    def locust_risk(w: WeatherWindow):
        score = 0; triggers = []
        if w.rain_total_mm > 25:
            score += 50; triggers.append(f"Heavy rain ({w.rain_total_mm:.0f}mm > 25mm)")
        if 24 <= w.temp_mean <= 36:
            score += 35; triggers.append(f"Breeding temp ({w.temp_mean:.1f}°C in 24–36°C)")
        if w.rh_mean > 60:
            score += 15; triggers.append(f"Moderate humidity ({w.rh_mean:.0f}%)")
        return min(score, 100), triggers

    @staticmethod
    def maize_fall_armyworm(w: WeatherWindow):
        score = 0; triggers = []
        if 19 <= w.temp_mean <= 31:
            score += 40; triggers.append(f"FAW-optimal temp ({w.temp_mean:.1f}°C)")
        if w.rh_mean > 65:
            score += 30; triggers.append(f"Humid conditions ({w.rh_mean:.0f}%)")
        if w.rain_total_mm > 15:
            score += 30; triggers.append(f"Rain ({w.rain_total_mm:.0f}mm > 15mm)")
        return min(score, 100), triggers

    @staticmethod
    def sugarcane_red_rot(w: WeatherWindow):
        score = 0; triggers = []
        if w.temp_mean > 25 and w.rh_mean > 70:
            score += 50; triggers.append(f"Warm+humid ({w.temp_mean:.0f}°C, {w.rh_mean:.0f}%)")
        if w.rain_total_mm > 20:
            score += 30; triggers.append(f"Heavy rain ({w.rain_total_mm:.0f}mm)")
        if w.leaf_wet_hrs > 20:
            score += 20; triggers.append(f"Long leaf wetness ({w.leaf_wet_hrs}h)")
        return min(score, 100), triggers


# ── Pest catalogue (linked to rules) ──────────────────────────────────────────

PEST_CATALOGUE = [
    {
        "crop":       "Wheat",
        "pest_name":  "Yellow Rust",
        "urdu_name":  "پیلی کنگی",
        "rule":       RiskRules.wheat_yellow_rust,
        "treatment":  "Spray Propiconazole (Tilt 250 EC) at first sign. Inspect fields daily.",
        "pesticide":  "Propiconazole 25% EC — 500ml/acre",
    },
    {
        "crop":       "Wheat",
        "pest_name":  "Brown Rust",
        "urdu_name":  "بھوری کنگی",
        "rule":       RiskRules.wheat_brown_rust,
        "treatment":  "Apply Tebuconazole (Folicur) at tillering stage if infection spotted.",
        "pesticide":  "Tebuconazole 25% WG — 200g/acre",
    },
    {
        "crop":       "Rice",
        "pest_name":  "Rice Blast",
        "urdu_name":  "بلاسٹ بیماری",
        "rule":       RiskRules.rice_blast,
        "treatment":  "Spray Tricyclazole or Isoprothiolane at boot/heading stage.",
        "pesticide":  "Tricyclazole 75% WP — 80g/acre",
    },
    {
        "crop":       "Cotton",
        "pest_name":  "Whitefly",
        "urdu_name":  "سفید مکھی",
        "rule":       RiskRules.cotton_whitefly,
        "treatment":  "Use neem-based spray early. For severe: Imidacloprid or Spiromesifen.",
        "pesticide":  "Imidacloprid 200 SL — 125ml/acre",
    },
    {
        "crop":       "All",
        "pest_name":  "Desert Locust",
        "urdu_name":  "ٹڈی دل",
        "rule":       RiskRules.locust_risk,
        "treatment":  "Report sighting to Dept of Plant Protection immediately. Do NOT spray alone.",
        "pesticide":  "Chlorpyrifos (contact your district agriculture officer)",
    },
    {
        "crop":       "Maize",
        "pest_name":  "Fall Armyworm",
        "urdu_name":  "فال آرمی ورم",
        "rule":       RiskRules.maize_fall_armyworm,
        "treatment":  "Scout early. Spinosad or Emamectin benzoate for larvae in whorl stage.",
        "pesticide":  "Emamectin Benzoate 1.9% EC — 400ml/acre",
    },
    {
        "crop":       "Sugarcane",
        "pest_name":  "Red Rot",
        "urdu_name":  "سرخ سڑن",
        "rule":       RiskRules.sugarcane_red_rot,
        "treatment":  "Use disease-free setts. Apply Carbendazim drench at planting.",
        "pesticide":  "Carbendazim 50% WP — 1g/litre water",
    },
]


def _severity(score: float) -> str:
    if score >= 75: return "Critical"
    if score >= 50: return "High"
    if score >= 25: return "Medium"
    return "Low"


# ── Main public API ───────────────────────────────────────────────────────────

def assess_risk(
    lat: float,
    lon: float,
    crop: str,
    forecast_days: int = 7,
) -> list[PestRisk]:
    try:
        weather = fetch_weather(lat, lon, days=forecast_days)
    except Exception as e:
        logger.error(f"Weather fetch failed for ({lat},{lon}): {e}")
        raise

    results = []
    for entry in PEST_CATALOGUE:
        if entry["crop"] not in (crop, "All"):
            continue
        score, triggers = entry["rule"](weather)
        results.append(PestRisk(
            pest_name    = entry["pest_name"],
            crop         = entry["crop"],
            score        = round(score, 1),
            severity     = _severity(score),
            triggered_by = triggers,
            urdu_name    = entry["urdu_name"],
            treatment    = entry["treatment"],
            pesticide    = entry["pesticide"],
        ))

    results.sort(key=lambda r: r.score, reverse=True)
    return results


def get_high_risk_alerts(
    lat: float,
    lon: float,
    crop: str,
    threshold: int = 50,
) -> list[PestRisk]:
    return [r for r in assess_risk(lat, lon, crop) if r.score >= threshold]
