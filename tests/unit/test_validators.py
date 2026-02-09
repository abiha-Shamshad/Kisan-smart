"""
Unit tests for validation functions
"""

import pytest


@pytest.mark.unit
class TestValidators:
    """Tests for input validation functions"""

    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        from website.utils.validators import validate_email

        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "test123@test-domain.com",
        ]

        for email in valid_emails:
            assert validate_email(email) is True, f"{email} should be valid"

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        from website.utils.validators import validate_email

        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user @example.com",
            "",
            "user@.com",
        ]

        for email in invalid_emails:
            assert validate_email(email) is False, f"{email} should be invalid"

    def test_validate_password_strength(self):
        """Test password strength validation"""
        from website.utils.validators import validate_password_strength

        # Strong password
        result = validate_password_strength("StrongPass123!")
        assert result["is_valid"] is True
        assert result["score"] >= 3

        # Weak password (too short)
        result = validate_password_strength("Pass1!")
        assert result["is_valid"] is False

        # Weak password (no numbers)
        result = validate_password_strength("Password!")
        assert result["is_valid"] is False

        # Weak password (no special chars)
        result = validate_password_strength("Password123")
        assert result["is_valid"] is False

    def test_validate_numeric_range(self):
        """Test numeric range validation"""
        from website.utils.validators import validate_numeric_range

        # Valid values
        assert validate_numeric_range(50, 0, 100) is True
        assert validate_numeric_range(0, 0, 100) is True
        assert validate_numeric_range(100, 0, 100) is True

        # Invalid values
        assert validate_numeric_range(-1, 0, 100) is False
        assert validate_numeric_range(101, 0, 100) is False

    def test_validate_ph_value(self):
        """Test pH value validation"""
        from website.utils.validators import validate_ph

        # Valid pH values
        assert validate_ph(7.0) is True
        assert validate_ph(6.5) is True
        assert validate_ph(3.0) is True
        assert validate_ph(10.0) is True

        # Invalid pH values
        assert validate_ph(2.9) is False
        assert validate_ph(10.1) is False
        assert validate_ph(-1) is False

    def test_validate_npk_values(self):
        """Test NPK nutrient validation"""
        from website.utils.validators import validate_npk

        # Valid NPK values
        assert validate_npk(nitrogen=50, phosphorus=30, potassium=25) is True
        assert validate_npk(nitrogen=0, phosphorus=0, potassium=0) is True
        assert validate_npk(nitrogen=200, phosphorus=200, potassium=200) is True

        # Invalid NPK values
        assert validate_npk(nitrogen=-1, phosphorus=30, potassium=25) is False
        assert validate_npk(nitrogen=50, phosphorus=201, potassium=25) is False

    def test_validate_crop_type(self):
        """Test crop type validation"""
        from website.utils.validators import validate_crop_type

        valid_crops = ["wheat", "rice", "maize", "cotton", "sugarcane"]

        for crop in valid_crops:
            assert validate_crop_type(crop) is True

        # Invalid crop
        assert validate_crop_type("invalid_crop") is False
        assert validate_crop_type("") is False

    def test_validate_phone_number(self):
        """Test phone number validation"""
        from website.utils.validators import validate_phone

        valid_phones = ["+1234567890", "1234567890", "+1 (555) 123-4567"]

        for phone in valid_phones:
            assert validate_phone(phone) is True

        # Invalid phones
        assert validate_phone("123") is False
        assert validate_phone("abcd") is False
