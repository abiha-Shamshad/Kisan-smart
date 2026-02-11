"""
Integration tests for history management
"""

import pytest
from website.models import Recommendation


@pytest.mark.integration
class TestHistoryFlow:
    """Test prediction history management"""

    def test_get_user_history(self, authenticated_client, test_predictions):
        """Test user can retrieve their prediction history"""
        response = authenticated_client.get("/api/v1/history")

        assert response.status_code == 200
        assert "data" in response.json
        assert "predictions" in response.json["data"]

        predictions = response.json["data"]["predictions"]
        assert len(predictions) > 0

    def test_history_pagination(self, authenticated_client, test_predictions):
        """Test history pagination works"""
        # Get first page
        response = authenticated_client.get("/api/v1/history?page=1&per_page=5")

        assert response.status_code == 200
        data = response.json["data"]

        assert "predictions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

        # Should return max 5 items
        assert len(data["predictions"]) <= 5

    def test_history_filtering_by_crop(self, authenticated_client, test_predictions):
        """Test filtering history by crop type"""
        response = authenticated_client.get("/api/v1/history?crop_type=wheat")

        assert response.status_code == 200
        predictions = response.json["data"]["predictions"]

        # All predictions should be for wheat
        for pred in predictions:
            assert pred["crop_type"] == "wheat"

    def test_history_filtering_by_date(self, authenticated_client, test_predictions):
        """Test filtering history by date range"""
        from datetime import datetime, timedelta

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        response = authenticated_client.get(
            f"/api/v1/history?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
        )

        assert response.status_code == 200
        # Should return predictions within date range

    def test_view_single_prediction(self, authenticated_client, test_predictions):
        """Test user can view details of a single prediction"""
        prediction_id = test_predictions[0].prediction_id
        response = authenticated_client.get(f"/api/v1/history/{prediction_id}")

        assert response.status_code == 200
        assert "data" in response.json

        data = response.json["data"]
        assert data["prediction_id"] == prediction_id
        assert "crop_type" in data
        assert "fertilizer_type" in data

    def test_cannot_view_other_user_prediction(self, authenticated_client, db_session):
        """Test user cannot view another user's prediction"""
        # Create another user and prediction
        from website.models import User

        other_user = User(username="otheruser", email="other@example.com")
        other_user.set_password("Password123!")
        db_session.session.add(other_user)
        db_session.session.commit()

        other_pred = Recommendation(
            user_id=other_user.id,
            crop_type="rice",
            nitrogen=40,
            phosphorus=30,
            potassium=25,
            ph=6.5,
            fertilizer_type="DAP",
            quantity=100,
            overall_confidence=80,
        )
        db_session.session.add(other_pred)
        db_session.session.commit()

        # Try to access other user's prediction
        response = authenticated_client.get(f"/api/v1/history/{other_pred.id}")

        # Should return 403 Forbidden or 404 Not Found
        assert response.status_code in [403, 404]

    def test_delete_prediction(
        self, authenticated_client, test_predictions, db_session
    ):
        """Test user can delete a prediction"""
        prediction_id = test_predictions[0].prediction_id

        response = authenticated_client.delete(f"/api/v1/history/{prediction_id}")

        assert response.status_code == 200

        # Prediction should be deleted from database
        deleted_pred = Recommendation.query.get(prediction_id)
        assert deleted_pred is None

    def test_cannot_delete_other_user_prediction(
        self, authenticated_client, db_session
    ):
        """Test user cannot delete another user's prediction"""
        # Create another user and prediction
        from website.models import User

        other_user = User(username="anotheruser", email="another@example.com")
        other_user.set_password("Password123!")
        db_session.session.add(other_user)
        db_session.session.commit()

        other_pred = Recommendation(
            user_id=other_user.id,
            crop_type="maize",
            nitrogen=45,
            phosphorus=30,
            potassium=25,
            ph=6.8,
            moisture=65.0,
            temperature=22.5,
            farm_area=2.5,
            growth_stage="Vegetative",
            # Optional fields omitted
            fertilizer_type="NPK",
            quantity=110,
            overall_confidence=75,
        )
        db_session.session.add(other_pred)
        db_session.session.commit()

        # Try to delete other user's prediction
        response = authenticated_client.delete(f"/api/v1/history/{other_pred.id}")

        # Should return 403 Forbidden
        assert response.status_code in [403, 404]

        # Prediction should still exist
        still_exists = Recommendation.query.get(other_pred.id)
        assert still_exists is not None

    def test_get_history_stats(self, authenticated_client, test_predictions):
        """Test getting history statistics for dashboard"""
        response = authenticated_client.get("/api/v1/history/stats")

        assert response.status_code == 200
        assert "data" in response.json

        stats = response.json["data"]

        # Should include key statistics
        assert "total_predictions" in stats
        assert "this_month" in stats
        assert "avg_confidence" in stats
        assert "crops_analyzed" in stats

        # Values should be reasonable
        assert stats["total_predictions"] >= 0
        assert 0 <= stats["avg_confidence"] <= 100
