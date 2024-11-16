from flask import Flask
import os

from .auxiliaries import create_instance_folder

from .globals import DB_SQLITE


def create(test_config: dict[str : str | bool] | None = None) -> Flask:
    """App factory."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dd8e010217eb709151bc670fe141eb3ed56b5e",
        DATABASE=os.path.join(app.instance_path, DB_SQLITE),
        APP_NAME="HJBlog",
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    create_instance_folder(app.instance_path)

    from . import db

    db.init_app(app)

    from . import admin_management

    admin_management.init_app(app)

    from .bps.main import routes

    app.register_blueprint(routes.bp)
    app.add_url_rule("/", endpoint="index")

    from .bps.auth import routes

    app.register_blueprint(routes.bp)

    from .bps.user_actions.routes import bp

    app.register_blueprint(bp)

    from .bps.user_profile.routes import bp

    app.register_blueprint(bp)

    from .bps.errors.handlers import bp

    app.register_blueprint(bp)

    return app
