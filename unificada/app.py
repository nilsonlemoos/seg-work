"""Aplicación unificada (estilo DVWA) con selector de modo seguro/inseguro.

Unifica v1-insecure y v2-secure en una sola app:

  - Modo INSEGURO: replica las vulnerabilidades de v1 (SQLi, RCE, XSS
    reflejado/almacenado, CSRF, contraseñas en texto plano, IDOR, sin auth).
  - Modo SEGURO: replica las mitigaciones de v2 (queries parametrizadas,
    bcrypt, CSRF + Referer estricto, security headers, cookies seguras,
    rate-limiting, filtro por owner_id).

El modo se persiste en sesión y se cambia con el botón del navbar.
Transporte: HTTPS (puerto 8444) — el TLS es un nivel de aplicación, no por modo.
"""
from urllib.parse import urlparse

from flask import (
    Flask, request, session, redirect, url_for,
    render_template, send_from_directory, jsonify, flash, abort
)
from flask_wtf.csrf import generate_csrf, validate_csrf
from werkzeug.utils import secure_filename
from wtforms import ValidationError
import bcrypt
import sqlite3
import os
import uuid
import time
import functools

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE", os.path.join(BASE, "database.db"))
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE, "uploads"))
CERT_FILE = os.environ.get("TLS_CERT", os.path.join(BASE, "certs", "cert.pem"))
KEY_FILE = os.environ.get("TLS_KEY", os.path.join(BASE, "certs", "key.pem"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-insegura-para-demo")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

# Cookies HttpOnly y SameSite siempre; Secure se activa por modo en before_request
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Token CSRF disponible en plantillas (validación manual, por modo)
app.jinja_env.globals["csrf_token"] = generate_csrf

# Headers de seguridad (solo se aplican en modo seguro)
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; style-src 'self' https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
}

# Rate-limiting del login (solo en modo seguro)
login_attempts = {}


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def is_secure():
    return session.get("mode") == "seguro"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT,
            password_hash TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT,
            stored_name TEXT,
            owner_id INTEGER
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hashing criptográfico seguro con bcrypt (igual que v2)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped


def allowed_file(filename):
    allowed = {"pdf", "png", "jpg", "jpeg", "gif", "txt", "docx"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _same_origin(a, b):
    pa, pb = urlparse(a), urlparse(b)
    return (pa.scheme, pa.hostname, pa.port) == (pb.scheme, pb.hostname, pb.port)


# ─── MIDDLEWARE (por modo) ───────────────────────────────────────────────────

@app.before_request
def protect():
    secure = is_secure()

    # Cookie Secure solo en modo seguro (en modo inseguro se manda por HTTP)
    app.config["SESSION_COOKIE_SECURE"] = secure

    if secure and request.method in ("POST", "PUT", "PATCH", "DELETE"):
        # Protección CSRF (igual que v2): token + Referer estricto sobre HTTPS
        token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        try:
            validate_csrf(token)
        except ValidationError:
            abort(400, "The CSRF token is missing or invalid.")

        if request.is_secure:
            if not request.referrer:
                abort(400, "The referrer header is missing.")
            if not _same_origin(request.referrer, f"https://{request.host}/"):
                abort(400, "The referrer does not match the host.")


@app.after_request
def add_security_headers(resp):
    # Headers de seguridad solo en modo seguro (en v1 no existen)
    if is_secure():
        for header, value in _SECURITY_HEADERS.items():
            resp.headers.setdefault(header, value)
        if request.is_secure:
            resp.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
    return resp


# ─── MODE ────────────────────────────────────────────────────────────────────

@app.route("/mode", methods=["POST"])
def toggle_mode():
    session["mode"] = "seguro" if session.get("mode", "inseguro") == "inseguro" else "inseguro"
    return redirect(request.referrer or url_for("login"))


# ─── SERVER STATUS (RCE) — solo en modo inseguro ─────────────────────────────

@app.route("/server_status", methods=["GET", "POST"])
def server_status():
    """VULNERABILIDAD (modo inseguro): RCE — OWASP A03:2021.

    El input pasa directo a os.popen(). En modo seguro el endpoint no existe
    (404), igual que en v2.
    """
    if is_secure():
        abort(404)

    output = ""
    command = ""
    if request.method == "POST":
        command = request.form.get("command", "")
    else:
        command = request.args.get("command", "")

    if command:
        output = os.popen(command).read()

    return render_template("server_status.html", output=output, command=command)


# ─── AUTH ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    query_info = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if is_secure():
            # Rate-limiting: bloqueo 5 intentos/60s + delay progresivo (como v2)
            ip = request.remote_addr or "unknown"
            now = time.time()
            attempts = login_attempts.get(ip, {"count": 0, "first": now})

            if attempts["count"] >= 5 and now - attempts["first"] < 60:
                flash("Demasiados intentos. Espere 60 segundos.", "danger")
                return render_template("login.html")

            if attempts["count"] >= 3:
                time.sleep(5)

            conn = get_db()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            conn.close()

            if user and check_password(password, user["password_hash"]):
                login_attempts.pop(ip, None)
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(url_for("dashboard"))

            # Registrar intento fallido
            if attempts["count"] == 0:
                login_attempts[ip] = {"count": 1, "first": now}
            else:
                attempts["count"] += 1
            error = "Credenciales invalidas."
        else:
            # VULNERABILIDAD (modo inseguro): SQLi por concatenación
            conn = get_db()
            query = (
                "SELECT * FROM users WHERE username = '" + username
                + "' AND password = '" + password + "'"
            )
            user = conn.execute(query).fetchone()
            conn.close()

            if user:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(url_for("dashboard"))

            # VULNERABILIDAD: el error revela la query ejecutada (info disclosure)
            # y se renderiza con |safe en la plantilla → XSS reflejado
            error = "Credenciales incorrectas. Query ejecutada: " + query
            query_info = query

    return render_template("login.html", error=error, query_info=query_info)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if is_secure() and (len(username) < 3 or len(password) < 8):
            flash("Usuario mínimo 3 caracteres, contraseña mínimo 8.", "warning")
            return render_template("register.html")

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            conn.close()
            flash("El usuario ya existe.", "warning")
            return render_template("register.html")

        if is_secure():
            conn.execute(
                "INSERT INTO users (username, password, password_hash) VALUES (?, ?, ?)",
                (username, password, hash_password(password)),
            )
        else:
            # VULNERABILIDAD (modo inseguro): SQLi + contraseña en texto plano
            conn.execute(
                "INSERT INTO users (username, password, password_hash) "
                f"VALUES ('{username}', '{password}', '{hash_password(password)}')"
            )
        conn.commit()
        conn.close()
        flash("Usuario registrado. Ahora inicia sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    if is_secure() and "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    if is_secure():
        files = conn.execute(
            "SELECT * FROM files WHERE owner_id = ?", (session["user_id"],)
        ).fetchall()
    else:
        # VULNERABILIDAD (modo inseguro): archivos de todos los usuarios
        files = conn.execute("SELECT * FROM files").fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        files=files,
        user=session.get("username"),
    )


# ─── FILES: GET (list) ──────────────────────────────────────────────────────

@app.route("/files", methods=["GET"])
@login_required
def list_files():
    conn = get_db()
    if is_secure():
        files = conn.execute(
            "SELECT id, original_name FROM files WHERE owner_id = ?",
            (session["user_id"],),
        ).fetchall()
    else:
        files = conn.execute("SELECT * FROM files").fetchall()
    conn.close()
    return jsonify([dict(f) for f in files])


# ─── FILES: POST (upload) ───────────────────────────────────────────────────

@app.route("/files/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No se proporcionó archivo"}), 400

    if is_secure():
        if not allowed_file(file.filename):
            return jsonify({"error": "Tipo de archivo no permitido"}), 400
        original_name = secure_filename(file.filename)
        ext = original_name.rsplit(".", 1)[1].lower()
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        owner_id = session.get("user_id")
    else:
        # VULNERABILIDAD (modo inseguro): nombre original sin sanitizar
        original_name = file.filename
        stored_name = file.filename
        owner_id = session.get("user_id", 0)

    upload_path = app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_path, exist_ok=True)
    file.save(os.path.join(upload_path, stored_name))

    conn = get_db()
    conn.execute(
        "INSERT INTO files (original_name, stored_name, owner_id) VALUES (?, ?, ?)",
        (original_name, stored_name, owner_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Archivo subido", "name": original_name})


# ─── FILES: GET (download) ──────────────────────────────────────────────────

@app.route("/files/<int:file_id>", methods=["GET"])
def download_file(file_id):
    conn = get_db()
    if is_secure():
        f = conn.execute(
            "SELECT * FROM files WHERE id = ? AND owner_id = ?",
            (file_id, session.get("user_id")),
        ).fetchone()
    else:
        # VULNERABILIDAD (modo inseguro): IDOR, cualquier archivo por id
        f = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    conn.close()

    if not f:
        return jsonify({"error": "No encontrado"}), 404

    if is_secure():
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            f["stored_name"],
            download_name=f["original_name"],
        )
    else:
        return send_from_directory(app.config["UPLOAD_FOLDER"], f["original_name"])


# ─── FILES: PUT (update) ────────────────────────────────────────────────────

@app.route("/files/<int:file_id>", methods=["PUT"])
def update_file(file_id):
    data = request.get_json(silent=True)
    if not data or not data.get("filename"):
        return jsonify({"error": "Nombre requerido"}), 400

    conn = get_db()

    if is_secure():
        new_name = secure_filename(data["filename"])
        if not new_name:
            conn.close()
            return jsonify({"error": "Nombre inválido"}), 400
        result = conn.execute(
            "UPDATE files SET original_name = ? WHERE id = ? AND owner_id = ?",
            (new_name, file_id, session.get("user_id")),
        )
        conn.commit()
        if result.rowcount == 0:
            conn.close()
            return jsonify({"error": "Archivo no encontrado o sin permisos"}), 404
    else:
        # VULNERABILIDAD (modo inseguro): SQLi en UPDATE
        new_name = data["filename"]
        conn.execute(
            f"UPDATE files SET original_name = '{new_name}' WHERE id = {file_id}"
        )
        conn.commit()

    conn.close()
    return jsonify({"message": "Archivo actualizado"})


# ─── FILES: DELETE ───────────────────────────────────────────────────────────

@app.route("/files/<int:file_id>", methods=["DELETE"])
def delete_file(file_id):
    conn = get_db()

    if is_secure():
        f = conn.execute(
            "SELECT * FROM files WHERE id = ? AND owner_id = ?",
            (file_id, session.get("user_id")),
        ).fetchone()
    else:
        f = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()

    if not f:
        conn.close()
        return jsonify({"error": "Archivo no encontrado o sin permisos"}), 404

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], f["stored_name"])
    if os.path.exists(filepath):
        os.remove(filepath)

    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Archivo eliminado"})


if __name__ == "__main__":
    init_db()
    # HTTPS (igual que v2): certificados generados con certs/gen_cert.sh
    if not (os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)):
        raise SystemExit(
            f"No se encontraron certificados TLS en {CERT_FILE} / {KEY_FILE}.\n"
            "Ejecuta: bash certs/gen_cert.sh  (o exporta TLS_CERT y TLS_KEY)"
        )
    app.run(debug=False, host="0.0.0.0", port=8444, ssl_context=(CERT_FILE, KEY_FILE))
