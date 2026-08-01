import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # TLS habilitado por defecto: requiere cert.pem y key.pem en certs/
    # (generarlos con: bash certs/gen_cert.sh)
    ssl_context = None
    if app.config["TLS_ENABLED"]:
        cert = app.config["CERT_FILE"]
        key = app.config["KEY_FILE"]
        if not (os.path.exists(cert) and os.path.exists(key)):
            raise SystemExit(
                f"No se encontraron certificados TLS en {cert} / {key}.\n"
                "Ejecuta: bash certs/gen_cert.sh  (o exporta TLS_CERT y TLS_KEY)"
            )
        ssl_context = (cert, key)

    app.run(debug=False, host="0.0.0.0", port=8443, ssl_context=ssl_context)
