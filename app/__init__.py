"""Flask application factory."""
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
csrf = CSRFProtect()


def create_app(config_class: type = Config) -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # The JSON API uses cookie auth; exempt it from CSRF (token-less clients).
    from app.api import api_bp as _api_bp_for_csrf
    csrf.exempt(_api_bp_for_csrf)

    # Register models so SQLAlchemy knows about them
    from app import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id: str):
        return models.User.query.get(int(user_id))

    # Blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.projects import projects_bp
    from app.tasks import tasks_bp
    from app.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create tables on first run (safe — no-op if they exist)
    with app.app_context():
        db.create_all()

    # Jinja helpers
    from datetime import date
    app.jinja_env.globals["today"] = date.today

    return app
