import os
import sys

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    print("Attempting to import website...")
    from website import create_app, db
    print("Import successful!")
    
    print("Creating app...")
    app = create_app('testing')
    print("App created!")
    
    with app.app_context():
        print("Initializing database...")
        db.create_all()
        print("Database initialized!")
        
        from website.models import User
        print("User model imported!")
        
        # Check if user exists
        user = User.query.filter_by(username='debug_user').first()
        if user:
            print(f"User found: {user.username}")
        else:
            print("Creating debug user...")
            user = User(username='debug_user', email='debug@example.com')
            user.set_password('DebugPass123!')
            db.session.add(user)
            db.session.commit()
            print("Debug user created!")
            
    print("DIAGNOSTIC SUCCESSFUL")
except Exception as e:
    print(f"DIAGNOSTIC FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
