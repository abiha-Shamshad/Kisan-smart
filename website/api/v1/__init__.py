from flask import Blueprint

api_v1 = Blueprint("api_v1", __name__)

# Import sub-blueprints
from .auth.routes import auth_api
from .prediction.routes import predict_api
from .history.routes import history_api
from .profile.routes import profile_api
from .reference.routes import reference_api

# Register sub-blueprints
api_v1.register_blueprint(auth_api, url_prefix="/auth")
api_v1.register_blueprint(predict_api, url_prefix="/predict")
api_v1.register_blueprint(history_api, url_prefix="/history")
api_v1.register_blueprint(profile_api, url_prefix="/profile")
api_v1.register_blueprint(reference_api, url_prefix="/reference")


@api_v1.route("/health")
def health_check():
    return {"status": "healthy", "version": "v1.0.0"}
