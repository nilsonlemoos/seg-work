import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Cargado desde variable de entorno, nunca hardcodeado
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32))

    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB máximo

    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "txt", "docx"}

    DATABASE = os.path.join(os.path.dirname(__file__), "..", "database.db")
