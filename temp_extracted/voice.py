"""
routes/voice.py
================
Flask Blueprint for all Urdu voice input/output endpoints.

Endpoints:
  POST /api/voice/transcribe   — STT: audio → Urdu text + parsed soil values
  POST /api/voice/speak        — TTS: text/recommendation → Urdu MP3 audio
  GET  /api/voice/greeting     — Returns greeting audio (first page load)

Mount in create_app():
  from routes.voice import voice_bp
  app.register_blueprint(voice_bp, url_prefix='/api/voice')
"""

import io
import logging
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from services.urdu_stt import process_voice_input
from services.urdu_tts import (
    speak_recommendation, speak_confirmation,
    speak_template, text_to_speech_urdu
)

logger = logging.getLogger(__name__)
voice_bp = Blueprint("voice", __name__)

# Max audio size: 10MB (a 60-second WebM recording is ~1-2MB typically)
MAX_AUDIO_SIZE = 10 * 1024 * 1024


# ── POST /api/voice/transcribe ────────────────────────────────────────────────

@voice_bp.route("/transcribe", methods=["POST"])
@jwt_required()
def transcribe():
    """
    Receive audio blob from browser, return Urdu transcript + parsed soil values.

    Request:
        Content-Type: audio/webm (or audio/ogg, audio/wav)
        Body: raw audio bytes

    Response 200:
        {
          "transcript":          "میری گندم ہے نائٹروجن نوے...",
          "language":            "ur",
          "whisper_confidence":  0.82,
          "crop":                "Wheat",
          "nitrogen":            90.0,
          "phosphorus":          50.0,
          "potassium":           30.0,
          "ph":                  6.8,
          "parse_confidence":    0.8,
          "raw_text":            "...",
          "needs_confirmation":  true   # ask farmer to confirm if confidence < 0.7
        }
    """
    # Validate content type
    content_type = request.content_type or "audio/webm"
    allowed = {"audio/webm", "audio/ogg", "audio/wav", "audio/mp4",
               "audio/mpeg", "audio/x-wav", "audio/mp4;codecs=opus"}
    if not any(ct in content_type for ct in allowed):
        return jsonify({"error": f"Unsupported audio type: {content_type}"}), 415

    # Validate size
    audio_bytes = request.get_data()
    if not audio_bytes:
        return jsonify({"error": "Empty audio data"}), 400
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        return jsonify({"error": f"Audio too large (max {MAX_AUDIO_SIZE//1024//1024}MB)"}), 413

    try:
        result = process_voice_input(audio_bytes, mime_type=content_type)
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        return jsonify({"error": "Transcription failed. Please try again."}), 503

    # Flag low-confidence parses for frontend to ask user to confirm
    result["needs_confirmation"] = (
        result["parse_confidence"] < 0.6 or
        result["whisper_confidence"] < 0.4
    )

    return jsonify(result)


# ── POST /api/voice/speak ─────────────────────────────────────────────────────

@voice_bp.route("/speak", methods=["POST"])
@jwt_required()
def speak():
    """
    Generate Urdu TTS audio for a recommendation or any Urdu text.

    Request JSON (option A — full recommendation):
        {
          "mode":       "recommendation",
          "crop":       "Wheat",
          "fertilizer": "Urea",
          "quantity":   45.0,
          "confidence": 88.0,
          "detail":     "full"    // or "short"
        }

    Request JSON (option B — confirmation readback):
        {
          "mode": "confirm",
          "crop": "Wheat",
          "n": 90, "p": 50, "k": 30, "ph": 6.8
        }

    Request JSON (option C — arbitrary template):
        {
          "mode": "template",
          "key":  "greeting"
        }

    Request JSON (option D — custom Urdu text):
        {
          "mode": "text",
          "text": "آپ کی مٹی میں پوٹاشیم کم ہے"
        }

    Response:
        Content-Type: audio/mpeg
        Body: MP3 audio bytes
    """
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "text")
    slow = data.get("slow", False)  # Accessibility: slower speech

    try:
        if mode == "recommendation":
            audio = speak_recommendation(
                crop       = data.get("crop", ""),
                fertilizer = data.get("fertilizer", ""),
                quantity   = float(data.get("quantity", 0)),
                confidence = float(data.get("confidence", 0)),
                mode       = data.get("detail", "full"),
                slow       = slow,
            )

        elif mode == "confirm":
            audio = speak_confirmation(
                crop = data.get("crop"),
                n    = data.get("n"),
                p    = data.get("p"),
                k    = data.get("k"),
                ph   = data.get("ph"),
            )

        elif mode == "template":
            key    = data.get("key", "greeting")
            kwargs = {k: v for k, v in data.items() if k not in ("mode", "key")}
            audio  = speak_template(key, **kwargs)

        elif mode == "text":
            text = data.get("text", "")
            if not text:
                return jsonify({"error": "text field required"}), 400
            if len(text) > 1000:
                return jsonify({"error": "Text too long (max 1000 chars)"}), 400
            audio = text_to_speech_urdu(text, slow=slow)

        else:
            return jsonify({"error": f"Unknown mode: {mode}"}), 400

    except Exception as e:
        logger.error(f"TTS failed: {e}", exc_info=True)
        return jsonify({"error": "Audio generation failed. Check internet connection."}), 503

    return send_file(
        io.BytesIO(audio),
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name="kisan_recommendation.mp3",
    )


# ── GET /api/voice/greeting ───────────────────────────────────────────────────

@voice_bp.route("/greeting", methods=["GET"])
@jwt_required()
def greeting():
    """
    Return the welcome greeting audio.
    Called on dashboard load so audio is ready before farmer taps mic.
    """
    try:
        audio = speak_template("greeting")
        return send_file(
            io.BytesIO(audio),
            mimetype="audio/mpeg",
            as_attachment=False,
        )
    except Exception as e:
        logger.warning(f"Greeting TTS failed: {e}")
        return jsonify({"error": "Audio unavailable"}), 503
