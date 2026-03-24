import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-key-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Database
    # Standard Flask-SQLAlchemy practice: if no URI provided, use SQLite in instance folder
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "True") == "True"
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # Mail
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("EMAIL_USER")
    MAIL_PASSWORD = os.environ.get("EMAIL_PASS")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@kisan-smart.com")
    MAIL_SUPPRESS_SEND = os.environ.get("FLASK_ENV", "development") != "production"

    # API
    API_TITLE = "Kisan Smart API"
    API_VERSION = "v1"
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False

class ProductionConfig(Config):
    # Enforce strong keys in production
    def __init__(self):
        if self.SECRET_KEY == "dev-key-change-me":
            raise ValueError("SECRET_KEY MUST be set in production")
        if self.JWT_SECRET_KEY == "jwt-dev-key-change-me":
            raise ValueError("JWT_SECRET_KEY MUST be set in production")

config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

def get_config(env: str = None) -> Config:
    env = env or os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
