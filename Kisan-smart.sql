-- Kisan Smart Database Schema - MySQL Compatible
CREATE DATABASE IF NOT EXISTS kisan_smart;
USE kisan_smart;

CREATE TABLE IF NOT EXISTS roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

INSERT IGNORE INTO roles (role_id, role_name) VALUES (1, 'Admin'), (2, 'Farmer');

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT DEFAULT 2,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

CREATE TABLE IF NOT EXISTS crops (
    crop_id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) UNIQUE NOT NULL,
    scientific_name VARCHAR(150),
    nitrogen_req INT NOT NULL,
    phosphorus_req INT NOT NULL,
    potassium_req INT NOT NULL,
    ideal_ph_min NUMERIC(3,1),
    ideal_ph_max NUMERIC(3,1)
);

INSERT IGNORE INTO crops (crop_name, scientific_name, nitrogen_req, phosphorus_req, potassium_req, ideal_ph_min, ideal_ph_max) VALUES
('Wheat','Triticum aestivum',120,60,40,6.0,7.5),
('Rice','Oryza sativa',100,50,50,5.5,7.0),
('Maize','Zea mays',150,70,60,5.8,7.5);

CREATE TABLE IF NOT EXISTS fertilizers (
    fertilizer_id INT AUTO_INCREMENT PRIMARY KEY,
    fertilizer_name VARCHAR(100) UNIQUE NOT NULL,
    composition VARCHAR(50),
    application_guidelines TEXT,
    unit VARCHAR(20) DEFAULT 'kg/ha'
);

INSERT IGNORE INTO fertilizers (fertilizer_name, composition, application_guidelines, unit) VALUES
('Urea','46-0-0','Apply in split doses','kg/ha'),
('DAP','18-46-0','Apply during soil preparation','kg/ha'),
('NPK 15-15-15','15-15-15','Apply evenly before irrigation','kg/ha');

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    crop_id INT NOT NULL,
    fertilizer_id INT NOT NULL,
    nitrogen NUMERIC(6,2) NOT NULL,
    phosphorus NUMERIC(6,2) NOT NULL,
    potassium NUMERIC(6,2) NOT NULL,
    ph NUMERIC(3,1) NOT NULL,
    recommended_quantity NUMERIC(8,2) NOT NULL,
    confidence_score NUMERIC(5,2),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
    FOREIGN KEY (fertilizer_id) REFERENCES fertilizers(fertilizer_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    action TEXT NOT NULL,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS ml_models (
    model_id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100),
    version VARCHAR(50),
    accuracy NUMERIC(5,2),
    trained_on TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_recommendations_user ON recommendations(user_id);
CREATE INDEX idx_recommendations_date ON recommendations(created_at);
