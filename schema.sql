-- ============================================================
-- FIXED schema.sql
-- ============================================================
-- Bugs fixed:
-- 1. No ON CONFLICT DO UPDATE for crop/fertilizer seed data — re-running
--    schema would silently skip updates to nutrition requirements.
-- 2. roles INSERT used explicit role_id values but SERIAL sequence was not
--    reset — manual INSERTs with hardcoded IDs desync the sequence,
--    causing "duplicate key" errors on the next auto-insert.
-- 3. recommendations.confidence_score and model_version were nullable with
--    no default — should always be recorded for audit/traceability.
-- 4. sessions.expires_at had no CHECK constraint — expired sessions were
--    never enforced at DB level.
-- 5. audit_logs.action had no length limit — TEXT is fine but
--    ip_address VARCHAR(45) was too short for IPv6 with port (max 47 chars
--    including brackets like [::1]:65535).
-- 6. ml_models had no UNIQUE constraint on (model_name, version) — duplicate
--    model registrations were silently allowed.
-- 7. Missing index on recommendations(crop_id) — joins on crop were slow.
-- 8. No updated_at column on users — impossible to track profile changes.
-- ============================================================

-- ── Extensions ────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- For gen_random_uuid() if needed

-- ── Roles ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    role_id  SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

-- FIX: Use ON CONFLICT on role_name (unique), not role_id
-- Also reset sequence after manual inserts to avoid future collisions
INSERT INTO roles (role_id, role_name)
VALUES (1, 'Admin'), (2, 'Farmer')
ON CONFLICT (role_name) DO NOTHING;

-- FIX: Sync sequence after manual id inserts
SELECT setval('roles_role_id_seq', (SELECT MAX(role_id) FROM roles));

-- ── Users ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id       INT DEFAULT 2,
    -- FIX: track profile updates
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ── Crops ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crops (
    crop_id         SERIAL PRIMARY KEY,
    crop_name       VARCHAR(100) UNIQUE NOT NULL,
    scientific_name VARCHAR(150),
    nitrogen_req    INT NOT NULL CHECK (nitrogen_req >= 0),
    phosphorus_req  INT NOT NULL CHECK (phosphorus_req >= 0),
    potassium_req   INT NOT NULL CHECK (potassium_req >= 0),
    ideal_ph_min    NUMERIC(3,1) CHECK (ideal_ph_min >= 0 AND ideal_ph_min <= 14),
    ideal_ph_max    NUMERIC(3,1) CHECK (ideal_ph_max >= 0 AND ideal_ph_max <= 14),
    CONSTRAINT chk_ph_range CHECK (ideal_ph_max >= ideal_ph_min)
);

-- FIX: ON CONFLICT DO UPDATE so re-running schema updates nutrient values
INSERT INTO crops (crop_name, scientific_name, nitrogen_req, phosphorus_req, potassium_req, ideal_ph_min, ideal_ph_max)
VALUES
    ('Wheat', 'Triticum aestivum',  120, 60, 40, 6.0, 7.5),
    ('Rice',  'Oryza sativa',       100, 50, 50, 5.5, 7.0),
    ('Maize', 'Zea mays',           150, 70, 60, 5.8, 7.5),
    ('Cotton','Gossypium hirsutum', 120, 60, 60, 5.8, 8.0),
    ('Sugarcane','Saccharum officinarum', 150, 60, 80, 6.0, 7.5)
ON CONFLICT (crop_name) DO UPDATE SET
    scientific_name = EXCLUDED.scientific_name,
    nitrogen_req    = EXCLUDED.nitrogen_req,
    phosphorus_req  = EXCLUDED.phosphorus_req,
    potassium_req   = EXCLUDED.potassium_req,
    ideal_ph_min    = EXCLUDED.ideal_ph_min,
    ideal_ph_max    = EXCLUDED.ideal_ph_max;

