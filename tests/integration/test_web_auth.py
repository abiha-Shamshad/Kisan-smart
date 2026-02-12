import pytest
from flask import url_for
from website.models import User, Role
from website import bcrypt

class TestWebAuthFlow:
    def test_register_page_load(self, client):
        """Test registration page loads"""
        response = client.get("/register")
        assert response.status_code == 200
        assert b"Register" in response.data

    def test_login_page_load(self, client):
        """Test login page loads"""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_successful_web_registration(self, client, db_session):
        """Test successful registration through web form"""
        response = client.post("/register", data={
            "username": "webuser",
            "email": "web@test.com",
            "full_name": "Web User",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "phone_number": "1234567890"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Account created" in response.data
        
        user = User.query.filter_by(email="web@test.com").first()
        assert user is not None
        assert user.username == "webuser"

    def test_successful_web_login(self, client, db_session):
        """Test successful login through web form"""
        # Create user first
        user = User(email="login@test.com", username="loginuser", full_name="Login User", is_verified=True)
        user.set_password("Password123!")
        db_session.session.add(user)
        db_session.session.commit()
        
        response = client.post("/login", data={
            "email": "login@test.com",
            "password": "Password123!",
            "remember": False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b"Logout" in response.data # Assuming home shows logout when auth

    def test_web_logout(self, client, db_session):
        """Test web logout"""
        user = User(email="logout@test.com", username="logoutuser", is_verified=True)
        user.set_password("Password123!")
        db_session.session.add(user)
        db_session.session.commit()
        
        client.post("/login", data={
            "email": "logout@test.com",
            "password": "Password123!"
        })
        
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_forgot_password_page(self, client):
        """Test forgot password page loads"""
        response = client.get("/forgot-password")
        assert response.status_code == 200
        assert b"Reset Password" in response.data
