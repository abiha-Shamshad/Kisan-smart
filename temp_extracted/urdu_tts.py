"""
services/urdu_tts.py
=====================
Urdu Text-to-Speech service using gTTS (Google Translate TTS).
Converts fertilizer recommendations into natural Urdu audio.

gTTS uses the undocumented Google Translate TTS endpoint.
lang='ur' produces clear, natural Urdu speech — no API key needed.

Install:
  pip install gTTS

Note: gTTS requires internet access to generate audio.
For offline fallback, see _offline_fallback() which uses pyttsx3.
"""

import io
import os
import re
import logging
import hashlib
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── Cache directory for generated audio ──────────────────────────────────────
# TTS is slow (~500ms per call). Cache by content hash to avoid re-generating
# the same recommendation text every request.

TTS_CACHE_DIR = Path(os.environ.get("TTS_CACHE_DIR", "/tmp/kisan_tts_cache"))
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ── Urdu recommendation templates ────────────────────────────────────────────
# These are the strings spoken back to the farmer after ML prediction.

TEMPLATES = {
    "recommendation_full": (
        "آپ کی فصل {crop} کے لیے سفارش ہے کہ {fertilizer} استعمال کریں۔ "
        "مقدار: {quantity} کلوگرام فی ایکڑ۔ "
        "اعتماد: {confidence} فیصد۔ "
        "{guideline}"
    ),
    "recommendation_short": (
        "{fertilizer} استعمال کریں۔ {quantity} کلو فی ایکڑ۔"
    ),
    "error_no_crop": (
        "معذرت، فصل کا نام نہیں سمجھ آیا۔ براہ کرم دوبارہ بولیں۔"
    ),
    "error_incomplete": (
        "کچھ قدریں نہیں سمجھ آئیں۔ براہ کرم نائٹروجن، فاسفورس، پوٹاشیم اور پی ایچ بولیں۔"
    ),
    "confirm_values": (
        "آپ نے کہا: {crop}، نائٹروجن {n}، فاسفورس {p}، پوٹاشیم {k}، پی ایچ {ph}۔ "
        "کیا یہ درست ہے؟"
    ),
    "greeting": (
        "کسان سمارٹ میں خوش آمدید۔ براہ کرم اپنی فصل اور مٹی کی قدریں بولیں۔"
    ),
    "retry": (
        "معذرت، دوبارہ کوشش کریں۔ ذرا واضح اور آہستہ بولیں۔"
    ),
}

# Fertilizer names in Urdu (for TTS output)
FERTILIZER_URDU = {
    "Urea":          "یوریا",
    "DAP":           "ڈی اے پی",
    "NPK 15-15-15":  "این پی کے پندرہ پندرہ پندرہ",
    "SOP":           "ایس او پی",
    "SSP":           "سنگل سپر فاسفیٹ",
}

# Crop names in Urdu
CROP_URDU = {
    "Wheat":     "گندم",
    "Rice":      "چاول",
    "Maize":     "مکئی",
    "Cotton":    "کپاس",
    "Sugarcane": "گنا",
}

# Application guidelines in Urdu
GUIDELINES_URDU = {
    "Urea":          "نصف بوائی کے وقت اور نصف اگاؤ کے بعد ڈالیں۔",
    "DAP":           "بوائی سے پہلے مٹی میں ملائیں۔",
    "NPK 15-15-15":  "پہلی آبپاشی سے پہلے یکساں طور پر ڈالیں۔",
    "SOP":           "پوٹاشیم کم ہونے پر بنیادی کھاد کے طور پر استعمال کریں۔",
    "SSP":           "بوائی کی نالیوں میں ڈالیں۔",
}


