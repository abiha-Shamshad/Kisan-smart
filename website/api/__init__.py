from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flasgger import Swagger

jwt = JWTManager()
cors = CORS()
swagger = Swagger()

def init_api(app):
    """Initializes API extensions and registers blueprints."""
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # Swagger config
    app.config['SWAGGER'] = {
        'title': 'Kisan Smart API',
        'uiversion': 3,
        'version': '1.0.0',
        'description': 'AI-Based Fertilizer Recommendation System API'
    }
    swagger.init_app(app)

    # Import and register v1 blueprint
    from .v1 import api_v1
    app.register_blueprint(api_v1, url_prefix='/api/v1')
    
    # Register error handlers
    from .v1.utils.errors import register_error_handlers
    register_error_handlers(app)
