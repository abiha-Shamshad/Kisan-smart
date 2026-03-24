from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)


def create_app(config_name=None):
    # Root of the project (one level up from this file)
    project_root = path.abspath(path.join(path.dirname(__file__), ".."))
    instance_path = path.join(project_root, "instance")
    
    # Ensure instance folder exists
    if not path.exists(instance_path):
        import os
        os.makedirs(instance_path)

    app = Flask(__name__, instance_path=instance_path, instance_relative_config=True)
    
    from config import get_config
    config_obj = get_config(config_name)
    app.config.from_object(config_obj)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    from .auth import auth
    from .views import views
    from .api import init_api

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/")

    # Initialize API
    init_api(app)

    from .models import User

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
