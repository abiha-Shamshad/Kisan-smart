import pytest
from website.models import User

class TestProfileFlow:
    def test_get_profile(self, authenticated_client, test_user):
        """Test getting current user profile"""
        response = authenticated_client.get("/api/v1/profile")
        assert response.status_code == 200
        assert response.json["data"]["email"] == test_user.email
        assert response.json["data"]["username"] == test_user.username

    def test_update_profile(self, authenticated_client, test_user, db_session):
        """Test updating user profile"""
        response = authenticated_client.put("/api/v1/profile", json={
            "full_name": "Updated Name",
            "phone_number": "0987654321"
        })
        assert response.status_code == 200
        assert response.json["data"]["full_name"] == "Updated Name"
        
        # Verify in DB
        user = User.query.get(test_user.id)
        assert user.full_name == "Updated Name"

    def test_change_password(self, authenticated_client, test_user, db_session):
        """Test changing user password"""
        response = authenticated_client.put("/api/v1/profile/password", json={
            "old_password": "TestPassword123!",
            "new_password": "NewPassword123!"
        })
        assert response.status_code == 200
        assert b"Password changed" in response.data or b"successfully" in response.data

    def test_delete_account(self, authenticated_client, test_user, db_session):
        """Test deleting user account"""
        response = authenticated_client.delete("/api/v1/profile")
        assert response.status_code == 200
        
        # Verify in DB - soft delete
        user = User.query.get(test_user.id)
        assert user is not None
        assert user.is_active is False
