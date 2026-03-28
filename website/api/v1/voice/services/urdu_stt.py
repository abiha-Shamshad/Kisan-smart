"""
services/urdu_stt.py
=====================
Urdu Speech-to-Text service using OpenAI Whisper (local) with
intelligent soil value extraction from natural Urdu speech.

How it works:
  1. Browser records audio via MediaRecorder API → sends WebM/OGG blob
  2. Flask endpoint receives blob, saves as temp WAV
  3. Whisper transcribes with language="ur" (Urdu)
  4. UrduValueExtractor parses NPK + pH from the transcript
  5. Returns structured JSON to frontend

Model choice:
  - whisper "small" (244M params): best balance for Urdu on CPU
    ~2-4s per recording on modern CPU, ~0.5s on GPU
  - whisper "medium" if GPU available: noticeably better Urdu accuracy
  - DO NOT use "turbo" — optimised for English only, poor Urdu support

Install:
  pip install openai-whisper ffmpeg-python
  # Also requires system ffmpeg:
  # Ubuntu:  sudo apt install ffmpeg
  # Windows: choco install ffmpeg
"""

import re
import os
import uuid
import logging
import tempfile
from pathlib import Path
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# ── Whisper model (loaded once, cached) ──────────────────────────────────────

@lru_cache(maxsize=1)
def _get_whisper_model():
    """
    Lazy-load Whisper. Cached so the 244MB model loads only once at startup.
    Change "small" to "medium" if you have a GPU — better Urdu accuracy.
    """
    try:
        import whisper
        model_size = os.environ.get("WHISPER_MODEL", "small")
        logger.info(f"Loading Whisper model: {model_size} (first load may take ~30s)")
        model = whisper.load_model(model_size)
        logger.info(f"Whisper model '{model_size}' ready.")
        return model
    except ImportError:
        raise ImportError(
            "Install whisper: pip install openai-whisper\n"
            "And ffmpeg: sudo apt install ffmpeg"
        )


def transcribe_urdu(audio_path: str) -> dict:
    """
    Transcribe an audio file to Urdu text using Whisper.

    Args:
        audio_path: Path to the audio file (WAV, MP3, OGG, WebM, M4A, etc.)

    Returns:
        {
          "text":     str,   # Urdu transcript
          "language": str,   # detected language code
          "segments": list,  # word-level timestamps (useful for debugging)
          "confidence": float  # avg log-probability as rough confidence 0-1
        }
    """
    model = _get_whisper_model()

    # Force Urdu language for Kisan Smart (prevents auto-detecting as Arabic)
    result = model.transcribe(
        audio_path,
        language="ur",          # Force Urdu — critical for soil value accuracy
        task="transcribe",      # transcribe (not translate)
        fp16=False,             # fp16 only works on CUDA — safe default
        condition_on_previous_text=False,  # avoid hallucination loop on short clips
        initial_prompt=(        # domain hint: tell model to expect agricultural terms
            "گندم چاول مکئی کپاس گنا نائٹروجن فاسفورس پوٹاشیم پی ایچ مٹی کھاد"
        ),
    )

    # Compute rough confidence from avg log-prob of all segments
    segments = result.get("segments", [])
    if segments:
        avg_logprob = sum(s.get("avg_logprob", -1) for s in segments) / len(segments)
        # log-prob of -0.2 ≈ very confident, -1.0 ≈ uncertain
        confidence = max(0.0, min(1.0, (avg_logprob + 1.0)))
    else:
        confidence = 0.0

    return {
        "text":       result["text"].strip(),
        "language":   result.get("language", "ur"),
        "segments":   segments,
        "confidence": round(confidence, 2),
    }


# ── Urdu number words → digits map ───────────────────────────────────────────
# Whisper may transcribe spoken numbers as Urdu words.
# This covers the ranges a farmer would say for NPK (0-300) and pH (3-10).

