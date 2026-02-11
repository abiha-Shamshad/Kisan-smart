from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Role(db.Model):
    __tablename__ = "roles"
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship("User", backref="role", lazy=True)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(50), unique=True, nullable=True
    )  # Set to nullable temporarily for existing users
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"), default=2)

    # Security/Status Fields
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_locked = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_login_attempt = db.Column(db.DateTime(timezone=True))
    locked_until = db.Column(db.DateTime(timezone=True))

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    def get_id(self):
        return str(self.id)

    def set_password(self, password):
        from . import bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        from . import bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_verification_token(self):
        from .utils import generate_token
        return generate_token(self.email, salt="email-confirm")

    @staticmethod
    def verify_verification_token(token):
        from .utils import verify_token
        return verify_token(token, salt="email-confirm")

    def generate_password_reset_token(self):
        from .utils import generate_token
        return generate_token(self.email, salt="password-reset")


import uuid
from datetime import datetime


def generate_prediction_id():
    return f"pred_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"


class Recommendation(db.Model):
    __tablename__ = "recommendations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    prediction_id = db.Column(
        db.String(50), 
        unique=True, 
        nullable=False, 
        default=generate_prediction_id
    )

    # Input data
    crop_type = db.Column(db.String(50))
    nitrogen = db.Column(db.Float)
    phosphorus = db.Column(db.Float)
    potassium = db.Column(db.Float)
    ph = db.Column(db.Float)
    moisture = db.Column(db.Float)
    temperature = db.Column(db.Float)
    farm_area = db.Column(db.Float)
    growth_stage = db.Column(db.String(50))

    # Predictions
    fertilizer_type = db.Column(db.String(100))
    quantity = db.Column(db.Float)
    quantity_unit = db.Column(db.String(20), default="kg/hectare")

    # Confidence
    type_confidence = db.Column(db.Float)
    quantity_confidence = db.Column(db.Float)
    overall_confidence = db.Column(db.Float)
    confidence_level = db.Column(db.String(20))

    # Metadata
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = db.relationship("User", backref="recommendations")
