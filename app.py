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

        # Pre-load Whisper model on startup specifically for the Voice UI
        if env != 'testing':
            logger.info("Pre-loading Whisper STT model (this may take a moment)...")
            os.environ.setdefault("WHISPER_MODEL", "tiny")
            
            # Injecting FFmpeg into live PATH since the 5-hour old server cannot see new system variables
            import os
            ffmpeg_dir = os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin")
            if os.path.exists(ffmpeg_dir):
                os.environ["PATH"] += os.pathsep + ffmpeg_dir
                logger.info(f"Appended FFmpeg path to environment: {ffmpeg_dir}")

            try:
                from website.api.v1.voice.services.urdu_stt import _get_whisper_model
                _get_whisper_model()
            except Exception as e:
                logger.error(f"Whisper preload failed (safely bypassing): {e}")

    port = int(os.environ.get("PORT", 5005))
    debug = env == "development"

    logger.info(f"Starting Kisan Smart on port {port} (env={env}, debug={debug})")
    app.run(debug=debug, port=port, host="0.0.0.0")
