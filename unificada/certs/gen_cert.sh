#!/usr/bin/env bash
#
# Genera un certificado autofirmado (self-signed) para levantar la app
# unificada con HTTPS (puerto 8444).
# Uso:  bash certs/gen_cert.sh  [CN]   (CN por defecto: localhost)
set -euo pipefail

CN="${1:-localhost}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT="$DIR/cert.pem"
KEY="$DIR/key.pem"

openssl req -x509 -newkey rsa:2048 -sha256 \
    -keyout "$KEY" \
    -out "$CERT" \
    -days 365 \
    -nodes \
    -subj "/C=PE/ST=Lima/L=Lima/O=SegWork/OU=SecDevOps/CN=$CN" \
    -addext "subjectAltName=DNS:$CN,DNS:localhost,IP:127.0.0.1"

chmod 600 "$KEY"
echo "Certificado generado:"
echo "  cert: $CERT"
echo "  key:  $KEY"
echo
echo "Levanta la app unificada con HTTPS:"
echo "  python app.py         # puerto 8444"
echo "  curl -k https://localhost:8444"