URDU_ONES = {
    "صفر": 0, "ایک": 1, "دو": 2, "تین": 3, "چار": 4,
    "پانچ": 5, "چھ": 6, "سات": 7, "آٹھ": 8, "نو": 9,
    "دس": 10, "گیارہ": 11, "بارہ": 12, "تیرہ": 13, "چودہ": 14,
    "پندرہ": 15, "سولہ": 16, "سترہ": 17, "اٹھارہ": 18, "انیس": 19,
    "بیس": 20, "تیس": 30, "چالیس": 40, "پچاس": 50,
    "ساٹھ": 60, "ستر": 70, "اسی": 80, "نوے": 90,
    "سو": 100, "ڈیڑھ سو": 150, "دو سو": 200, "ڈھائی سو": 250, "تین سو": 300,
}

# Also handle Eastern Arabic-Indic numerals that Whisper may output
ARABIC_INDIC = {"۰":0,"۱":1,"۲":2,"۳":3,"۴":4,"۵":5,"۶":6,"۷":7,"۸":8,"۹":9}

# Crop name synonyms (Whisper may transcribe regional variants)
CROP_SYNONYMS = {
    "گندم": "Wheat", "گہوں": "Wheat", "گیہوں": "Wheat",
    "چاول": "Rice",  "دھان": "Rice",
    "مکئی": "Maize", "ذرہ": "Maize",
    "کپاس": "Cotton","روئی": "Cotton",
    "گنا":  "Sugarcane", "اکھ": "Sugarcane",
}

# Parameter trigger phrases in Urdu speech
PARAM_TRIGGERS = {
    "nitrogen": [
        "نائٹروجن", "نائیٹروجن", "این", "n",
    ],
    "phosphorus": [
        "فاسفورس", "فاسفیرس", "پی", "p",
    ],
    "potassium": [
        "پوٹاشیم", "پوٹاشم", "کے", "k",
    ],
    "ph": [
        "پی ایچ", "پی-ایچ", "ph", "پی۔ایچ", "ایچ", "تیزابیت",
    ],
}


def _arabic_indic_to_int(text: str) -> str:
    """Convert Eastern Arabic-Indic numerals (۰-۹) to ASCII digits."""
    for ar, digit in ARABIC_INDIC.items():
        text = text.replace(ar, str(digit))
    return text


def _words_to_number(text: str) -> Optional[float]:
    """
    Try to convert Urdu number words or digit strings to a float.
    Returns None if conversion fails.
    """
    text = _arabic_indic_to_int(text.strip())

    # Try plain digit extraction first
    m = re.search(r'\d+(?:[.,]\d+)?', text)
    if m:
        return float(m.group(0).replace(',', '.'))

    # Try Urdu word lookup
    for word, val in sorted(URDU_ONES.items(), key=lambda x: -len(x[0])):
        if word in text:
            remaining = text.replace(word, "").strip()
            if remaining:
                sub = _words_to_number(remaining)
                return val + (sub or 0)
            return float(val)
    return None


