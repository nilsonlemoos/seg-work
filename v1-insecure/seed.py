"""
Seed para la versión v1 (INSEGURA).

Crea la infraestructura de datos desde cero y siembra usuarios de prueba.
REQUISITO CRÍTICO DE DISEÑO: en v1 las contraseñas se almacenan en TEXTO PLANO,
ya que esta versión replica los peores hábitos de la industria a propósito.

Idempotente: puede ejecutarse N veces sin duplicar registros.
"""
import os
import sqlite3

DB_PATH = os.environ.get(
    "DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
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


def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            owner TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def seed_users():
    conn = get_conn()
    inserted = 0
    for username, password in USERS:
        # Idempotencia: si el usuario ya existe, no se vuelve a insertar.
        exists = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if exists:
            print(f"[skip] {username} ya existe")
            continue
        # VULNERABILIDAD (intencional): contraseña en texto plano absoluto.
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password),
        )
        inserted += 1
        print(f"[ok]   {username} / {password} (TEXTO PLANO)")
    conn.commit()
    conn.close()
    return inserted


if __name__ == "__main__":
    init_db()
    print(f"Base de datos: {DB_PATH}")
    n = seed_users()
    print(f"Seeded: {n} usuario(s) nuevo(s) en v1-insecure (texto plano).")
