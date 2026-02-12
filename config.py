import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-12345")
    # PostgreSQL Connection
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/kisan_smart"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "True") == "True"

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-key")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@kisan-smart.com")
    MAIL_SUPPRESS_SEND = True # Don't send emails during development/load tests

    # Mail Configuration
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("EMAIL_USER")
    MAIL_PASSWORD = os.environ.get("EMAIL_PASS")

    # API & Documentation
    API_TITLE = "Kisan Smart API"
    API_VERSION = "v1"
    SWAGGER_UI_DOC_EXPANSION = "list"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_kisan.db"
    WTF_CSRF_ENABLED = False
    DEBUG = True
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    MAIL_DEFAULT_SENDER = "noreply@kisan-smart.com"
    MAIL_SUPPRESS_SEND = True  # Don't actually send emails in tests
