-- ============================================================
-- satellite_schema.sql — add to existing schema.sql
-- ============================================================

-- Enable PostGIS (run once per database)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Field boundaries
CREATE TABLE IF NOT EXISTS fields (
    id            SERIAL PRIMARY KEY,
    user_id       INT NOT NULL,
    name          VARCHAR(100) NOT NULL,
    crop          VARCHAR(50),
    area_ha       NUMERIC(8,3),
    season_start  TIMESTAMP WITH TIME ZONE,
    boundary      geometry(POLYGON, 4326) NOT NULL,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_field_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Spatial index on boundary (critical for intersection queries)
CREATE INDEX IF NOT EXISTS idx_fields_boundary ON fields USING GIST (boundary);
CREATE INDEX IF NOT EXISTS idx_fields_user     ON fields (user_id);

-- NDVI/NDWI/EVI statistics cache
CREATE TABLE IF NOT EXISTS satellite_cache (
    id           SERIAL PRIMARY KEY,
    field_id     INT NOT NULL,
    date         VARCHAR(10) NOT NULL,
    ndvi_mean    NUMERIC(6,4),
    ndvi_std     NUMERIC(6,4),
    ndvi_min     NUMERIC(6,4),
    ndvi_max     NUMERIC(6,4),
    ndwi_mean    NUMERIC(6,4),
    evi_mean     NUMERIC(6,4),
    cloud_pct    NUMERIC(5,1),
    health_label VARCHAR(20),
    health_color VARCHAR(10),
    full_stats_json JSONB,
    fetched_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_satcache_field FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE,
    CONSTRAINT uq_satcache_field_date UNIQUE (field_id, date)
);

CREATE INDEX IF NOT EXISTS idx_satcache_field_date ON satellite_cache (field_id, date);
