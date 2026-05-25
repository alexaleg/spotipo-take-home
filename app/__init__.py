from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_object: object | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates")

    if config_object is not None:
        app.config.from_object(config_object)
    else:
        from config import Config

        app.config.from_object(Config)

    db.init_app(app)

    from app.routes import main_bp

    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
