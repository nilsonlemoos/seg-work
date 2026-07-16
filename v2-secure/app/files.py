import os
import uuid
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, send_from_directory, current_app, flash
from werkzeug.utils import secure_filename
from .database import get_db
from .auth import login_required

files_bp = Blueprint("files", __name__)

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )

@files_bp.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    # Solo archivos del usuario autenticado
    files = db.execute(
        "SELECT * FROM files WHERE owner_id = ?", (session["user_id"],)
    ).fetchall()
    return render_template("dashboard.html", files=files, user=session["username"])

# ─── GET ─────────────────────────────────────────────────────────────────────

@files_bp.route("/files", methods=["GET"])
@login_required
def list_files():
    db = get_db()
    files = db.execute(
        "SELECT id, original_name FROM files WHERE owner_id = ?", (session["user_id"],)
    ).fetchall()
    return jsonify([dict(f) for f in files])

# ─── POST ────────────────────────────────────────────────────────────────────

@files_bp.route("/files/upload", methods=["POST"])
@login_required
def upload_file():
    file = request.files.get("file")

    if not file or file.filename == "":
        return jsonify({"error": "No se proporcionó archivo"}), 400

    # Validación de tipo de archivo
    if not allowed_file(file.filename):
        return jsonify({"error": "Tipo de archivo no permitido"}), 400

    original_name = secure_filename(file.filename)
    # Nombre aleatorio para evitar colisiones y path traversal
    ext = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"

    upload_path = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_path, exist_ok=True)
    file.save(os.path.join(upload_path, stored_name))

    db = get_db()
    db.execute(
        "INSERT INTO files (original_name, stored_name, owner_id) VALUES (?, ?, ?)",
        (original_name, stored_name, session["user_id"]),
    )
    db.commit()

    return jsonify({"message": "Archivo subido correctamente", "name": original_name})

# ─── GET (descarga) ──────────────────────────────────────────────────────────

@files_bp.route("/files/<int:file_id>", methods=["GET"])
@login_required
def download_file(file_id):
    db = get_db()
    # Verifica que el archivo pertenece al usuario autenticado
    f = db.execute(
        "SELECT * FROM files WHERE id = ? AND owner_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    if not f:
        return jsonify({"error": "Archivo no encontrado"}), 404

    # Se usa el nombre almacenado (uuid), no el nombre original del usuario
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], f["stored_name"], download_name=f["original_name"])

# ─── PUT ─────────────────────────────────────────────────────────────────────

@files_bp.route("/files/<int:file_id>", methods=["PUT"])
@login_required
def update_file(file_id):
    data = request.get_json(silent=True)
    if not data or not data.get("filename"):
        return jsonify({"error": "Nombre requerido"}), 400

    new_name = secure_filename(data["filename"])
    if not new_name:
        return jsonify({"error": "Nombre inválido"}), 400

    db = get_db()
    # Solo puede modificar sus propios archivos
    result = db.execute(
        "UPDATE files SET original_name = ? WHERE id = ? AND owner_id = ?",
        (new_name, file_id, session["user_id"]),
    )
    db.commit()

    if result.rowcount == 0:
        return jsonify({"error": "Archivo no encontrado o sin permisos"}), 404

    return jsonify({"message": "Archivo actualizado"})

# ─── DELETE ──────────────────────────────────────────────────────────────────

@files_bp.route("/files/<int:file_id>", methods=["DELETE"])
@login_required
def delete_file(file_id):
    db = get_db()
    # Solo puede eliminar sus propios archivos
    f = db.execute(
        "SELECT * FROM files WHERE id = ? AND owner_id = ?",
        (file_id, session["user_id"]),
    ).fetchone()

    if not f:
        return jsonify({"error": "Archivo no encontrado o sin permisos"}), 404

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], f["stored_name"])
    if os.path.exists(filepath):
        os.remove(filepath)

    db.execute("DELETE FROM files WHERE id = ?", (file_id,))
    db.commit()

    return jsonify({"message": "Archivo eliminado"})
