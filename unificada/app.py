from flask import (
    Flask, request, session, redirect, url_for,
    render_template, send_from_directory, jsonify, flash
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import uuid

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
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


def is_secure():
    return session.get("mode") == "seguro"


def allowed_file(filename):
    allowed = {"pdf", "png", "jpg", "jpeg", "gif", "txt", "docx"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# ─── MODE ────────────────────────────────────────────────────────────────────

@app.route("/mode", methods=["POST"])
def toggle_mode():
    session["mode"] = "seguro" if session.get("mode") == "inseguro" else "inseguro"
    return redirect(request.referrer or url_for("login"))


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

        conn = get_db()

        if is_secure():
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            conn.close()

            if user and check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect(url_for("dashboard"))
            else:
                error = "Credenciales invalidas."
        else:
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
            else:
                error = "Credenciales incorrectas."
                query_info = query

    return render_template("login.html", error=error, query_info=query_info)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        if is_secure():
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
        else:
            conn.execute(
                f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
            )
        conn.commit()
        conn.close()
        flash("Usuario registrado. Ahora inicia sesion.", "success")
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
        files = conn.execute("SELECT * FROM files").fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        files=files,
        user=session.get("username"),
    )


# ─── FILES: GET (list) ──────────────────────────────────────────────────────

@app.route("/files", methods=["GET"])
def list_files():
    conn = get_db()
    if is_secure():
        files = conn.execute(
            "SELECT id, original_name FROM files WHERE owner_id = ?",
            (session.get("user_id"),),
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
        return jsonify({"error": "No se proporciono archivo"}), 400

    if is_secure():
        if not allowed_file(file.filename):
            return jsonify({"error": "Tipo de archivo no permitido"}), 400
        original_name = secure_filename(file.filename)
        ext = original_name.rsplit(".", 1)[1].lower()
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        owner_id = session.get("user_id")
    else:
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
            return jsonify({"error": "Nombre invalido"}), 400
        result = conn.execute(
            "UPDATE files SET original_name = ? WHERE id = ? AND owner_id = ?",
            (new_name, file_id, session.get("user_id")),
        )
        conn.commit()
        if result.rowcount == 0:
            conn.close()
            return jsonify({"error": "Archivo no encontrado o sin permisos"}), 404
    else:
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
    app.secret_key = os.environ.get("SECRET_KEY", "clave-insegura-para-demo")
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.run(debug=False, host="0.0.0.0", port=5002)
