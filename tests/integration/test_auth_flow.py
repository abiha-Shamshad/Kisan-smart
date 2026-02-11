"""
Integration tests for authentication and user management flows
"""

import pytest
from unittest.mock import patch
from website.models import User


@pytest.mark.integration
class TestRegistrationFlow:
    """Test complete user registration flow"""

    def test_successful_registration(self, client, db_session):
        """Test user can register successfully"""
        registration_data = {
            "username": "newuser",
            "full_name": "New User",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
        }

        response = client.post("/api/v1/auth/register", json=registration_data)

        # Should return 201 Created
        assert response.status_code == 201
        assert "data" in response.json

        # User should be created in database
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.is_verified is False  # Not verified yet

    @patch("website.utils.send_verification_email")
    def test_registration_sends_verification_email(self, mock_email, client, db_session):
        """Test verification email is sent on registration"""
        # Registration data with full_name
        registration_data = {
            "username": "testuser",
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "Password123!",
        }

        response = client.post("/api/v1/auth/register", json=registration_data)

        assert response.status_code == 201
        # Verification email should be sent
        mock_email.assert_called_once()

    def test_registration_duplicate_username(self, client, test_user):
        """Test registration fails with duplicate username"""
        registration_data = {
            "username": "testuser",  # Already exists
            "email": "different@example.com",
            "password": "Password123!",
        }

        response = client.post("/api/v1/auth/register", json=registration_data)

        # Should return 409 Conflict or 422
        assert response.status_code in [409, 422]
        assert "error" in response.json

    def test_registration_duplicate_email(self, client, test_user):
        """Test registration fails with duplicate email"""
        registration_data = {
            "username": "differentuser",
            "email": "test@example.com",  # Already exists
            "password": "Password123!",
        }

        response = client.post("/api/v1/auth/register", json=registration_data)

        assert response.status_code in [409, 422]
        assert "error" in response.json

    def test_registration_invalid_email(self, client, db_session):
        """Test registration fails with invalid email"""
        registration_data = {
            "username": "newuser",
            "email": "invalid-email",
            "password": "Password123!",
        }

        response = client.post("/api/v1/auth/register", json=registration_data)

        assert response.status_code == 422

    def test_registration_weak_password(self, client, db_session):
        """Test registration fails with weak password"""
        registration_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "123",  # Too weak
        }

        response = client.post("/api/v1/auth/register", json=registration_data)

        assert response.status_code == 422

    def test_email_verification_flow(self, client, db_session):
        """Test complete email verification flow"""
        # Register user
        registration_data = {
            "username": "verifyuser",
            "full_name": "Verify User",
            "email": "verify@example.com",
            "password": "Password123!",
        }

        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201

        # Get user
        user = User.query.filter_by(username="verifyuser").first()
        assert user.is_verified is False

        # Generate verification token
        token = user.generate_verification_token()

        # Verify email
        response = client.get(f"/api/v1/auth/verify/{token}")
        assert response.status_code == 200

        # User should now be verified
        db_session.session.refresh(user)
        assert user.is_verified is True


@pytest.mark.integration
class TestLoginFlow:
    """Test login and authentication flow"""

    def test_successful_login(self, client, test_user):
        """Test user can login with correct credentials"""
        login_data = {"email": "test@example.com", "password": "TestPassword123!"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        assert "data" in response.json
        assert "access_token" in response.json["data"]

        # Token should be a non-empty string
        token = response.json["data"]["access_token"]
        assert isinstance(token, str)
        assert len(token) > 20

    def test_login_wrong_password(self, client, test_user):
        """Test login fails with wrong password"""
        login_data = {"email": "test@example.com", "password": "WrongPassword!"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "error" in response.json

    def test_login_nonexistent_user(self, client, db_session):
        """Test login fails for non-existent user"""
        login_data = {"email": "nonexistent@example.com", "password": "Password123!"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    def test_protected_route_without_token(self, client, db_session):
        """Test protected routes require authentication"""
        response = client.get("/api/v1/history")

        # Should return 401 Unauthorized
        assert response.status_code == 401

    def test_protected_route_with_valid_token(self, authenticated_client):
        """Test protected routes work with valid token"""
        response = authenticated_client.get("/api/v1/history")

        # Should return 200 OK
        assert response.status_code == 200

    def test_protected_route_with_invalid_token(self, client):
        """Test protected routes reject invalid token"""
        response = client.get(
            "/api/v1/history", headers={"Authorization": "Bearer invalid-token-12345"}
        )

        assert response.status_code in [401, 422]


@pytest.mark.integration
class TestPasswordResetFlow:
    """Test password reset flow"""

    @patch("website.utils.send_reset_email")
    def test_request_password_reset(self, mock_email, client, test_user):
        """Test user can request password reset"""
        # Test password reset request
        response = client.post(
            "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        # Email should be sent
        mock_email.assert_called_once()

    def test_reset_password_with_token(self, client, test_user, db_session):
        """Test password reset with valid token"""
        # Generate reset token
        token = test_user.generate_password_reset_token()

        new_password = "NewPassword123!"

        response = client.post(
            "/api/v1/auth/reset-password", json={"password": new_password, "token": token}
        )

        assert response.status_code == 200

        # User should be able to login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": new_password},
        )

        assert login_response.status_code == 200

    def test_reset_password_invalid_token(self, client):
        """Test password reset fails with invalid token"""
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"password": "NewPassword123!", "token": "invalid-token"},
        )

        assert response.status_code in [400, 401]
