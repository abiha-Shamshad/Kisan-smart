import os
import logging
from website import create_app, db

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kisan_smart")

# App factory
env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    with app.app_context():
        # Auto-create tables if they don't exist
        db.create_all()
        logger.info("Database initialized (tables verified)")

    port = int(os.environ.get("PORT", 5005))
    debug = env == "development"

    logger.info(f"Starting Kisan Smart on port {port} (env={env}, debug={debug})")
    app.run(debug=debug, port=port, host="0.0.0.0")
