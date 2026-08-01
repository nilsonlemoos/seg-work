from flask import Flask, request
from flask_wtf import CSRFProtect
from .config import Config
from .database import init_db

csrf = CSRFProtect()

# Headers de seguridad recomendados por la industria (OWASP Secure Headers)
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; style-src 'self' https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
}


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    init_db(app)

    csrf.init_app(app)

    from .auth import auth_bp
    from .files import files_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)

    @app.after_request
    def add_security_headers(resp):
        for header, value in _SECURITY_HEADERS.items():
            resp.headers.setdefault(header, value)
        # HSTS solo sobre HTTPS (evita header en peticiones HTTP planas)
        if request.is_secure:
            resp.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return resp

    return app
