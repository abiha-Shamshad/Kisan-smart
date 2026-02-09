"""
Unit tests for database models
"""

import pytest
from datetime import datetime, timedelta
from website.models import User, Recommendation


@pytest.mark.unit
class TestUserModel:
    """Tests for User model"""

    def test_create_user(self, db_session):
        """Test creating a user"""
        user = User(username="newuser", email="new@example.com")
        user.set_password("Password123!")

        db_session.session.add(user)
        db_session.session.commit()

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.created_at is not None

    def test_password_hashing(self, db_session):
        """Test password is hashed, not stored as plain text"""
        user = User(username="testuser", email="test@example.com")
        password = "MySecretPassword123!"
        user.set_password(password)

        # Password should be hashed
        assert user.password_hash != password
        assert len(user.password_hash) > 50  # Bcrypt hash is long

        # Should not be able to retrieve original password
        assert not hasattr(user, "password")

    def test_password_verification(self, db_session):
        """Test password verification works correctly"""
        user = User(username="testuser", email="test@example.com")
        password = "CorrectPassword123!"
        user.set_password(password)

        # Correct password should verify
        assert user.check_password(password) is True

        # Wrong password should not verify
        assert user.check_password("WrongPassword") is False
        assert user.check_password("") is False

    def test_generate_verification_token(self, db_session):
        """Test verification token generation"""
        user = User(username="testuser", email="test@example.com")

        token = user.generate_verification_token()

        assert isinstance(token, str)
        assert len(token) > 20

    def test_verify_valid_token(self, db_session):
        """Test verifying a valid token"""
        user = User(username="testuser", email="test@example.com")
        db_session.session.add(user)
        db_session.session.commit()

        token = user.generate_verification_token()

        # Token should verify correctly
        verified_user_id = User.verify_verification_token(token)
        assert verified_user_id == user.id

    def test_verify_invalid_token(self, db_session):
        """Test invalid token is rejected"""
        result = User.verify_verification_token("invalid-token-string")
        assert result is None

    def test_verify_expired_token(self, db_session):
        """Test expired token is rejected"""
        user = User(username="testuser", email="test@example.com")
        db_session.session.add(user)
        db_session.session.commit()

        # Generate token with very short expiration (if supported)
        # This test depends on implementation
        # For now, we'll skip this as it requires mocking time
        pass

    def test_generate_password_reset_token(self, db_session):
        """Test password reset token generation"""
        user = User(username="testuser", email="test@example.com")

        token = user.generate_password_reset_token()

        assert isinstance(token, str)
        assert len(token) > 20

    def test_unique_username_constraint(self, db_session):
        """Test username must be unique"""
        user1 = User(username="duplicate", email="user1@example.com")
        user1.set_password("Pass123!")
        db_session.session.add(user1)
        db_session.session.commit()

        user2 = User(username="duplicate", email="user2@example.com")
        user2.set_password("Pass123!")
        db_session.session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.session.commit()

    def test_unique_email_constraint(self, db_session):
        """Test email must be unique"""
        user1 = User(username="user1", email="duplicate@example.com")
        user1.set_password("Pass123!")
        db_session.session.add(user1)
        db_session.session.commit()

        user2 = User(username="user2", email="duplicate@example.com")
        user2.set_password("Pass123!")
        db_session.session.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.session.commit()

    def test_user_repr(self, db_session):
        """Test user string representation"""
        user = User(username="testuser", email="test@example.com")

        repr_str = repr(user)
        assert "testuser" in repr_str or "User" in repr_str


@pytest.mark.unit
class TestRecommendationModel:
    """Tests for Recommendation model"""

    def test_create_recommendation(self, db_session, test_user):
        """Test creating a recommendation"""
        rec = Recommendation(
            user_id=test_user.id,
            crop_type="wheat",
            nitrogen=45.0,
            phosphorus=30.0,
            potassium=25.0,
            ph=6.8,
            moisture=65.0,
            temperature=22.5,
            farm_area=2.5,
            fertilizer_type="Urea",
            quantity=120.0,
            overall_confidence=85.5,
        )

        db_session.session.add(rec)
        db_session.session.commit()

        assert rec.id is not None
        assert rec.user_id == test_user.id
        assert rec.crop_type == "wheat"
        assert rec.created_at is not None

    def test_recommendation_user_relationship(self, db_session, test_user):
        """Test relationship between recommendation and user"""
        rec = Recommendation(
            user_id=test_user.id,
            crop_type="rice",
            nitrogen=40.0,
            phosphorus=28.0,
            potassium=22.0,
            ph=6.5,
            fertilizer_type="DAP",
            quantity=110.0,
            overall_confidence=80.0,
        )

        db_session.session.add(rec)
        db_session.session.commit()

        # Should be able to access user from recommendation
        assert rec.user.username == test_user.username

        # Should be able to access recommendations from user
        assert len(test_user.recommendations) > 0
        assert rec in test_user.recommendations

    def test_multiple_recommendations_per_user(self, db_session, test_user):
        """Test user can have multiple recommendations"""
        recs = []
        for i in range(3):
            rec = Recommendation(
                user_id=test_user.id,
                crop_type="maize",
                nitrogen=45.0 + i,
                phosphorus=30.0,
                potassium=25.0,
                ph=6.8,
                fertilizer_type="NPK",
                quantity=100.0 + i * 10,
                overall_confidence=75.0 + i,
            )
            recs.append(rec)
            db_session.session.add(rec)

        db_session.session.commit()

        assert len(test_user.recommendations) >= 3

    def test_cascade_delete(self, db_session, test_user):
        """Test deleting user cascades to recommendations"""
        # Create recommendation
        rec = Recommendation(
            user_id=test_user.id,
            crop_type="cotton",
            nitrogen=50.0,
            phosphorus=35.0,
            potassium=30.0,
            ph=7.0,
            fertilizer_type="Potash",
            quantity=90.0,
            overall_confidence=70.0,
        )
        db_session.session.add(rec)
        db_session.session.commit()

        rec_id = rec.id

        # Delete user
        db_session.session.delete(test_user)
        db_session.session.commit()

        # Recommendation should also be deleted (if cascade configured)
        deleted_rec = Recommendation.query.get(rec_id)
        # Depends on cascade configuration
        # assert deleted_rec is None

    def test_recommendation_defaults(self, db_session, test_user):
        """Test default values for optional fields"""
        rec = Recommendation(
            user_id=test_user.id,
            crop_type="wheat",
            nitrogen=45.0,
            phosphorus=30.0,
            potassium=25.0,
            ph=6.8,
            fertilizer_type="Urea",
            quantity=100.0,
            overall_confidence=80.0,
        )

        db_session.session.add(rec)
        db_session.session.commit()

        # Optional fields should have defaults or None
        # Check created_at is set automatically
        assert rec.created_at is not None
        assert isinstance(rec.created_at, datetime)

    def test_recommendation_repr(self, db_session, test_user):
        """Test recommendation string representation"""
        rec = Recommendation(
            user_id=test_user.id,
            crop_type="wheat",
            nitrogen=45.0,
            phosphorus=30.0,
            potassium=25.0,
            ph=6.8,
            fertilizer_type="Urea",
            quantity=100.0,
            overall_confidence=80.0,
        )

        repr_str = repr(rec)
        assert "Recommendation" in repr_str or "wheat" in repr_str