def _cache_key(text: str) -> str:
    """Generate a cache filename from the text content hash."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def text_to_speech_urdu(text: str, slow: bool = False) -> bytes:
    """
    Convert Urdu text to MP3 audio bytes using gTTS.

    Args:
        text: Urdu text to speak
        slow: If True, slower speech speed (helpful for elderly farmers)

    Returns:
        MP3 audio as bytes

    Raises:
        RuntimeError if gTTS fails (network error, rate limit, etc.)
    """
    # Check cache first
    cache_file = TTS_CACHE_DIR / f"{_cache_key(text)}.mp3"
    if cache_file.exists():
        logger.debug(f"TTS cache hit for text hash {cache_file.stem}")
        return cache_file.read_bytes()

    try:
        from gtts import gTTS, gTTSError

        buf = io.BytesIO()
        tts = gTTS(text=text, lang="ur", slow=slow)
        tts.write_to_fp(buf)
        audio_bytes = buf.getvalue()

        # Cache the result
        cache_file.write_bytes(audio_bytes)
        logger.info(f"TTS generated and cached: {len(audio_bytes)} bytes")
        return audio_bytes

    except ImportError:
        raise ImportError("Install gTTS: pip install gTTS")
    except Exception as e:
        logger.error(f"gTTS failed: {e}. Trying offline fallback.")
        return _offline_fallback(text)


def _offline_fallback(text: str) -> bytes:
    """
    Offline TTS fallback using pyttsx3 (no internet needed).
    Quality is lower but works without internet — important for rural areas.

    Install: pip install pyttsx3
    Note: Urdu support depends on installed system voices.
    On Linux, install espeak-ng for Urdu: sudo apt install espeak-ng
    """
    try:
        import pyttsx3, wave, tempfile, subprocess
        from pathlib import Path

        engine = pyttsx3.init()

        # Try to find Urdu voice
        voices = engine.getProperty("voices")
        urdu_voice = next(
            (v for v in voices if "urdu" in v.name.lower() or "ur" in v.id.lower()),
            None
        )
        if urdu_voice:
            engine.setProperty("voice", urdu_voice.id)

        engine.setProperty("rate", 140)  # Slightly slower for clarity

        # Save to temp wav
        tmp = Path(tempfile.gettempdir()) / "kisan_tts_offline.wav"
        engine.save_to_file(text, str(tmp))
        engine.runAndWait()

        # Convert wav → mp3 via ffmpeg
        mp3_tmp = tmp.with_suffix(".mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(tmp), str(mp3_tmp)],
            capture_output=True, check=True
        )
        return mp3_tmp.read_bytes()

    except Exception as e:
        logger.error(f"Offline TTS fallback also failed: {e}")
        raise RuntimeError("Both online (gTTS) and offline (pyttsx3) TTS failed.")


# ── High-level recommendation speaker ────────────────────────────────────────

def speak_recommendation(
    crop: str,
    fertilizer: str,
    quantity: float,
    confidence: float,
    mode: str = "full",   # "full" or "short"
    slow: bool = False,
) -> bytes:
    """
    Generate Urdu audio for a fertilizer recommendation.

    Args:
        crop:       English crop name e.g. "Wheat"
        fertilizer: English fertilizer name e.g. "Urea"
        quantity:   Recommended quantity in kg/ha
        confidence: ML confidence 0-100
        mode:       "full" = detailed, "short" = brief
        slow:       Slower speech for accessibility

    Returns:
        MP3 audio bytes
    """
    crop_ur   = CROP_URDU.get(crop, crop)
    fert_ur   = FERTILIZER_URDU.get(fertilizer, fertilizer)
    guide_ur  = GUIDELINES_URDU.get(fertilizer, "")

    template_key = f"recommendation_{mode}"
    template = TEMPLATES[template_key]

    text = template.format(
        crop       = crop_ur,
        fertilizer = fert_ur,
        quantity   = int(quantity),
        confidence = int(confidence),
        guideline  = guide_ur,
    )
    return text_to_speech_urdu(text, slow=slow)


def speak_confirmation(
    crop: str, n: float, p: float, k: float, ph: float
) -> bytes:
    """Read back parsed values to farmer for confirmation before prediction."""
    crop_ur = CROP_URDU.get(crop, crop) if crop else "نامعلوم"
    text = TEMPLATES["confirm_values"].format(
        crop=crop_ur,
        n=int(n) if n else "نامعلوم",
        p=int(p) if p else "نامعلوم",
        k=int(k) if k else "نامعلوم",
        ph=ph if ph else "نامعلوم",
    )
    return text_to_speech_urdu(text)


def speak_template(key: str, **kwargs) -> bytes:
    """Speak any named template. e.g. speak_template('greeting')"""
    text = TEMPLATES.get(key, "")
    if kwargs:
        text = text.format(**kwargs)
    return text_to_speech_urdu(text)


def clear_tts_cache():
    """Remove all cached TTS files (call periodically to save disk space)."""
    count = 0
    for f in TTS_CACHE_DIR.glob("*.mp3"):
        f.unlink()
        count += 1
    logger.info(f"Cleared {count} TTS cache files")
    return count
