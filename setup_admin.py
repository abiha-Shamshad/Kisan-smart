import os
from website import create_app, db
from website.models import User, Role

def setup_admin():
    app = create_app()
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # 1. Ensure Roles Exist
        admin_role = Role.query.filter_by(role_id=1).first()
        if not admin_role:
            admin_role = Role(role_id=1, role_name='Admin')
            db.session.add(admin_role)
            print("Created Admin role (role_id=1)")
            
        user_role = Role.query.filter_by(role_id=2).first()
        if not user_role:
            user_role = Role(role_id=2, role_name='User')
            db.session.add(user_role)
            print("Created User role (role_id=2)")
        
        db.session.commit()

        # 2. Setup Admin User
        admin_password = os.environ.get('ADMIN_PASSWORD', 'AdminPassword123!')
        if os.environ.get('FLASK_ENV') == 'production' and admin_password == 'AdminPassword123!':
            print('WARNING: Using default admin password in production! Set ADMIN_PASSWORD.')

        user = User.query.filter_by(email='admin@kisan.smart').first()
        if not user:
            user = User(
                email='admin@kisan.smart',
                username='admin',
                full_name='System Admin',
                role_id=1,  # Admin role
                is_verified=True
            )
            user.set_password(admin_password)
            db.session.add(user)
            db.session.commit()
            print('Admin user created successfully with role_id=1.')
        else:
            if user.role_id != 1:
                user.role_id = 1
                db.session.commit()
                print('Updated existing admin user to role_id=1.')
            else:
                print('Admin user already exists with correct role.')

if __name__ == "__main__":
    setup_admin()
