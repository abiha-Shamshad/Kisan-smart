import io
import logging
from flask import Blueprint, request, jsonify, send_file

from website.api.v1.voice.services.urdu_stt import process_voice_input
from website.api.v1.voice.services.urdu_tts import (
    speak_recommendation, speak_confirmation,
    speak_template, text_to_speech_urdu
)

logger = logging.getLogger(__name__)
voice_api = Blueprint("voice_api", __name__)

MAX_AUDIO_SIZE = 10 * 1024 * 1024

@voice_api.route("/transcribe", methods=["POST"])
def transcribe():
    content_type = request.content_type or "audio/webm"
    allowed = {"audio/webm", "audio/ogg", "audio/wav", "audio/mp4",
               "audio/mpeg", "audio/x-wav", "audio/mp4;codecs=opus"}
    if not any(ct in content_type for ct in allowed):
        return jsonify({"error": f"Unsupported audio type: {content_type}"}), 415

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

    result["needs_confirmation"] = (
        result.get("parse_confidence", 1.0) < 0.6 or
        result.get("whisper_confidence", 1.0) < 0.4
    )

    return jsonify(result)

@voice_api.route("/speak", methods=["POST"])
def speak():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "text")
    slow = data.get("slow", False)

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

@voice_api.route("/greeting", methods=["GET"])
def greeting():
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
