from flask import Flask
from .config import Config
from .database import init_db

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    init_db(app)

    from .auth import auth_bp
    from .files import files_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)

    return app