class UrduValueExtractor:
    """
    Extracts structured soil input values from Urdu speech transcripts.

    A farmer might say:
      "میری گندم کی فصل ہے، نائٹروجن نوے، فاسفورس پچاس،
       پوٹاشیم تیس، پی ایچ سات"

    This extracts: crop=Wheat, N=90, P=50, K=30, pH=7.0
    """

    def extract(self, transcript: str) -> dict:
        """
        Parse soil parameters from a Urdu transcript.

        Returns:
            {
              "crop":       str | None,
              "nitrogen":   float | None,
              "phosphorus": float | None,
              "potassium":  float | None,
              "ph":         float | None,
              "raw_text":   str,
              "parse_confidence": float,  # 0-1, how many fields were found
            }
        """
        text = transcript.strip()
        result = {
            "crop": None,
            "nitrogen": None,
            "phosphorus": None,
            "potassium": None,
            "ph": None,
            "raw_text": text,
            "parse_confidence": 0.0,
        }

        # 1. Detect crop
        for urdu_name, english_name in CROP_SYNONYMS.items():
            if urdu_name in text:
                result["crop"] = english_name
                break

        # 2. Convert Arabic-Indic numerals to ASCII
        text_norm = _arabic_indic_to_int(text)

        # 3. Extract parameter values
        # Strategy: look for trigger word, then grab the next number in the text
        for param, triggers in PARAM_TRIGGERS.items():
            for trigger in triggers:
                # Find trigger position, then extract number after it
                pattern = re.compile(
                    re.escape(trigger) + r'[\s،,:-]*(\d+(?:[.,]\d+)?)',
                    re.IGNORECASE | re.UNICODE
                )
                m = pattern.search(text_norm)
                if m:
                    val = float(m.group(1).replace(',', '.'))
                    # Sanity-check ranges
                    if param in ("nitrogen", "phosphorus", "potassium") and 0 <= val <= 350:
                        result[param] = round(val, 1)
                    elif param == "ph" and 0 <= val <= 14:
                        result[param] = round(val, 1)
                    break

        # 4. Fallback: if no triggers found but 4 numbers exist in order,
        #    assume N P K pH order (common farmer shorthand: "90 50 30 7")
        if all(result[k] is None for k in ["nitrogen","phosphorus","potassium","ph"]):
            numbers = re.findall(r'\d+(?:\.\d+)?', text_norm)
            if len(numbers) >= 4:
                n, p, k, ph = float(numbers[0]), float(numbers[1]), float(numbers[2]), float(numbers[3])
                if 0<=n<=350 and 0<=p<=350 and 0<=k<=350 and 0<=ph<=14:
                    result["nitrogen"] = n
                    result["phosphorus"] = p
                    result["potassium"] = k
                    result["ph"] = ph

        # 5. Compute parse confidence
        fields_found = sum(1 for k in ["crop","nitrogen","phosphorus","potassium","ph"] if result[k] is not None)
        result["parse_confidence"] = round(fields_found / 5, 2)

        return result


# ── Public API ────────────────────────────────────────────────────────────────

_extractor = UrduValueExtractor()


def process_voice_input(audio_bytes: bytes, mime_type: str = "audio/webm") -> dict:
    """
    End-to-end pipeline: audio bytes → structured soil values.

    Args:
        audio_bytes: Raw audio bytes from browser MediaRecorder
        mime_type:   MIME type of the audio (webm, ogg, wav, mp4)

    Returns:
        {
          "transcript":       str,
          "language":         str,
          "whisper_confidence": float,
          "crop":             str | None,
          "nitrogen":         float | None,
          "phosphorus":       float | None,
          "potassium":        float | None,
          "ph":               float | None,
          "parse_confidence": float,
          "raw_text":         str,
        }
    """
    # Determine file extension from MIME type
    ext_map = {
        "audio/webm":  ".webm",
        "audio/ogg":   ".ogg",
        "audio/wav":   ".wav",
        "audio/mp4":   ".m4a",
        "audio/mpeg":  ".mp3",
        "audio/x-wav": ".wav",
    }
    ext = ext_map.get(mime_type.split(";")[0].strip(), ".webm")

    # Write to temp file (Whisper needs a file path, not bytes)
    tmp_path = Path(tempfile.gettempdir()) / f"kisan_voice_{uuid.uuid4().hex}{ext}"
    try:
        tmp_path.write_bytes(audio_bytes)

        # Transcribe
        transcription = transcribe_urdu(str(tmp_path))

        # Extract soil values
        parsed = _extractor.extract(transcription["text"])

        return {
            "transcript":         transcription["text"],
            "language":           transcription["language"],
            "whisper_confidence": transcription["confidence"],
            **{k: parsed[k] for k in ["crop","nitrogen","phosphorus","potassium","ph","parse_confidence","raw_text"]},
        }

    finally:
        # Always clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()
