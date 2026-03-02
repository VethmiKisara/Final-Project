from flask import Flask
from .config import Config
from .db import init_db
from .routes.pages import pages_bp
from .routes.auth import auth_bp
from .routes.api import api_bp

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    init_db(app)

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Make the logged-in user available in templates
    @app.context_processor
    def _inject_current_user():
        from flask import session
        return {
            "current_user": {
                "id": session.get("user_id"),
                "username": session.get("username"),
                "email": session.get("email"),
            }
            if session.get("user_id")
            else None
        }

    return app
