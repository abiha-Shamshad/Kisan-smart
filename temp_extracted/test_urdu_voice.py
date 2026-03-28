"""
tests/test_urdu_voice.py
========================
Unit tests for Urdu STT value extraction and TTS text formatting.
No audio files or network calls required — all mocked.

Run: pytest tests/test_urdu_voice.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from services.urdu_stt import UrduValueExtractor, _words_to_number, _arabic_indic_to_int
from services.urdu_tts import TEMPLATES, CROP_URDU, FERTILIZER_URDU


# ── Number conversion tests ────────────────────────────────────────────────────

class TestNumberConversion:

    def test_arabic_indic_to_ascii(self):
        assert _arabic_indic_to_int("۹۰") == "90"
        assert _arabic_indic_to_int("۶.۵") == "6.5"
        assert _arabic_indic_to_int("نائٹروجن ۱۰۰") == "نائٹروجن 100"

    def test_digit_string_extraction(self):
        assert _words_to_number("90") == 90.0
        assert _words_to_number("6.5") == 6.5
        assert _words_to_number("150") == 150.0

    def test_urdu_word_numbers(self):
        assert _words_to_number("نوے") == 90.0
        assert _words_to_number("پچاس") == 50.0
        assert _words_to_number("تیس") == 30.0
        assert _words_to_number("سو") == 100.0

    def test_none_on_invalid(self):
        assert _words_to_number("نامعلوم") is None
        assert _words_to_number("") is None


# ── Value extractor tests ──────────────────────────────────────────────────────

class TestUrduValueExtractor:

    def setup_method(self):
        self.ext = UrduValueExtractor()

    # ── Crop detection ─────────────────────────────────────────────────────────

    def test_wheat_detection(self):
        r = self.ext.extract("میری گندم کی فصل ہے")
        assert r["crop"] == "Wheat"

    def test_rice_detection(self):
        r = self.ext.extract("چاول اگانا ہے")
        assert r["crop"] == "Rice"

    def test_cotton_detection(self):
        r = self.ext.extract("کپاس کا کھیت ہے")
        assert r["crop"] == "Cotton"

    def test_no_crop(self):
        r = self.ext.extract("نائٹروجن 90 فاسفورس 50 پوٹاشیم 30 پی ایچ 7")
        assert r["crop"] is None

    # ── NPK + pH extraction ────────────────────────────────────────────────────

    def test_full_extraction_arabic_numerals(self):
        transcript = "گندم نائٹروجن 90 فاسفورس 50 پوٹاشیم 30 پی ایچ 6.8"
        r = self.ext.extract(transcript)
        assert r["crop"] == "Wheat"
        assert r["nitrogen"] == 90.0
        assert r["phosphorus"] == 50.0
        assert r["potassium"] == 30.0
        assert r["ph"] == 6.8

    def test_full_extraction_indic_numerals(self):
        transcript = "چاول نائٹروجن ۸۰ فاسفورس ۴۰ پوٹاشیم ۵۰ پی ایچ ۶.۵"
        r = self.ext.extract(transcript)
        assert r["crop"] == "Rice"
        assert r["nitrogen"] == 80.0
        assert r["ph"] == 6.5

    def test_shorthand_4_numbers(self):
        # Farmer says only 4 numbers without labels
        r = self.ext.extract("گندم 90 50 30 7")
        assert r["nitrogen"]   == 90.0
        assert r["phosphorus"] == 50.0
        assert r["potassium"]  == 30.0
        assert r["ph"]         == 7.0

    def test_out_of_range_ph_rejected(self):
        # pH > 14 should not be accepted
        r = self.ext.extract("پی ایچ 99")
        assert r["ph"] is None

    def test_out_of_range_npk_rejected(self):
        r = self.ext.extract("نائٹروجن 9999")
        assert r["nitrogen"] is None

    # ── Parse confidence ───────────────────────────────────────────────────────

    def test_full_confidence(self):
        r = self.ext.extract("گندم نائٹروجن 90 فاسفورس 50 پوٹاشیم 30 پی ایچ 7")
        assert r["parse_confidence"] == 1.0

    def test_partial_confidence(self):
        r = self.ext.extract("گندم نائٹروجن 90")
        assert 0 < r["parse_confidence"] < 1.0

    def test_zero_confidence_empty(self):
        r = self.ext.extract("آپ کا شکریہ")
        assert r["parse_confidence"] == 0.0

    # ── Robustness ─────────────────────────────────────────────────────────────

    def test_colon_separator(self):
        r = self.ext.extract("نائٹروجن: 120 فاسفورس: 60 پوٹاشیم: 40")
        assert r["nitrogen"] == 120.0

    def test_alternative_ph_trigger(self):
        r = self.ext.extract("تیزابیت 6.5")
        assert r["ph"] == 6.5

    def test_urdu_word_value(self):
        # Whisper may transcribe "نوے" instead of "90"
        r = self.ext.extract("نائٹروجن نوے")
        assert r["nitrogen"] == 90.0


# ── TTS template tests ─────────────────────────────────────────────────────────

class TestUrduTTSTemplates:

    def test_all_templates_exist(self):
        required = ["recommendation_full", "recommendation_short",
                    "error_no_crop", "error_incomplete",
                    "confirm_values", "greeting", "retry"]
        for key in required:
            assert key in TEMPLATES, f"Template '{key}' missing"

    def test_recommendation_full_format(self):
        text = TEMPLATES["recommendation_full"].format(
            crop="گندم", fertilizer="یوریا",
            quantity=45, confidence=88, guideline="بوائی پر ڈالیں"
        )
        assert "یوریا" in text
        assert "45" in text
        assert "88" in text

    def test_confirm_values_format(self):
        text = TEMPLATES["confirm_values"].format(
            crop="گندم", n=90, p=50, k=30, ph=6.8
        )
        assert "گندم" in text
        assert "90" in text
        assert "6.8" in text

    def test_all_crops_have_urdu_names(self):
        for crop in ["Wheat", "Rice", "Maize", "Cotton", "Sugarcane"]:
            assert crop in CROP_URDU, f"Crop '{crop}' missing Urdu name"

    def test_all_fertilizers_have_urdu_names(self):
        for fert in ["Urea", "DAP", "NPK 15-15-15", "SOP", "SSP"]:
            assert fert in FERTILIZER_URDU, f"Fertilizer '{fert}' missing Urdu name"


# ── Integration mock test ──────────────────────────────────────────────────────

class TestProcessVoiceInputMocked:

    @patch("services.urdu_stt.transcribe_urdu")
    def test_full_pipeline(self, mock_transcribe):
        mock_transcribe.return_value = {
            "text":       "گندم نائٹروجن 90 فاسفورس 50 پوٹاشیم 30 پی ایچ 7",
            "language":   "ur",
            "segments":   [],
            "confidence": 0.85,
        }

        from services.urdu_stt import process_voice_input
        result = process_voice_input(b"fake_audio_bytes", "audio/webm")

        assert result["crop"]        == "Wheat"
        assert result["nitrogen"]    == 90.0
        assert result["phosphorus"]  == 50.0
        assert result["potassium"]   == 30.0
        assert result["ph"]          == 7.0
        assert result["parse_confidence"] == 1.0

    @patch("services.urdu_stt.transcribe_urdu")
    def test_low_confidence_flagged(self, mock_transcribe):
        mock_transcribe.return_value = {
            "text": "کچھ بات ہوئی", "language": "ur",
            "segments": [], "confidence": 0.2,
        }

        from services.urdu_stt import process_voice_input
        result = process_voice_input(b"x" * 2000, "audio/webm")
        assert result["parse_confidence"] == 0.0
