import os
from dotenv import load_dotenv

load_dotenv()

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    # Cargado desde variable de entorno, nunca hardcodeado
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32))

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(_BASE, "uploads"))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB máximo

    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "txt", "docx"}

    DATABASE = os.environ.get("DATABASE", os.path.join(_BASE, "database.db"))

    # ── Seguridad de sesión / cookies ───────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True     # no accesible desde JS (mitiga XSS)
    SESSION_COOKIE_SECURE = True       # solo se envía por HTTPS
    SESSION_COOKIE_SAMESITE = "Lax"    # mitiga CSRF a nivel de navegador

    # ── Protección CSRF (Flask-WTF) ─────────────────────────────────────────
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # ── TLS / certificados ──────────────────────────────────────────────────
    CERT_FILE = os.environ.get("TLS_CERT", os.path.join(_BASE, "certs", "cert.pem"))
    KEY_FILE = os.environ.get("TLS_KEY", os.path.join(_BASE, "certs", "key.pem"))
    TLS_ENABLED = os.environ.get("TLS_ENABLED", "true").lower() in ("1", "true", "yes")
