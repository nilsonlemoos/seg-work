"""
Seed para la app UNIFICADA (modo seguro/inseguro).

La tabla users guarda DOS columnas para que el mismo usuario funcione en ambos
modos:
  - password       → texto plano (usado por el modo INSEGURO, como en v1)
  - password_hash  → bcrypt (usado por el modo SEGURO, como en v2)

Idempotente: puede ejecutarse N veces sin duplicar registros.
"""
import os
import sqlite3

import bcrypt

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


def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT,
            password_hash TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT,
            stored_name TEXT,
            owner_id INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_users():
    conn = get_conn()
    inserted = 0
    for username, password in USERS:
        password_hash = hash_password(password)
        cur = conn.execute(
            "INSERT OR IGNORE INTO users (username, password, password_hash) VALUES (?, ?, ?)",
            (username, password, password_hash),
        )
        if cur.rowcount == 0:
            print(f"[skip] {username} ya existe")
            continue
        inserted += 1
        print(f"[ok]   {username} / {password} (texto plano + bcrypt)")
    conn.commit()
    conn.close()
    return inserted


if __name__ == "__main__":
    init_db()
    print(f"Base de datos: {DB_PATH}")
    n = seed_users()
    print(f"Seeded: {n} usuario(s) nuevo(s) en unificada (plano + bcrypt).")
