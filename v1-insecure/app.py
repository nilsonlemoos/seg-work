from flask import Flask, request, session, redirect, url_for, render_template, send_from_directory, jsonify
import sqlite3
import os

app = Flask(__name__)

# VULNERABILIDAD: Secret key hardcodeada
app.secret_key = "admin123"

# VULNERABILIDAD: Ruta de uploads expuesta y sin restricciones
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# VULNERABILIDAD: Base de datos creada sin ningún control
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            owner TEXT
        )
    """)
    conn.commit()
    conn.close()

# ─── AUTH ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # VULNERABILIDAD: SQL Injection — query construida con concatenación
        conn = get_db()
        query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
        user = conn.execute(query).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            # VULNERABILIDAD: mensaje de error revela si el usuario existe
            error = "Usuario o contraseña incorrectos. Query ejecutada: " + query

    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # VULNERABILIDAD: contraseña guardada en texto plano
        conn = get_db()
        conn.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
        conn.commit()
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    # VULNERABILIDAD: sin verificar si el usuario está autenticado
    conn = get_db()
    # VULNERABILIDAD: retorna TODOS los archivos de todos los usuarios
    files = conn.execute("SELECT * FROM files").fetchall()
    conn.close()
    return render_template("dashboard.html", files=files, user=session.get("user"))

# ─── FILES ───────────────────────────────────────────────────────────────────

@app.route("/files", methods=["GET"])
def list_files():
    conn = get_db()
    files = conn.execute("SELECT * FROM files").fetchall()
    conn.close()
    return jsonify([dict(f) for f in files])

@app.route("/files/upload", methods=["POST"])
def upload_file():
    # VULNERABILIDAD: sin autenticación requerida
    # VULNERABILIDAD: sin validación de tipo de archivo
    # VULNERABILIDAD: sin límite de tamaño
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file"}), 400

    filename = file.filename  # VULNERABILIDAD: nombre original sin sanitizar
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    owner = session.get("user", "anonimo")
    conn = get_db()
    conn.execute(f"INSERT INTO files (filename, owner) VALUES ('{filename}', '{owner}')")
    conn.commit()
    conn.close()

    return jsonify({"message": "Archivo subido", "filename": filename})

@app.route("/files/<int:file_id>", methods=["GET"])
def download_file(file_id):
    # VULNERABILIDAD: cualquiera puede descargar cualquier archivo
    # VULNERABILIDAD: path traversal posible con el nombre del archivo
    conn = get_db()
    f = conn.execute(f"SELECT * FROM files WHERE id = {file_id}").fetchone()
    conn.close()

    if not f:
        return jsonify({"error": "No encontrado"}), 404

    return send_from_directory(app.config["UPLOAD_FOLDER"], f["filename"])

@app.route("/files/<int:file_id>", methods=["PUT"])
def update_file(file_id):
    # VULNERABILIDAD: sin autenticación, cualquiera puede renombrar
    data = request.get_json()
    new_name = data.get("filename")

    conn = get_db()
    # VULNERABILIDAD: SQL Injection en UPDATE
    conn.execute(f"UPDATE files SET filename = '{new_name}' WHERE id = {file_id}")
    conn.commit()
    conn.close()

    return jsonify({"message": "Archivo actualizado"})

@app.route("/files/<int:file_id>", methods=["DELETE"])
def delete_file(file_id):
    # VULNERABILIDAD: cualquiera puede eliminar cualquier archivo sin autenticar
    conn = get_db()
    f = conn.execute(f"SELECT * FROM files WHERE id = {file_id}").fetchone()
    if f:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], f["filename"])
        if os.path.exists(filepath):
            os.remove(filepath)
        conn.execute(f"DELETE FROM files WHERE id = {file_id}")
        conn.commit()
    conn.close()

    return jsonify({"message": "Archivo eliminado"})

if __name__ == "__main__":
    init_db()
    # VULNERABILIDAD: debug=True expone el debugger interactivo de Werkzeug
    app.run(debug=True, host="0.0.0.0", port=5000)
