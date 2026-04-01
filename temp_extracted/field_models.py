"""
models/field_models.py
=======================
SQLAlchemy ORM models for field boundaries and satellite index cache.

Requires:
  - PostgreSQL with PostGIS extension enabled
  - pip install geoalchemy2 shapely psycopg2-binary

DB setup (run once):
  psql -U postgres -d kisan_smart -c "CREATE EXTENSION IF NOT EXISTS postgis;"
"""

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean,
    DateTime, ForeignKey, JSON, Index,
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape, from_shape
from shapely.geometry import mapping, shape as sh_shape

from website import db          # your existing Flask-SQLAlchemy instance


class Field(db.Model):
    """
    A farmer's field — stores the boundary polygon as PostGIS geometry.
    One farmer can have multiple fields (e.g. different plots).
    """
    __tablename__ = "fields"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    name        = Column(String(100), nullable=False)          # "Home Field", "North Plot"
    crop        = Column(String(50))                           # "Wheat", "Rice", etc.
    area_ha     = Column(Float)                                # auto-computed from geometry
    season_start = Column(DateTime(timezone=True))             # when monitoring started

    # PostGIS geometry column — stores the drawn polygon in WGS84
    # SRID 4326 = standard lat/lng coordinate system
    boundary    = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))
    is_active   = Column(Boolean, default=True)

    # Relationships
    owner       = relationship("User", backref="fields")
    ndvi_cache  = relationship("SatelliteCache", backref="field",
                               cascade="all, delete-orphan",
                               order_by="SatelliteCache.date.desc()")

    __table_args__ = (
        Index("idx_fields_user",     "user_id"),
        Index("idx_fields_boundary", "boundary", postgresql_using="gist"),
    )

    def to_geojson(self) -> dict:
        """Return field as a GeoJSON Feature."""
        geom = to_shape(self.boundary)
        return {
            "type":     "Feature",
            "geometry": mapping(geom),
            "properties": {
                "id":      self.id,
                "name":    self.name,
                "crop":    self.crop,
                "area_ha": self.area_ha,
            },
        }

    @classmethod
    def from_geojson(cls, user_id: int, name: str, crop: str,
                     geojson_geometry: dict) -> "Field":
        """Create a Field instance from a GeoJSON geometry dict."""
        shapely_geom = sh_shape(geojson_geometry)

        # Compute area in hectares using a rough approximation
        # (accurate enough for field-scale use in Pakistan)
        # For production, use pyproj with local UTM projection
        bounds  = shapely_geom.bounds
        lat_mid = (bounds[1] + bounds[3]) / 2
        import math
        lat_rad   = math.radians(lat_mid)
        m_per_deg_lon = 111320 * math.cos(lat_rad)
        m_per_deg_lat = 111320.0

        area_deg2 = shapely_geom.area
        area_m2   = area_deg2 * m_per_deg_lon * m_per_deg_lat
        area_ha   = round(area_m2 / 10000, 3)

        return cls(
            user_id  = user_id,
            name     = name,
            crop     = crop,
            area_ha  = area_ha,
            boundary = from_shape(shapely_geom, srid=4326),
        )

    def get_geojson_polygon(self) -> dict:
        """Return just the geometry dict (for Sentinel Hub requests)."""
        return mapping(to_shape(self.boundary))


class SatelliteCache(db.Model):
    """
    Cached satellite index statistics per field per date.
    Prevents repeated API calls for already-fetched data.
    Cache is valid for 7 days (new Sentinel-2 pass every 3–5 days).
    """
    __tablename__ = "satellite_cache"

    id        = Column(Integer, primary_key=True)
    field_id  = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False)
    date      = Column(String(10), nullable=False)          # "YYYY-MM-DD"

    # Vegetation indices (mean values over field polygon)
    ndvi_mean = Column(Float)
    ndvi_std  = Column(Float)
    ndvi_min  = Column(Float)
    ndvi_max  = Column(Float)

    ndwi_mean = Column(Float)
    evi_mean  = Column(Float)

    cloud_pct = Column(Float)           # % cloudy pixels in acquisition
    health_label = Column(String(20))   # "Good", "Moderate", etc.
    health_color = Column(String(10))   # "#5cb85c"

    # Full stats JSON for percentiles and per-index details
    full_stats_json = Column(JSON)

    fetched_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_satcache_field_date", "field_id", "date"),
    )

    def is_stale(self, max_age_days: int = 7) -> bool:
        """Returns True if this cache entry is older than max_age_days."""
        if not self.fetched_at:
            return True
        age = datetime.now(timezone.utc) - self.fetched_at
        return age.days > max_age_days

    def to_dict(self) -> dict:
        return {
            "date":        self.date,
            "ndvi":        {"mean": self.ndvi_mean, "std": self.ndvi_std,
                            "min":  self.ndvi_min,  "max": self.ndvi_max},
            "ndwi":        {"mean": self.ndwi_mean},
            "evi":         {"mean": self.evi_mean},
            "cloud_pct":   self.cloud_pct,
            "health":      {"label": self.health_label, "color": self.health_color},
        }
