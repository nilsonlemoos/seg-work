from flask import Blueprint, request, session, redirect, url_for, render_template, flash
import bcrypt
from .database import get_db
import functools

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str) -> str:
    """Hashing criptográfico seguro con bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    """Verificación de contraseña contra hash bcrypt."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False

def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped

@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        # Query parametrizada — sin SQL Injection posible
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        # Mensaje genérico — no revela si el usuario existe
        if user is None or not check_password(password, user["password_hash"]):
            flash("Credenciales inválidas.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("files.dashboard"))

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if len(username) < 3 or len(password) < 8:
            flash("Usuario mínimo 3 caracteres, contraseña mínimo 8.", "warning")
            return render_template("register.html")

        db = get_db()
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing:
            flash("El usuario ya existe.", "warning")
            return render_template("register.html")

        # Contraseña hasheada con bcrypt
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        db.commit()
        flash("Registro exitoso. Inicia sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
