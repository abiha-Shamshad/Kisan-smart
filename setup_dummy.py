from website import create_app, db, bcrypt
from website.models import User, Role

app = create_app()
with app.app_context():
    # 1. Create Roles
    if not Role.query.filter_by(role_name='User').first():
        user_role = Role(role_name='User')
        admin_role = Role(role_name='Admin')
        db.session.add(user_role)
        db.session.add(admin_role)
        db.session.commit()
    
    # 2. Create Dummy User
    role = Role.query.filter_by(role_name='User').first()
    if not User.query.filter_by(email='abiha@smart.com').first():
        hashed_password = bcrypt.generate_password_hash('12345678').decode('utf-8')
        user = User(
            username='abiha',
            email='abiha@smart.com',
            password_hash=hashed_password,
            full_name='Abiha Shamshad',
            role=role,
            is_verified=True,
            lat=32.57,
            lon=74.08,
            crop='Wheat'
        )
        db.session.add(user)
        db.session.commit()
        print("User abiha@smart.com created successfully.")
    else:
        print("User already exists.")
