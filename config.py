import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-12345')
    # MySQL Connection: mysql+mysqlconnector://user:password@host/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+mysqlconnector://root:@localhost/kisan_smart')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
