CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);

CREATE TABLE crops (
    crop_id SERIAL PRIMARY KEY,
    crop_name VARCHAR(100) UNIQUE NOT NULL,
    scientific_name VARCHAR(150),
    nitrogen_req INT NOT NULL,
    phosphorus_req INT NOT NULL,
    potassium_req INT NOT NULL,
    ideal_ph_min NUMERIC(3,1),
    ideal_ph_max NUMERIC(3,1)
);

INSERT INTO crops VALUES
(DEFAULT,'Wheat','Triticum aestivum',120,60,40,6.0,7.5),
(DEFAULT,'Rice','Oryza sativa',100,50,50,5.5,7.0),
(DEFAULT,'Maize','Zea mays',150,70,60,5.8,7.5);

CREATE TABLE fertilizers (
    fertilizer_id SERIAL PRIMARY KEY,
    fertilizer_name VARCHAR(100) UNIQUE NOT NULL,
    composition VARCHAR(50),
    application_guidelines TEXT,
    unit VARCHAR(20) DEFAULT 'kg/ha'
);

INSERT INTO fertilizers VALUES
(DEFAULT,'Urea','46-0-0','Apply in split doses'),
(DEFAULT,'DAP','18-46-0','Apply during soil preparation'),
(DEFAULT,'NPK 15-15-15','15-15-15','Apply evenly before irrigation');

CREATE TABLE recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    crop_id INT REFERENCES crops(crop_id),
    fertilizer_id INT REFERENCES fertilizers(fertilizer_id),
    nitrogen NUMERIC(6,2) NOT NULL,
    phosphorus NUMERIC(6,2) NOT NULL,
    potassium NUMERIC(6,2) NOT NULL,
    ph NUMERIC(3,1) NOT NULL,
    recommended_quantity NUMERIC(8,2) NOT NULL,
    confidence_score NUMERIC(5,2),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendations_user ON recommendations(user_id);
CREATE INDEX idx_recommendations_date ON recommendations(created_at);

CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE TABLE password_reset_tokens (
    token_id UUID PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    admin_id INT REFERENCES users(user_id),
    action TEXT NOT NULL,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ml_models (
    model_id SERIAL PRIMARY KEY,
    model_name VARCHAR(100),
    version VARCHAR(50),
    accuracy NUMERIC(5,2),
    trained_on TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);