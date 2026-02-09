"""
Shared pytest fixtures and configuration for Kisan Smart tests
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from website import create_app, db
from website.models import User, Recommendation


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    from website import limiter
    with app.app_context():
        limiter.reset()
    return app


@pytest.fixture(scope="function")
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Create a database session for testing"""
    with app.app_context():
        # Create all tables
        db.create_all()

        yield db

        # Cleanup after test
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user"""
    user = User(username="testuser", email="test@example.com")
    user.set_password("TestPassword123!")

    db_session.session.add(user)
    db_session.session.commit()

    return user


@pytest.fixture(scope="function")
def authenticated_client(client, test_user):
    """Create an authenticated test client"""
    # Login and get token
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "TestPassword123!"},
    )

    if response.status_code == 200:
        token = response.json["data"]["access_token"]

        # Add authorization header to client
        class AuthenticatedClient:
            def __init__(self, client, token):
                self.client = client
                self.token = token

            def get(self, *args, **kwargs):
                kwargs.setdefault("headers", {})
                kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
                return self.client.get(*args, **kwargs)

            def post(self, *args, **kwargs):
                kwargs.setdefault("headers", {})
                kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
                return self.client.post(*args, **kwargs)

            def put(self, *args, **kwargs):
                kwargs.setdefault("headers", {})
                kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
                return self.client.put(*args, **kwargs)

            def delete(self, *args, **kwargs):
                kwargs.setdefault("headers", {})
                kwargs["headers"]["Authorization"] = f"Bearer {self.token}"
                return self.client.delete(*args, **kwargs)

        return AuthenticatedClient(client, token)

    return client


@pytest.fixture(scope="function")
def test_predictions(db_session, test_user):
    """Create test prediction data"""
    predictions = []

    crops = ["wheat", "rice", "maize", "cotton"]
    fertilizers = ["Urea", "DAP", "NPK", "Potash"]

    for i in range(10):
        pred = Recommendation(
            user_id=test_user.id,
            crop_type=crops[i % len(crops)],
            nitrogen=40 + i * 5,
            phosphorus=30 + i * 3,
            potassium=25 + i * 2,
            ph=6.5 + i * 0.1,
            moisture=60.0 + i,
            temperature=20.0 + i * 0.5,
            farm_area=2.0 + i * 0.5,
            fertilizer_type=fertilizers[i % len(fertilizers)],
            quantity=100.0 + i * 10,
            overall_confidence=75.0 + i,
        )
        predictions.append(pred)
        db_session.session.add(pred)

    db_session.session.commit()
    return predictions


@pytest.fixture(scope="function")
def sample_prediction_data():
    """Sample prediction input data"""
    return {
        "crop_type": "wheat",
        "nitrogen": 45.0,
        "phosphorus": 30.0,
        "potassium": 25.0,
        "ph": 6.8,
        "moisture": 65.0,
        "temperature": 22.5,
        "farm_area": 2.5,
    }
