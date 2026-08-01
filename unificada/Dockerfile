FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p uploads

# Certificado self-signed generado en tiempo de build (CN=localhost)
RUN bash certs/gen_cert.sh

EXPOSE 8444
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "app.py"]
