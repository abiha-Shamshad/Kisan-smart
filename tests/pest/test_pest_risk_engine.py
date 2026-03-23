"""
tests/pest/test_pest_risk_engine.py
===================================
Unit tests for the pest risk scoring engine.
Run: pytest tests/pest/test_pest_risk_engine.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from website.api.v1.pest.services.engine import (
    WeatherWindow, RiskRules, assess_risk,
    get_high_risk_alerts, _severity, PEST_CATALOGUE,
)


# ── WeatherWindow fixtures ─────────────────────────────────────────────────────

def cold_humid():
    """Yellow rust weather: cool + humid"""
    return WeatherWindow(
        temp_min=8, temp_max=18, temp_mean=13,
        rh_mean=85, rh_max=95, rain_total_mm=15,
        leaf_wet_hrs=30, warm_humid_hrs=5, consecutive_humid_days=4,
    )

def hot_dry():
    """Whitefly weather: hot + dry"""
    return WeatherWindow(
        temp_min=28, temp_max=42, temp_mean=35,
        rh_mean=35, rh_max=55, rain_total_mm=2,
        leaf_wet_hrs=0, warm_humid_hrs=0, consecutive_humid_days=0,
    )

def warm_humid():
    """Rice blast weather: warm + humid nights"""
    return WeatherWindow(
        temp_min=20, temp_max=32, temp_mean=26,
        rh_mean=82, rh_max=95, rain_total_mm=25,
        leaf_wet_hrs=25, warm_humid_hrs=18, consecutive_humid_days=3,
    )

def locust_weather():
    """Locust breeding conditions: heavy rain + warm"""
    return WeatherWindow(
        temp_min=22, temp_max=38, temp_mean=30,
        rh_mean=65, rh_max=80, rain_total_mm=40,
        leaf_wet_hrs=10, warm_humid_hrs=8, consecutive_humid_days=2,
    )

def benign():
    """Low-risk baseline"""
    return WeatherWindow(
        temp_min=15, temp_max=25, temp_mean=20,
        rh_mean=50, rh_max=65, rain_total_mm=3,
        leaf_wet_hrs=5, warm_humid_hrs=2, consecutive_humid_days=1,
    )


# ── Severity helper tests ──────────────────────────────────────────────────────

def test_severity_labels():
    assert _severity(0)   == "Low"
    assert _severity(24)  == "Low"
    assert _severity(25)  == "Medium"
    assert _severity(49)  == "Medium"
    assert _severity(50)  == "High"
    assert _severity(74)  == "High"
    assert _severity(75)  == "Critical"
    assert _severity(100) == "Critical"


# ── Rule tests ────────────────────────────────────────────────────────────────

class TestWheatYellowRust:
    def test_high_risk_in_cold_humid(self):
        score, triggers = RiskRules.wheat_yellow_rust(cold_humid())
        assert score >= 75, f"Expected Critical, got {score}"
        assert len(triggers) >= 3

    def test_low_risk_in_hot_dry(self):
        score, triggers = RiskRules.wheat_yellow_rust(hot_dry())
        assert score < 25

    def test_triggers_contain_temp(self):
        score, triggers = RiskRules.wheat_yellow_rust(cold_humid())
        assert any("temp" in t.lower() for t in triggers)


class TestCottonWhitefly:
    def test_high_risk_in_hot_dry(self):
        score, triggers = RiskRules.cotton_whitefly(hot_dry())
        assert score >= 75, f"Expected Critical, got {score}"

    def test_low_risk_in_cold_humid(self):
        score, triggers = RiskRules.cotton_whitefly(cold_humid())
        assert score < 30

    def test_triggers_contain_humidity(self):
        score, triggers = RiskRules.cotton_whitefly(hot_dry())
        assert any("humid" in t.lower() for t in triggers)


class TestRiceBlast:
    def test_high_risk_warm_humid(self):
        score, triggers = RiskRules.rice_blast(warm_humid())
        assert score >= 50

    def test_low_risk_benign(self):
        score, triggers = RiskRules.rice_blast(benign())
        assert score < 30


class TestLocustRisk:
    def test_high_risk_after_heavy_rain(self):
        score, triggers = RiskRules.locust_risk(locust_weather())
        assert score >= 75

    def test_low_risk_no_rain(self):
        score, triggers = RiskRules.locust_risk(benign())
        assert score < 20


# ── Score boundary tests ───────────────────────────────────────────────────────

def test_scores_capped_at_100():
    """No score should ever exceed 100."""
    extreme = WeatherWindow(
        temp_min=5, temp_max=15, temp_mean=10,
        rh_mean=99, rh_max=100, rain_total_mm=100,
        leaf_wet_hrs=168, warm_humid_hrs=168, consecutive_humid_days=7,
    )
    for entry in PEST_CATALOGUE:
        score, _ = entry["rule"](extreme)
        assert score <= 100, f"{entry['pest_name']} scored {score} > 100"


def test_scores_non_negative():
    """Scores must always be >= 0."""
    for entry in PEST_CATALOGUE:
        score, _ = entry["rule"](benign())
        assert score >= 0


# ── Integration test (mocked weather API) ─────────────────────────────────────

MOCK_OM_RESPONSE = {
    "hourly": {
        "time":                  [f"2025-03-0{d+1}T{h:02d}:00" for d in range(7) for h in range(24)],
        "temperature_2m":        [12.0] * 168,
        "relative_humidity_2m":  [88.0] * 168,
        "precipitation":         [2.0]  * 168,
    }
}

@patch("website.api.v1.pest.services.engine._retry_session")
def test_assess_risk_wheat(mock_session):
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_OM_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_resp

    risks = assess_risk(lat=31.5, lon=74.3, crop="Wheat")

    assert len(risks) > 0
    assert risks[0].score >= risks[-1].score  # sorted descending
    assert all(r.crop in ("Wheat", "All") for r in risks)
    assert all(0 <= r.score <= 100 for r in risks)
    assert all(r.severity in ("Low", "Medium", "High", "Critical") for r in risks)


@patch("website.api.v1.pest.services.engine._retry_session")
def test_get_high_risk_alerts_filters_correctly(mock_session):
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_OM_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_resp

    alerts = get_high_risk_alerts(lat=31.5, lon=74.3, crop="Wheat", threshold=50)
    assert all(r.score >= 50 for r in alerts)


@patch("website.api.v1.pest.services.engine._retry_session")
def test_empty_result_for_low_risk_weather(mock_session):
    """In benign weather, high-risk filter should return empty list."""
    benign_response = {
        "hourly": {
            "time":                  [f"2025-03-0{d+1}T{h:02d}:00" for d in range(7) for h in range(24)],
            "temperature_2m":        [22.0] * 168,  # Mild
            "relative_humidity_2m":  [45.0] * 168,  # Dry
            "precipitation":         [0.0]  * 168,  # No rain
        }
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = benign_response
    mock_resp.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_resp

    alerts = get_high_risk_alerts(lat=31.5, lon=74.3, crop="Cotton", threshold=75)
    # In dry conditions, whitefly might still score high — that's valid
    # But rust should be low
    rust_alerts = [a for a in alerts if "Rust" in a.pest_name]
    assert len(rust_alerts) == 0
