from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db
import functools
import time

auth_bp = Blueprint("auth", __name__)

login_attempts = {}

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
    ip = request.remote_addr or "unknown"

    if request.method == "POST":
        now = time.time()
        attempts = login_attempts.get(ip, {"count": 0, "first": now})

        # Bloquear si excede 5 intentos en 60 segundos
        if attempts["count"] >= 5 and now - attempts["first"] < 60:
            flash("Demasiados intentos. Espere 60 segundos.", "danger")
            return render_template("login.html")

        # Delay progresivo desde el 3er intento
        if attempts["count"] >= 3:
            time.sleep(5)

        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            # Registrar intento fallido
            if attempts["count"] == 0:
                login_attempts[ip] = {"count": 1, "first": now}
            else:
                attempts["count"] += 1

            flash("Credenciales inválidas.", "danger")
            return render_template("login.html")

        # Login exitoso — limpiar intentos
        login_attempts.pop(ip, None)
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

        # Contraseña hasheada con bcrypt via werkzeug
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()
        flash("Registro exitoso. Inicia sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
