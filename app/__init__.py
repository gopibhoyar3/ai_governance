from flask import Flask

from app.config import Config
from app.extensions import db, migrate
from app.errors import register_error_handlers
from app.routes.health import health_bp
from app.routes.risk_routes import risk_bp
from app.routes.use_cases import use_cases_bp
from app.routes.dashboard import dashboard_bp
from app.routes.governance import governance_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    register_error_handlers(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(risk_bp, url_prefix="/api/risk")
    app.register_blueprint(use_cases_bp, url_prefix="/api/use-cases")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(governance_bp, url_prefix="/api/governance")

    return app
