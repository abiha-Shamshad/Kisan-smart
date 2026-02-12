import pytest
from flask import url_for
from website.decorators import role_required, admin_required, farmer_required
from website.models import User, Role
from flask_login import login_user

def test_role_required_authorized(app, db_session):
    """Test role_required with authorized user"""
    with app.test_request_context():
        role = Role.query.filter_by(role_name="Admin").first()
        user = User(email="admin@test.com", username="admin", role_id=role.role_id)
        user.set_password("Pass123!")
        db_session.session.add(user)
        db_session.session.commit()
        
        login_user(user)
        
        @role_required(["Admin"])
        def protected_route():
            return "Success"
            
        assert protected_route() == "Success"

def test_role_required_unauthorized_role(app, db_session):
    """Test role_required with unauthorized role"""
    with app.test_request_context():
        role = Role.query.filter_by(role_name="Farmer").first()
        user = User(email="farmer@test.com", username="farmer", role_id=role.role_id)
        user.set_password("Pass123!")
        db_session.session.add(user)
        db_session.session.commit()
        
        login_user(user)
        
        @role_required(["Admin"])
        def protected_route():
            return "Success"
            
        response = protected_route()
        assert response.status_code == 302 # Redirect to home
        assert response.location == url_for("views.home")

def test_role_required_unauthenticated(app):
    """Test role_required with unauthenticated user"""
    with app.test_request_context():
        @role_required(["Admin"])
        def protected_route():
            return "Success"
            
        response = protected_route()
        assert response.status_code == 302 # Redirect to login
        assert response.location == url_for("auth.login")

def test_admin_required(app, db_session):
    """Test admin_required decorator"""
    with app.test_request_context():
        role = Role.query.filter_by(role_name="Admin").first()
        user = User(email="admin2@test.com", username="admin2", role_id=role.role_id)
        user.set_password("Pass123!")
        db_session.session.add(user)
        db_session.session.commit()
        
        login_user(user)
        
        @admin_required
        def admin_route():
            return "Admin Success"
            
        assert admin_route() == "Admin Success"

def test_farmer_required(app, db_session):
    """Test farmer_required decorator"""
    with app.test_request_context():
        role = Role.query.filter_by(role_name="Farmer").first()
        user = User(email="farmer2@test.com", username="farmer2", role_id=role.role_id)
        user.set_password("Pass123!")
        db_session.session.add(user)
        db_session.session.commit()
        
        login_user(user)
        
        @farmer_required
        def farmer_route():
            return "Farmer Success"
            
        assert farmer_route() == "Farmer Success"
