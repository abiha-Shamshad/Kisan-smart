"""
Integration tests for prediction workflow
"""

import pytest
import time
from website.models import Recommendation


@pytest.mark.integration
class TestPredictionFlow:
    """Test complete prediction workflow"""

    def test_make_prediction_authenticated(
        self, authenticated_client, sample_prediction_data, db_session
    ):
        """Test user can make prediction when authenticated"""
        response = authenticated_client.post(
            "/api/v1/predict", json=sample_prediction_data
        )

        # Should return 200 OK
        assert response.status_code == 200
        assert "data" in response.json

        data = response.json["data"]

        # Should contain recommendation
        assert "fertilizer_type" in data
        assert "quantity" in data
        assert "confidence" in data

        # Should include prediction ID
        assert "prediction_id" in data or "id" in data

    def test_prediction_saves_to_database(
        self, authenticated_client, sample_prediction_data, db_session, test_user
    ):
        """Test prediction is saved to database"""
        initial_count = Recommendation.query.filter_by(user_id=test_user.id).count()

        response = authenticated_client.post(
            "/api/v1/predict", json=sample_prediction_data
        )

        assert response.status_code == 200

        # Should have one more prediction in database
        final_count = Recommendation.query.filter_by(user_id=test_user.id).count()
        assert final_count == initial_count + 1

        # Latest prediction should match input data
        latest_pred = (
            Recommendation.query.filter_by(user_id=test_user.id)
            .order_by(Recommendation.created_at.desc())
            .first()
        )

        assert latest_pred.crop_type == sample_prediction_data["crop_type"]
        assert latest_pred.nitrogen == sample_prediction_data["nitrogen"]
        assert latest_pred.fertilizer_type is not None

    def test_prediction_without_authentication(self, client, sample_prediction_data):
        """Test prediction requires authentication"""
        response = client.post("/api/v1/predict", json=sample_prediction_data)

        # Should return 401 Unauthorized
        assert response.status_code == 401

    def test_prediction_with_invalid_data(self, authenticated_client):
        """Test prediction validates input data"""
        invalid_data = {
            "crop_type": "invalid_crop",
            "nitrogen": -10,  # Negative value
            "phosphorus": 300,  # Out of range
            "potassium": 25,
            "ph": 15,  # Out of range
        }

        response = authenticated_client.post("/api/v1/predict", json=invalid_data)

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
        assert "error" in response.json

    def test_prediction_with_missing_required_fields(self, authenticated_client):
        """Test prediction requires all mandatory fields"""
        incomplete_data = {
            "crop_type": "wheat",
            "nitrogen": 45,
            # Missing phosphorus, potassium, ph
        }

        response = authenticated_client.post("/api/v1/predict", json=incomplete_data)

        assert response.status_code == 422

    def test_prediction_response_time(
        self, authenticated_client, sample_prediction_data
    ):
        """Test prediction completes within acceptable time"""
        start_time = time.time()
        response = authenticated_client.post(
            "/api/v1/predict", json=sample_prediction_data
        )
        end_time = time.time()

        duration = end_time - start_time

        assert response.status_code == 200
        # Should complete within 3 seconds
        assert duration < 3.0, f"Prediction took {duration}s, should be <3s"

    def test_prediction_confidence_scores(
        self, authenticated_client, sample_prediction_data
    ):
        """Test prediction includes confidence scores"""
        response = authenticated_client.post(
            "/api/v1/predict", json=sample_prediction_data
        )

        assert response.status_code == 200

        confidence = response.json["data"]["confidence"]

        assert "overall_confidence" in confidence
        assert 0 <= confidence["overall_confidence"] <= 100

    def test_multiple_predictions_same_user(
        self, authenticated_client, sample_prediction_data, test_user, db_session
    ):
        """Test user can make multiple predictions"""
        # Make first prediction
        response1 = authenticated_client.post(
            "/api/v1/predict", json=sample_prediction_data
        )
        assert response1.status_code == 200

        # Make second prediction with different data
        different_data = sample_prediction_data.copy()
        different_data["crop_type"] = "rice"
        different_data["nitrogen"] = 50

        response2 = authenticated_client.post("/api/v1/predict", json=different_data)
        assert response2.status_code == 200

        # User should have at least 2 predictions
        count = Recommendation.query.filter_by(user_id=test_user.id).count()
        assert count >= 2

    def test_prediction_with_optional_fields(self, authenticated_client):
        """Test prediction works with only required fields"""
        minimal_data = {
            "crop_type": "wheat",
            "nitrogen": 45.0,
            "phosphorus": 30.0,
            "potassium": 25.0,
            "ph": 6.8,
            # Optional fields omitted
        }

        response = authenticated_client.post("/api/v1/predict", json=minimal_data)

        # Should still work
        assert response.status_code == 200
        assert "fertilizer_type" in response.json["data"]

    def test_prediction_with_all_fields(
        self, authenticated_client, sample_prediction_data
    ):
        """Test prediction works with all optional fields"""
        response = authenticated_client.post(
            "/api/v1/predict", json=sample_prediction_data
        )

        assert response.status_code == 200

        # Result should include all input parameters
        data = response.json["data"]
        assert "fertilizer_type" in data
        assert "quantity" in data
