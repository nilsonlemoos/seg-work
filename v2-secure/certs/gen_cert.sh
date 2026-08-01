#!/usr/bin/env bash
#
# Genera un certificado autofirmado (self-signed) para levantar v2 con HTTPS.
# Uso:  bash certs/gen_cert.sh  [CN]   (CN por defecto: localhost)
#
# Para un laboratorio académico un certificado self-signed es suficiente.
# En producción se usaría Let's Encrypt / una CA.
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
echo "Levanta v2 con HTTPS:"
echo "  python run.py          # puerto 8443"
echo "  curl -k https://localhost:8443"
