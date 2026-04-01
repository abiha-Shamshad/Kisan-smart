# Satellite Field Health Monitoring — Integration Guide

## Files delivered
```
satellite/
  services/
    satellite_service.py    ← Sentinel Hub NDVI/NDWI/EVI + trend engine
    satellite_scheduler.py  ← Celery weekly auto-check + alerts
  models/
    field_models.py         ← SQLAlchemy + PostGIS ORM models
  routes/
    satellite.py            ← Flask Blueprint (6 API endpoints)
  templates/
    satellite_dashboard.html ← Leaflet map + Chart.js dashboard
  tests/
    test_satellite_service.py ← 18 pytest tests (all mocked)
  satellite_schema.sql      ← PostGIS schema additions
```

---

## Step 1 — Enable PostGIS in your database
```bash
psql -U postgres -d kisan_smart -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U postgres -d kisan_smart -f satellite_schema.sql
```

## Step 2 — Install dependencies
```bash
pip install sentinelhub geoalchemy2 shapely --break-system-packages
```

## Step 3 — Get free Sentinel Hub credentials
1. Register at https://dataspace.copernicus.eu (free)
2. Go to: Dashboard → User Settings → OAuth Clients → New Client
3. Copy Client ID and Client Secret

## Step 4 — Add to .env
```env
SENTINEL_HUB_CLIENT_ID=your-client-id-here
SENTINEL_HUB_CLIENT_SECRET=your-client-secret-here
```

## Step 5 — Register Blueprint in create_app()
```python
from routes.satellite import satellite_bp
app.register_blueprint(satellite_bp, url_prefix='/api/satellite')
```

## Step 6 — Run tests
```bash
pytest tests/test_satellite_service.py -v
# Expected: 18 passed
```

## Step 7 — Start weekly scheduler (optional)
```bash
# Add to your existing Celery worker command:
celery -A services.satellite_scheduler worker --beat --loglevel=info
```

---

## API Endpoints

### POST /api/satellite/fields
Save a drawn field boundary.
```json
{
  "name": "Home Field",
  "crop": "Wheat",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[74.1, 32.5], [74.2, 32.5], [74.2, 32.6], [74.1, 32.6], [74.1, 32.5]]]
  }
}
```

### GET /api/satellite/fields
Returns all fields as GeoJSON FeatureCollection.

### GET /api/satellite/fields/{id}/health
Returns latest NDVI, NDWI, EVI stats. Cached for 7 days.

### GET /api/satellite/fields/{id}/timeseries?days=90
Returns 90-day time series for Chart.js rendering + trend analysis.

### GET /api/satellite/fields/{id}/summary
Returns season peak NDVI, mean, trend, and alert status.

---

## How the satellite data pipeline works

```
Farmer draws polygon on Leaflet map
        ↓
GeoJSON polygon saved to PostGIS (fields table)
        ↓
Flask calls Sentinel Hub Statistical API
  - evalscript runs IN THE CLOUD on Sentinel Hub servers
  - Computes NDVI, NDWI, EVI per 10m pixel inside the polygon
  - Returns only statistics (mean, std, min, max) — not raw imagery
  - Cloud masking applied (max 20% cloud coverage)
        ↓
Results cached in satellite_cache table (7-day TTL)
        ↓
Frontend renders Chart.js time series + colours field polygon by health
        ↓
Celery Beat job repeats every Monday at 5 AM PKT
  - Alerts farmer via push/WhatsApp if NDVI drops >20% from peak
```

---

## Processing Unit budget (free tier: 30,000 PU/month)

| Operation | PU cost | Notes |
|-----------|---------|-------|
| 10-day NDVI stats for 1ha field | ~15 PU | 10m res × 1ha |
| 10-day NDVI stats for 5ha field | ~75 PU | |
| Weekly check, 1 field, 1 year | ~780 PU/year | Very affordable |
| 100 fields × weekly | 78,000 PU/year | Need paid tier |

Free tier supports ~38 fields with weekly checks.
For more, upgrade to Sentinel Hub Basic (~€25/month = unlimited fields).

---

## Satellite indices explained (for farmers)

| Index | What it measures | Healthy range |
|-------|-----------------|---------------|
| NDVI  | Vegetation density and health | 0.4–0.9 |
| NDWI  | Water content in leaves | 0.0–0.5 |
| EVI   | Better NDVI for dense crops | 0.3–0.8 |

NDVI < 0.3 for a wheat field = action needed.
NDWI < -0.1 = water stress — irrigate soon.

---

## Sentinel-2 revisit time for Pakistan

Pakistan falls under Sentinel-2 tiles 43RCP, 43RCQ, 43RDQ (Punjab region).
Revisit time: approximately every 5 days.
So you get 6 cloud-free observations per month in clear weather.
During monsoon (July–September), expect 1–2 usable observations/month.
