"""
Seed para la versión v2 (SEGURA).

Crea la infraestructura de datos desde cero y siembra usuarios de prueba.
REQUISITO CRÍTICO DE DISEÑO: en v2 las contraseñas se almacenan hasheadas con
bcrypt (librería `bcrypt`), aplicando las mejores prácticas de la industria.

Idempotente: puede ejecutarse N veces sin duplicar registros.
"""
import os
import sqlite3

import bcrypt

# Misma ruta que app/config.py (configurable para volumen Docker)
DB_PATH = os.environ.get(
    "DATABASE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
)

USERS = [
    ("admin", "admin123"),
    ("ana", "123456"),
    ("pedro", "password"),
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Hashing criptográfico seguro con bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


def seed_users():
    conn = get_conn()
    inserted = 0
    for username, password in USERS:
        # Idempotencia: username es UNIQUE; INSERT OR IGNORE descarta duplicados.
        password_hash = hash_password(password)
        cur = conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        if cur.rowcount == 0:
            print(f"[skip] {username} ya existe")
            continue
        inserted += 1
        print(f"[ok]   {username} / (bcrypt: {password_hash[:20]}...)")
    conn.commit()
    conn.close()
    return inserted


if __name__ == "__main__":
    init_db()
    print(f"Base de datos: {DB_PATH}")
    n = seed_users()
    print(f"Seeded: {n} usuario(s) nuevo(s) en v2-secure (bcrypt).")
