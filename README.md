# seg-work — Aplicación de Gestión de Archivos

Proyecto académico de seguridad que demuestra el impacto de SecDevOps comparando tres versiones de la misma aplicación web:

- **v1-insecure**: app Flask con vulnerabilidades intencionales (OWASP Top 10)
- **v2-secure**: misma app fortificada aplicando prácticas de seguridad
- **unificada**: conmutador de modo seguro/inseguro por sesión (estilo DVWA)

---

## Cómo ejecutar

**Requisitos: [Docker](https://docs.docker.com/engine/install/) con el daemon activo.**

```bash
docker compose up --build -d
```

> En esta máquina de desarrollo Docker corre como servicio del sistema, por lo que se usa:
> `DOCKER_HOST=unix:///var/run/docker.sock docker compose up --build -d`

Las tres versiones quedan disponibles en:

| Versión | URL | Descripción |
|---|---|---|
| v1 — Insegura | http://localhost:5000 | Vulnerabilidades intencionales (HTTP) |
| v2 — Segura | https://localhost:8443 | Corregida (HTTPS + CSRF + headers) |
| v3 — Unificada | https://localhost:8444 | Modo seguro/inseguro conmutable por sesión |

Para v2 y v3 el navegador pedirá aceptar el **certificado autofirmado** (Advanced → Continue). Es un certificado generado localmente para desarrollo.

Para detener: `docker compose down`.

**Ejecución local (sin Docker):**

```bash
# v1 (puerto 5000)
cd v1-insecure
pip install -r requirements.txt
python seed.py
python app.py

# v2 (puerto 8443, requiere certificados)
cd v2-secure
pip install -r requirements.txt
bash certs/gen_cert.sh
python seed.py
python run.py

# unificada (puerto 8444, requiere certificados)
cd unificada
pip install -r requirements.txt
bash certs/gen_cert.sh
python seed.py
python app.py
```

### Credenciales de prueba

| Usuario | Contraseña |
|---|---|
| admin | admin123 |
| ana | 123456 |
| pedro | password |

---

## Estructura del proyecto

```
seg-work/
├── docker-compose.yml         # Levanta v1, v2 y unificada con volúmenes + healthchecks
├── sqlmap/                    # Automatización de SQLi con sqlmap (Fase 3)
├── v1-insecure/               # Versión con vulnerabilidades intencionales
│   ├── app.py                 # Aplicación monolítica (Flask)
│   ├── seed.py                # Usuarios de prueba en texto plano
│   ├── templates/             # HTML: login, registro, dashboard
│   └── Dockerfile
├── v2-secure/                 # Versión corregida con SecDevOps
│   ├── app/
│   │   ├── auth.py            # Autenticación (bcrypt)
│   │   ├── files.py           # CRUD de archivos
│   │   ├── config.py          # Configuración segura + TLS
│   │   ├── database.py        # Acceso a base de datos
│   │   └── templates/
│   ├── certs/                 # gen_cert.sh + certificados locales
│   ├── run.py                 # HTTPS en puerto 8443
│   ├── seed.py                # Usuarios de prueba con bcrypt
│   └── Dockerfile
└── unificada/                 # Versión unificada (estilo DVWA, puerto 8444)
    ├── app.py                 # Conmutador de modo seguro/inseguro por sesión
    ├── seed.py                # Usuarios con texto plano + bcrypt
    ├── templates/             # HTML con badge de modo y CSRF condicional
    └── Dockerfile
```

---

## Vulnerabilidades en V1 vs soluciones en V2

| # | Vulnerabilidad | OWASP | V1 | V2 |
|---|---|---|---|---|
| 1 | SQL Injection | A03 | ❌ Concatenación directa | ✅ Queries parametrizadas |
| 2 | Command Injection (RCE) | A03 | ❌ `os.popen()` en `/server_status` | ✅ Endpoint inexistente |
| 3 | XSS reflejado y almacenado | A03 | ❌ `\|safe` en login y dashboard | ✅ Escape de plantillas |
| 4 | CSRF | A07 | ❌ Sin tokens | ✅ Flask-WTF + Referer estricto |
| 5 | Contraseñas en texto plano | A02 | ❌ Sin hashing | ✅ bcrypt |
| 6 | Secret key hardcodeada | A02 | ❌ `"admin123"` en código | ✅ Variable de entorno |
| 7 | Archivos sin validación | A04 | ❌ Cualquier tipo y tamaño | ✅ Whitelist + límite 5 MB |
| 8 | Endpoints sin autenticación | A01 | ❌ API abierta | ✅ `@login_required` |
| 9 | Acceso a archivos de otros usuarios | A01 | ❌ Sin filtro por usuario | ✅ Filtro por `owner_id` |
| 10 | Errores con info interna | A05 | ❌ Muestra queries SQL | ✅ Mensajes genéricos |
| 11 | Debug mode activo | A05 | ❌ `debug=True` | ✅ `debug=False` |
| 12 | Sin TLS | — | ❌ HTTP plano | ✅ HTTPS 8443 + HSTS |

---

## Documentación adicional

| Documento | Contenido |
|---|---|
| `sqlmap/resultados_sqlmap.md` | Explotación automatizada del SQLi del login |
| `docs/GUIA_ENTORNO_Y_TRAFICO.md` | Guía de despliegue, evidencias de V1/V2/V3, análisis de tráfico (local, no versionado) |