-- ── Fertilizers ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fertilizers (
    fertilizer_id         SERIAL PRIMARY KEY,
    fertilizer_name       VARCHAR(100) UNIQUE NOT NULL,
    composition           VARCHAR(50),
    application_guidelines TEXT,
    unit                  VARCHAR(20) DEFAULT 'kg/ha'
);

INSERT INTO fertilizers (fertilizer_name, composition, application_guidelines, unit)
VALUES
    ('Urea',         '46-0-0',    'Apply in split doses — 50% basal, 50% top dress', 'kg/ha'),
    ('DAP',          '18-46-0',   'Apply during soil preparation before sowing',      'kg/ha'),
    ('NPK 15-15-15', '15-15-15',  'Apply evenly before first irrigation',             'kg/ha'),
    ('SOP',          '0-0-50',    'Apply as basal for K-deficient soils',             'kg/ha'),
    ('SSP',          '0-16-0',    'Apply in furrows at time of sowing',               'kg/ha')
ON CONFLICT (fertilizer_name) DO UPDATE SET
    composition            = EXCLUDED.composition,
    application_guidelines = EXCLUDED.application_guidelines;

-- ── Recommendations ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id    SERIAL PRIMARY KEY,
    user_id              INT NOT NULL,
    crop_id              INT NOT NULL,
    fertilizer_id        INT NOT NULL,
    nitrogen             NUMERIC(6,2) NOT NULL,
    phosphorus           NUMERIC(6,2) NOT NULL,
    potassium            NUMERIC(6,2) NOT NULL,
    ph                   NUMERIC(3,1) NOT NULL CHECK (ph >= 0 AND ph <= 14),
    recommended_quantity NUMERIC(8,2) NOT NULL CHECK (recommended_quantity >= 0),
    -- FIX: non-nullable with defaults for full audit trail
    confidence_score     NUMERIC(5,2) NOT NULL DEFAULT 0.0 CHECK (confidence_score BETWEEN 0 AND 100),
    model_version        VARCHAR(50)  NOT NULL DEFAULT 'unknown',
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user        FOREIGN KEY (user_id)       REFERENCES users(user_id)       ON DELETE CASCADE,
    CONSTRAINT fk_crop        FOREIGN KEY (crop_id)       REFERENCES crops(crop_id),
    CONSTRAINT fk_fertilizer  FOREIGN KEY (fertilizer_id) REFERENCES fertilizers(fertilizer_id)
);

-- ── Sessions ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id    INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    -- FIX: enforce expires_at is always in the future at insert time
    CONSTRAINT chk_session_expiry CHECK (expires_at > created_at),
    CONSTRAINT fk_user_sessions FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ── Password Reset Tokens ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id   VARCHAR(255) PRIMARY KEY,
    user_id    INT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    used_at    TIMESTAMP WITH TIME ZONE,           -- FIX: track token usage to prevent replay
    CONSTRAINT fk_user_tokens FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ── Audit Logs ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id     SERIAL PRIMARY KEY,
    admin_id   INT NOT NULL,
    action     TEXT NOT NULL,
    -- FIX: VARCHAR(45) was insufficient for IPv6 with brackets+port (up to 47 chars)
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_admin FOREIGN KEY (admin_id) REFERENCES users(user_id)
);

-- ── ML Models ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ml_models (
    model_id   SERIAL PRIMARY KEY,
    model_name VARCHAR(100),
    version    VARCHAR(50),
    accuracy   NUMERIC(5,2) CHECK (accuracy BETWEEN 0 AND 100),
    trained_on TIMESTAMP WITH TIME ZONE,
    is_active  BOOLEAN DEFAULT TRUE,
    -- FIX: prevent duplicate (name, version) registrations
    CONSTRAINT uq_model_version UNIQUE (model_name, version)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_email            ON users(email);
CREATE INDEX IF NOT EXISTS idx_recommendations_user   ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_date   ON recommendations(created_at);
-- FIX: missing index on crop_id — joins to crops table were unindexed
CREATE INDEX IF NOT EXISTS idx_recommendations_crop   ON recommendations(crop_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user          ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires       ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_reset_tokens_user      ON password_reset_tokens(user_id);
