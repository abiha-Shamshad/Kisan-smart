import pytest
from website import db
from website.models import User

def test_db_setup(app):
    with app.app_context():
        db.create_all()
        # Check tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nTables found: {tables}")
        assert "users" in tables
