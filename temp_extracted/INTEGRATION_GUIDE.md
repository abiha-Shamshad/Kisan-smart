# Urdu Voice Input & Output — Integration Guide

## Files delivered
```
urdu-voice/
  services/
    urdu_stt.py          ← Whisper STT + Urdu value extractor
    urdu_tts.py          ← gTTS Urdu speech synthesis + template engine
  routes/
    voice.py             ← Flask Blueprint (3 API endpoints)
  static/js/
    voice_input.js       ← Browser recording + waveform + playback controller
  templates/
    voice_dashboard.html ← Full RTL Urdu voice dashboard (Jinja2)
  tests/
    test_urdu_voice.py   ← 20 pytest tests (no network/audio needed)
```

---

## Step 1 — Install dependencies
```bash
# Core
pip install openai-whisper gTTS --break-system-packages

# System: ffmpeg (required by Whisper for audio decoding)
sudo apt install ffmpeg           # Ubuntu/Debian
# brew install ffmpeg             # macOS
# choco install ffmpeg            # Windows

# Optional offline TTS fallback
pip install pyttsx3 --break-system-packages
```

## Step 2 — Add to .env
```env
WHISPER_MODEL=small           # tiny | small | medium | large-v3
                               # small = best Urdu/speed balance on CPU
                               # medium = better accuracy, needs 5GB RAM
                               # large-v3 = best quality, needs GPU
TTS_CACHE_DIR=/tmp/kisan_tts_cache
```

## Step 3 — Register Blueprint in create_app()
```python
# In website/__init__.py, inside create_app():
from routes.voice import voice_bp
app.register_blueprint(voice_bp, url_prefix='/api/voice')
```

## Step 4 — Add Whisper model preload to app startup
In app.py, add after `db.create_all()`:
```python
# Pre-load Whisper on startup (avoids 30s delay on first voice request)
if env != 'testing':
    from services.urdu_stt import _get_whisper_model
    _get_whisper_model()   # loads and caches model
```

## Step 5 — Run tests
```bash
pytest tests/test_urdu_voice.py -v
# Expected: 20 passed (no audio files or network needed)
```

---

## API Reference

### POST /api/voice/transcribe
Send raw audio bytes. Returns Urdu transcript + parsed soil values.

```
Content-Type: audio/webm
Authorization: Bearer <jwt>
Body: <raw audio bytes>

Response:
{
  "transcript":         "گندم نائٹروجن نوے فاسفورس پچاس...",
  "whisper_confidence": 0.82,
  "crop":               "Wheat",
  "nitrogen":           90.0,
  "phosphorus":         50.0,
  "potassium":          30.0,
  "ph":                 6.8,
  "parse_confidence":   1.0,
  "needs_confirmation": false
}
```

### POST /api/voice/speak
Returns MP3 audio of a recommendation in Urdu.

```json
{ "mode": "recommendation", "crop": "Wheat", "fertilizer": "Urea",
  "quantity": 45, "confidence": 88, "detail": "full" }
```

### GET /api/voice/greeting
Returns MP3 of the Urdu welcome message.

---

## What a farmer says (example scripts)

Full form:
> "میری گندم کی فصل ہے۔ نائٹروجن نوے، فاسفورس پچاس، پوٹاشیم تیس، پی ایچ سات"

Shorthand (4 numbers):
> "گندم نوے پچاس تیس سات"

With Indic numerals (Whisper may produce):
> "چاول نائٹروجن ۸۰ فاسفورس ۴۰ پوٹاشیم ۵۰ پی ایچ ۶"

---

## Whisper model comparison for Urdu

| Model    | RAM   | CPU speed | Urdu WER | Recommendation |
|----------|-------|-----------|----------|----------------|
| tiny     | 1GB   | ~0.5s     | ~35%     | Dev only        |
| small    | 2GB   | ~2s       | ~22%     | ✅ Production CPU |
| medium   | 5GB   | ~6s       | ~15%     | ✅ GPU or high-RAM server |
| large-v3 | 10GB  | ~15s      | ~10%     | GPU server only |

For production on a low-cost VPS (2GB RAM), use `small`.
For a GPU server (e.g. Colab, Vast.ai), use `medium` or `large-v3`.

---

## Urdu speech patterns supported

The extractor handles these real-world variations:

| Farmer says                          | Extracted |
|--------------------------------------|-----------|
| نائٹروجن نوے                         | N=90      |
| نائٹروجن: 90                         | N=90      |
| نائٹروجن ۹۰ (Indic numerals)        | N=90      |
| گندم 90 50 30 7 (shorthand)          | all 4     |
| تیزابیت سات (pH synonym)            | pH=7      |
| این پچانوے (spoken initials + word) | N=95*     |

*Partial support — depends on Whisper transcription variant.

---

## Cost breakdown

| Component  | Cost      | Notes |
|------------|-----------|-------|
| Whisper    | Free      | Open-source, runs locally |
| gTTS       | Free      | Uses Google Translate TTS (undocumented API) |
| ffmpeg     | Free      | Audio decoding |
| pyttsx3    | Free      | Offline TTS fallback |
| Server RAM | ~2GB extra| For Whisper "small" model |

Total additional cost: **PKR 0** per month on existing server.
