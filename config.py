import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-12345')
    # PostgreSQL Connection: postgresql://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/kisan_smart')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
