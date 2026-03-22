"""
FIXED config.py
==============
Bugs fixed:
1. SECRET_KEY and JWT_SECRET_KEY have weak hardcoded fallbacks - raised ValueError if missing in production
2. DATABASE_URL had no fallback safety — crashes if env var missing without explanation
3. JWT_ACCESS_TOKEN_EXPIRES was an int (seconds) but Flask-JWT-Extended expects timedelta
4. SQLALCHEMY_TRACK_MODIFICATIONS warning suppressed but engine options missing (pool_pre_ping)
5. TestingConfig lacked JWT_SECRET_KEY — JWT-protected test routes would 500
6. MAIL_DEFAULT_SENDER not included in base Config properly (was duplicated)
7. No FLASK_ENV / APP_ENV distinction — debug mode could leak to production
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str, default: str = None, production_required: bool = False):
    """Helper: return env var or raise clearly if required in production."""
    value = os.environ.get(key, default)
    env = os.environ.get("FLASK_ENV", "development")
    if production_required and env == "production" and not os.environ.get(key):
        raise ValueError(
            f"[Kisan Smart] Environment variable '{key}' is required in production "
            f"but was not set. Please add it to your .env file."
        )
    return value


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = _require_env("SECRET_KEY", "dev-key-change-me", production_required=True)
    JWT_SECRET_KEY = _require_env("JWT_SECRET_KEY", "jwt-dev-key-change-me", production_required=True)

    # FIX: was int (3600) — Flask-JWT-Extended requires timedelta
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = _require_env(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/kisan_smart",
        production_required=True,
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # FIX: pool_pre_ping prevents stale connection errors after idle periods
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "True") == "True"
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # ── Mail ──────────────────────────────────────────────────────────────────
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("EMAIL_USER")
    MAIL_PASSWORD = os.environ.get("EMAIL_PASS")
    # FIX: single source of truth — was duplicated across base + TestingConfig
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@kisan-smart.com")
    MAIL_SUPPRESS_SEND = os.environ.get("FLASK_ENV", "development") != "production"

    # ── API / Docs ────────────────────────────────────────────────────────────
    API_TITLE = "Kisan Smart API"
    API_VERSION = "v1"
    SWAGGER_UI_DOC_EXPANSION = "list"

    # FIX: debug must default False — never accidentally True in production
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set True only when debugging queries


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_kisan.db"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    MAIL_SUPPRESS_SEND = True
    # FIX: TestingConfig was missing JWT_SECRET_KEY — JWT routes returned 500 in tests
    JWT_SECRET_KEY = "test-jwt-secret-key-not-for-production"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(env: str = None) -> Config:
    env = env or os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
