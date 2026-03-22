"""
FIXED app.py
============
Bugs fixed:
1. db.create_all() in __main__ block is fine for dev but was running unconditionally,
   could cause issues if migrations (Alembic/Flask-Migrate) are used — now guarded.
2. No config environment selection — always ran with default (dev) config.
3. debug=True hardcoded — production deployments should read from env.
4. No logging setup — errors were silent in production.
5. Port hardcoded as 5005 — now reads from env with 5005 as default.
"""

import os
import logging
from website import create_app, db
from config import get_config

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kisan_smart")

# ── App factory ───────────────────────────────────────────────────────────────
env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    with app.app_context():
        # FIX: only auto-create tables in dev/testing; production should use migrations
        if env in ("development", "testing"):
            db.create_all()
            logger.info("Database tables created/verified.")
        else:
            logger.warning(
                "Running in production — skipping db.create_all(). "
                "Run 'flask db upgrade' to apply migrations."
            )

    port = int(os.environ.get("PORT", 5005))
    debug = env == "development"

    logger.info(f"Starting Kisan Smart on port {port} (env={env}, debug={debug})")
    app.run(debug=debug, port=port, host="0.0.0.0")
