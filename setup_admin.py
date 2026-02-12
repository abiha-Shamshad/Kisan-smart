from website import create_app, db
from website.models import User

def setup_admin():
    app = create_app()
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        user = User.query.filter_by(email='admin@kisan.smart').first()
        if not user:
            user = User(
                email='admin@kisan.smart',
                username='admin',
                full_name='System Admin',
                is_verified=True
            )
            user.set_password('AdminPassword123!')
            db.session.add(user)
            db.session.commit()
            print('Admin user created successfully.')
        else:
            print('Admin user already exists.')

if __name__ == "__main__":
    setup_admin()
