"""
Performance benchmarking tests
"""

import pytest
import time
import statistics
from app.models import Recommendation


@pytest.mark.performance
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    def test_prediction_endpoint_performance(
        self, authenticated_client, sample_prediction_data
    ):
        """Benchmark prediction endpoint response time"""
        n = 20  # Number of iterations
        times = []

        for _ in range(n):
            start = time.time()
            response = authenticated_client.post(
                "/api/v1/predict", json=sample_prediction_data
            )
            end = time.time()

            assert response.status_code == 200
            times.append(end - start)

        # Calculate statistics
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)

        # Performance assertions
        assert avg_time < 3.0, f"Average response time {avg_time:.3f}s exceeds 3s"
        assert (
            median_time < 2.5
        ), f"Median response time {median_time:.3f}s exceeds 2.5s"
        assert max_time < 5.0, f"Max response time {max_time:.3f}s exceeds 5s"

        print(f"\nPrediction Endpoint Performance:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Median: {median_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")

    def test_history_retrieval_performance(
        self, authenticated_client, test_predictions
    ):
        """Benchmark history retrieval performance"""
        n = 30
        times = []

        for _ in range(n):
            start = time.time()
            response = authenticated_client.get("/api/v1/history")
            end = time.time()

            assert response.status_code == 200
            times.append(end - start)

        avg_time = statistics.mean(times)

        # Should be fast (<1s)
        assert avg_time < 1.0, f"Average history retrieval {avg_time:.3f}s exceeds 1s"

        print(f"\nHistory Retrieval Performance:")
        print(f"  Average: {avg_time:.3f}s")

    def test_dashboard_stats_performance(self, authenticated_client, test_predictions):
        """Benchmark dashboard stats calculation"""
        n = 50
        times = []

        for _ in range(n):
            start = time.time()
            response = authenticated_client.get("/api/v1/history/stats")
            end = time.time()

            assert response.status_code == 200
            times.append(end - start)

        avg_time = statistics.mean(times)

        assert avg_time < 0.5, f"Average stats calculation {avg_time:.3f}s exceeds 0.5s"

        print(f"\nDashboard Stats Performance:")
        print(f"  Average: {avg_time:.3f}s")

    def test_database_query_performance(self, db_session, test_user):
        """Benchmark database query performance"""
        # Create larger dataset
        for i in range(100):
            pred = Recommendation(
                user_id=test_user.id,
                crop_type="wheat",
                nitrogen=40 + i,
                phosphorus=30,
                potassium=25,
                ph=6.8,
                fertilizer_type="Urea",
                quantity=100,
                overall_confidence=75,
            )
            db_session.session.add(pred)
        db_session.session.commit()

        # Benchmark query
        start = time.time()
        predictions = (
            Recommendation.query.filter_by(user_id=test_user.id).limit(20).all()
        )
        end = time.time()

        duration = end - start

        assert duration < 0.1, f"Query took {duration:.3f}s, should be <0.1s"
        assert len(predictions) == 20
