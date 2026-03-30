from website import create_app, db, bcrypt
from website.models import User
import os

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='abiha@smart.com').first()
    if user:
        user.password_hash = bcrypt.generate_password_hash('Password123!').decode('utf-8')
        user.is_verified = True # Just in case
        db.session.commit()
        print("Password updated for abiha@smart.com")
    else:
        print("User abiha@smart.com not found")
