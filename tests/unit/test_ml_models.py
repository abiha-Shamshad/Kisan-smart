"""
Unit tests for ML prediction models
"""

import pytest
import time
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestMLPredictor:
    """Tests for ML prediction models"""

    def test_model_loads(self):
        """Test ML models load successfully"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()

        assert predictor is not None
        assert hasattr(predictor, "predict")

    def test_prediction_with_valid_input(self, sample_prediction_data):
        """Test prediction with valid input data"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()
        result = predictor.predict(sample_prediction_data)

        # Check result structure
        assert "fertilizer_type" in result
        assert "quantity" in result
        assert "confidence" in result

        # Check data types
        assert isinstance(result["fertilizer_type"], str)
        assert isinstance(result["quantity"], (int, float))
        assert isinstance(result["confidence"], dict)

    def test_prediction_confidence_scores(self, sample_prediction_data):
        """Test confidence scores are in valid range"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()
        result = predictor.predict(sample_prediction_data)

        confidence = result["confidence"]

        # Check overall confidence
        assert "overall_confidence" in confidence
        assert 0 <= confidence["overall_confidence"] <= 100

        # Check component confidences if present
        if "fertilizer_confidence" in confidence:
            assert 0 <= confidence["fertilizer_confidence"] <= 100
        if "quantity_confidence" in confidence:
            assert 0 <= confidence["quantity_confidence"] <= 100

    def test_prediction_with_extreme_values(self):
        """Test prediction handles extreme but valid input"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()

        extreme_data = {
            "crop_type": "wheat",
            "nitrogen": 0,  # Minimum
            "phosphorus": 200,  # Maximum
            "potassium": 0,  # Minimum
            "ph": 3.0,  # Minimum
            "moisture": 0,
            "temperature": -10,
            "farm_area": 0.1,
        }

        result = predictor.predict(extreme_data)

        # Should still return valid structure
        assert "fertilizer_type" in result
        assert "quantity" in result

    def test_prediction_with_missing_optional_params(self):
        """Test prediction works with missing optional parameters"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()

        minimal_data = {
            "crop_type": "rice",
            "nitrogen": 45,
            "phosphorus": 30,
            "potassium": 25,
            "ph": 6.8,
            # Missing: moisture, temperature, farm_area
        }

        result = predictor.predict(minimal_data)

        assert "fertilizer_type" in result
        assert "quantity" in result

    def test_prediction_performance(self, sample_prediction_data):
        """Test prediction completes within acceptable time"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()

        start_time = time.time()
        result = predictor.predict(sample_prediction_data)
        end_time = time.time()

        duration = end_time - start_time

        # Should complete in less than 3 seconds
        assert duration < 3.0, f"Prediction took {duration}s, should be <3s"

    def test_prediction_with_invalid_crop(self):
        """Test prediction handles invalid crop type"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()

        invalid_data = {
            "crop_type": "invalid_crop_12345",
            "nitrogen": 45,
            "phosphorus": 30,
            "potassium": 25,
            "ph": 6.8,
        }

        # Should raise ValueError or return error
        with pytest.raises((ValueError, KeyError)):
            predictor.predict(invalid_data)

    def test_prediction_with_negative_values(self):
        """Test prediction rejects negative nutrient values"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()

        invalid_data = {
            "crop_type": "wheat",
            "nitrogen": -10,  # Invalid
            "phosphorus": 30,
            "potassium": 25,
            "ph": 6.8,
        }

        with pytest.raises(ValueError):
            predictor.predict(invalid_data)

    def test_prediction_consistency(self, sample_prediction_data):
        """Test prediction gives consistent results for same input"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()

        result1 = predictor.predict(sample_prediction_data)
        result2 = predictor.predict(sample_prediction_data)

        # Same input should give same recommendation
        assert result1["fertilizer_type"] == result2["fertilizer_type"]
        # Quantity might vary slightly, but should be close
        assert abs(result1["quantity"] - result2["quantity"]) < 5

    def test_quantity_calculation(self):
        """Test fertilizer quantity is reasonable"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()

        data = {
            "crop_type": "wheat",
            "nitrogen": 45,
            "phosphorus": 30,
            "potassium": 25,
            "ph": 6.8,
            "farm_area": 2.5,
        }

        result = predictor.predict(data)

        # Quantity should be positive and reasonable (0-500 kg/ha)
        assert result["quantity"] > 0
        assert result["quantity"] < 500

    @pytest.mark.slow
    def test_prediction_with_all_crops(self):
        """Test prediction works for all supported crops"""
        from models.ml_models.inference_engine import InferenceEngine

        predictor = InferenceEngine()
        crops = ["wheat", "rice", "maize", "cotton", "sugarcane"]

        for crop in crops:
            data = {
                "crop_type": crop,
                "nitrogen": 45,
                "phosphorus": 30,
                "potassium": 25,
                "ph": 6.8,
            }

            result = predictor.predict(data)

            assert "fertilizer_type" in result
            assert "quantity" in result
