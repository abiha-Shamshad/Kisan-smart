"""
tests/test_satellite_service.py
================================
Unit tests for satellite service — all Sentinel Hub calls mocked.
Run: pytest tests/test_satellite_service.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from services.satellite_service import (
    classify_ndvi, compute_trend, get_season_summary,
    _parse_stats_response, NDVI_CLASSES,
)


# ── NDVI Classification ───────────────────────────────────────────────────────

class TestClassifyNDVI:
    def test_excellent(self):
        r = classify_ndvi(0.75)
        assert r["label"] == "Excellent"
        assert r["color"] == "#1a7c1a"

    def test_good(self):
        assert classify_ndvi(0.55)["label"] == "Good"

    def test_moderate(self):
        assert classify_ndvi(0.40)["label"] == "Moderate"

    def test_poor(self):
        assert classify_ndvi(0.15)["label"] == "Poor"

    def test_bare_stress(self):
        assert classify_ndvi(0.05)["label"]  == "Bare/Stress"
        assert classify_ndvi(-0.2)["label"]  == "Bare/Stress"

    def test_boundary_values(self):
        assert classify_ndvi(0.7)["label"] == "Excellent"
        assert classify_ndvi(0.5)["label"] == "Good"
        assert classify_ndvi(0.3)["label"] == "Moderate"
        assert classify_ndvi(0.1)["label"] == "Poor"


# ── Trend computation ─────────────────────────────────────────────────────────

def _make_series(ndvi_vals, dates=None):
    if dates is None:
        dates = [f"2025-03-{i+1:02d}" for i in range(len(ndvi_vals))]
    return [
        {"date": d, "ndvi": {"mean": v, "std": 0.05, "min": v-0.1, "max": v+0.1}}
        for d, v in zip(dates, ndvi_vals)
    ]


class TestComputeTrend:
    def test_improving(self):
        series = _make_series([0.3, 0.4, 0.5, 0.6])
        r = compute_trend(series)
        assert r["trend"] == "improving"
        assert r["change_pct"] > 0

    def test_declining(self):
        series = _make_series([0.7, 0.6, 0.5, 0.4])
        r = compute_trend(series)
        assert r["trend"] == "declining"
        assert r["change_pct"] < 0

    def test_stable(self):
        series = _make_series([0.55, 0.56, 0.55, 0.57])
        r = compute_trend(series)
        assert r["trend"] == "stable"

    def test_alert_on_peak_drop(self):
        # Peak was 0.7, now 0.4 — >20% drop should trigger alert
        series = _make_series([0.4, 0.5, 0.7, 0.65, 0.6, 0.4])
        r = compute_trend(series)
        assert r["alert"] == True
        assert r["alert_msg"] is not None

    def test_no_alert_healthy(self):
        series = _make_series([0.5, 0.6, 0.65, 0.7])
        r = compute_trend(series)
        assert r["alert"] == False

    def test_insufficient_data(self):
        r = compute_trend([_make_series([0.5])[0]])
        assert r["trend"] == "insufficient_data"

    def test_empty_series(self):
        r = compute_trend([])
        assert r["trend"] == "insufficient_data"


# ── Season summary ────────────────────────────────────────────────────────────

class TestGetSeasonSummary:
    def test_peak_detection(self):
        series = _make_series(
            [0.3, 0.5, 0.7, 0.65, 0.6],
            ["2025-01-01","2025-01-11","2025-01-21","2025-02-01","2025-02-11"]
        )
        s = get_season_summary(series)
        assert s["peak_ndvi"] == 0.7
        assert s["peak_date"] == "2025-01-21"
        assert s["n_observations"] == 5

    def test_mean_ndvi(self):
        series = _make_series([0.4, 0.6])
        s = get_season_summary(series)
        assert abs(s["mean_ndvi"] - 0.5) < 0.01

    def test_empty_returns_empty(self):
        assert get_season_summary([]) == {}


# ── Response parsing ──────────────────────────────────────────────────────────

class TestParseStatsResponse:
    def _mock_response(self, ndvi_mean=0.62, ndwi_mean=-0.1, evi_mean=0.45):
        """Build a mock Sentinel Hub Statistical API response."""
        return [{
            "data": [{
                "interval": {
                    "from": "2025-03-01T00:00:00Z",
                    "to":   "2025-03-10T23:59:59Z",
                },
                "outputs": {
                    "indices": {
                        "bands": {
                            "B0": {   # NDVI
                                "statistics": {
                                    "mean":         ndvi_mean,
                                    "stDev":        0.07,
                                    "min":          ndvi_mean - 0.15,
                                    "max":          ndvi_mean + 0.15,
                                    "percentile_25": ndvi_mean - 0.1,
                                    "percentile_50": ndvi_mean,
                                    "percentile_75": ndvi_mean + 0.1,
                                    "sampleCount":  10000,
                                    "noDataCount":   500,
                                }
                            },
                            "B1": {   # NDWI
                                "statistics": {
                                    "mean": ndwi_mean, "stDev": 0.05,
                                    "min": ndwi_mean - 0.1, "max": ndwi_mean + 0.1,
                                    "sampleCount": 10000, "noDataCount": 500,
                                }
                            },
                            "B2": {   # EVI
                                "statistics": {
                                    "mean": evi_mean, "stDev": 0.06,
                                    "min": evi_mean - 0.1, "max": evi_mean + 0.1,
                                    "sampleCount": 10000, "noDataCount": 500,
                                }
                            },
                        }
                    }
                }
            }]
        }]

    def test_parses_ndvi(self):
        raw = self._mock_response(ndvi_mean=0.62)
        result = _parse_stats_response(raw)
        assert len(result) == 1
        assert result[0]["ndvi"]["mean"] == 0.62
        assert result[0]["date"] == "2025-03-01"

    def test_parses_ndwi(self):
        raw = self._mock_response(ndwi_mean=-0.1)
        result = _parse_stats_response(raw)
        assert result[0]["ndwi"]["mean"] == -0.1

    def test_health_classification_attached(self):
        raw = self._mock_response(ndvi_mean=0.65)
        result = _parse_stats_response(raw)
        assert result[0]["health"]["label"] == "Good"

    def test_cloud_pct_computed(self):
        raw = self._mock_response()
        result = _parse_stats_response(raw)
        # 500/10000 = 5%
        assert result[0]["cloud_pct"] == 5.0

    def test_empty_response(self):
        result = _parse_stats_response([{"data": []}])
        assert result == []
