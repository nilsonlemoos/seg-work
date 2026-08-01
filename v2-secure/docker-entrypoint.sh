#!/bin/sh
set -e

echo "[entrypoint] Sembrando base de datos (idempotente)..."
python seed.py

echo "[entrypoint] Iniciando aplicacion..."
exec "$@"
