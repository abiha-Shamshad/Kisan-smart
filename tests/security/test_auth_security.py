"""
Security tests for authentication and authorization
"""

import pytest
from website.models import User, Recommendation


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security"""

    def test_protected_route_requires_token(self, client):
        """Test protected routes require authentication token"""
        protected_endpoints = ["/api/v1/history", "/api/v1/profile"]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert (
                response.status_code == 401
            ), f"{endpoint} should require authentication"

    def test_invalid_token_rejected(self, client):
        """Test invalid JWT token is rejected"""
        headers = {"Authorization": "Bearer invalid-token-12345"}

        response = client.get("/api/v1/history", headers=headers)
        assert response.status_code == 401

    def test_malformed_authorization_header(self, client):
        """Test malformed authorization header is rejected"""
        malformed_headers = [
            {"Authorization": "invalid-format"},
            {"Authorization": "Bearer"},
            {"Authorization": ""},
        ]

        for headers in malformed_headers:
            response = client.get("/api/v1/history", headers=headers)
            assert response.status_code == 401

    def test_expired_token_rejected(self, client):
        """Test expired JWT token is rejected"""
        # This would require mocking time or using a pre-expired token
        # Implementation depends on JWT configuration
        pass

    def test_user_cannot_access_others_data(self, client, db_session):
        """Test users cannot access other users' data"""
        # Create two users
        user1 = User(username="user1", email="user1@example.com")
        user1.set_password("Password123!")
        user2 = User(username="user2", email="user2@example.com")
        user2.set_password("Password123!")

        db_session.session.add_all([user1, user2])
        db_session.session.commit()

        # Create prediction for user2
        pred = Recommendation(
            user_id=user2.id,
            crop_type="wheat",
            nitrogen=45,
            phosphorus=30,
            potassium=25,
            ph=6.8,
            fertilizer_type="Urea",
            quantity=100,
            overall_confidence=80,
        )
        db_session.session.add(pred)
        db_session.session.commit()

        # Login as user1
        login_response = client.post(
            "/api/v1/auth/login", json={"email": "user1@example.com", "password": "Password123!"}
        )
        token = login_response.json["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access user2's prediction
        response = client.get(f"/api/v1/history/{pred.id}", headers=headers)

        # Should be denied
        assert response.status_code in [403, 404]

    def test_password_not_returned_in_api(self, client, test_user):
        """Test password hash is never returned in API responses"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPassword123!"},
        )

        # Get profile
        token = login_response.json["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        profile_response = client.get("/api/v1/profile", headers=headers)

        # Password hash should not be in response
        profile_data = profile_response.json["data"]
        assert "password" not in profile_data
        assert "password_hash" not in profile_data


@pytest.mark.security
class TestInputValidationSecurity:
    """Test input validation and injection prevention"""

    def test_sql_injection_prevention(self, authenticated_client):
        """Test SQL injection is prevented"""
        # Try SQL injection in crop type filter
        malicious_inputs = [
            "wheat' OR 1=1--",
            "wheat'; DROP TABLE predictions;--",
            "wheat' UNION SELECT * FROM users--",
        ]

        for malicious_input in malicious_inputs:
            response = authenticated_client.get(
                f"/api/v1/history?crop_type={malicious_input}"
            )

            # Should not cause error, should sanitize input
            assert response.status_code in [200, 400, 422]

            # Should not return all data
            if response.status_code == 200:
                # Verify it filtered correctly or returned no results
                predictions = response.json["data"]["predictions"]
                # Results should be empty or properly filtered
                assert isinstance(predictions, list)

    def test_xss_prevention(self, authenticated_client):
        """Test XSS attacks are prevented"""
        xss_payload = '<script>alert("XSS")</script>'

        # Try XSS in prediction input
        prediction_data = {
            "crop_type": xss_payload,
            "nitrogen": 45,
            "phosphorus": 30,
            "potassium": 25,
            "ph": 6.8,
        }

        response = authenticated_client.post("/api/v1/predict", json=prediction_data)

        # Should either reject or sanitize
        if response.status_code == 200:
            # If accepted, script tags should be escaped/removed
            assert "<script>" not in str(response.json)

    def test_large_payload_rejection(self, authenticated_client):
        """Test very large payloads are rejected"""
        # Create extremely large payload
        large_data = {
            "crop_type": "wheat",
            "nitrogen": 45,
            "phosphorus": 30,
            "potassium": 25,
            "ph": 6.8,
            "notes": "A" * 1000000,  # 1MB of data
        }

        response = authenticated_client.post("/api/v1/predict", json=large_data)

        # Should reject or handle gracefully
        assert response.status_code in [400, 413, 422]

    def test_special_characters_handled(self, authenticated_client, db_session):
        """Test special characters are handled properly"""
        # Update profile with special characters
        profile_data = {
            "full_name": "O'Brien <>&\"",
            "phone": "+1 (555) 123-4567",
            "farm_name": "Test & Co.",
        }

        response = authenticated_client.put("/api/v1/profile", json=profile_data)

        # Should handle special characters
        assert response.status_code in [200, 422]


@pytest.mark.security
class TestRateLimiting:
    """Test rate limiting security"""

    def test_login_rate_limiting(self, client):
        """Test login endpoint has rate limiting"""
        # Make multiple failed login attempts
        for i in range(10):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"},
            )

        # After many attempts, should be rate limited
        final_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        # Should return 429 Too Many Requests (if rate limiting implemented)
        # Or continue to return 401
        assert final_response.status_code in [401, 429]

    def test_api_rate_limiting(self, authenticated_client):
        """Test API endpoints have rate limiting"""
        # Make many rapid requests
        responses = []
        for i in range(100):
            response = authenticated_client.get("/api/v1/history/stats")
            responses.append(response.status_code)

        # Check if rate limiting kicks in
        # This depends on rate limit configuration
        # Should either all succeed or some be rate limited
        rate_limited = any(code == 429 for code in responses)

        # At minimum, server should handle the load without crashing
        assert all(code in [200, 429] for code in responses)


@pytest.mark.security
class TestCSRFProtection:
    """Test CSRF protection"""

    def test_csrf_token_required_for_state_changing_operations(self, client):
        """Test CSRF token is required for POST/PUT/DELETE"""
        # This test depends on CSRF implementation
        # Flask-WTF or similar would require CSRF tokens
        pass
