# Notas de sesión — seg-work

Resumen de todo lo construido en esta sesión por si se pierde el contexto.

---

## Qué es el proyecto

Actividad universitaria de seguridad que compara dos versiones de la misma app web:

- **v1-insecure**: app Flask con vulnerabilidades intencionales (OWASP Top 10)
- **v2-secure**: misma app corregida aplicando prácticas SecDevOps

Funcionalidades: login, registro, subida de archivos, CRUD (GET, POST, PUT, DELETE).

---

## Stack

- Python 3.12 + Flask 3.0
- SQLite (base de datos en archivo local)
- HTML + Bootstrap 5 (sin frameworks JS)
- Docker + Docker Compose (para que el docente no instale nada)
- sqlmap 1.8.4 (Fase 3), openssl 3.0 (Fase 2)

---

## Estado de las fases

| Fase | Descripción | Estado |
|---|---|---|
| 0 | Seeds de BD con datos de prueba | ✅ `feat/v1-owasp-fase0-1` |
| 1 | v1 ampliada: RCE, XSS, CSRF + mapeo OWASP | ✅ `feat/v1-owasp-fase0-1` |
| 2 | Fortificación v2: HTTPS/TLS, CSRF, cookies, headers | ✅ `feat/v2-fortificacion-https` |
| 3 | SQLmap automatizado | ✅ `feat/sqlmap-fase3` |
| 4 | Arquitectura de despliegue (Docker refinado) | ✅ `feat/fase4-despliegue` |
| 5 | Documentación (README/NOTAS al repo; GUIA y docs local) | ✅ `feat/fase5-documentacion` |

---

## Estructura de archivos

```
seg-work/
├── docker-compose.yml          # v1 + v2 con volúmenes, red seg-net, healthchecks
├── .gitignore
├── README.md                   ← instrucciones para el docente
├── NOTAS_SESION.md             ← este archivo
├── GUIA_PRUEBAS.md             ← local only (no se commitea)
├── mapeo_owasp.md              ← 12 vulns vs OWASP Top 10 2021
├── deploy/
│   └── ARQUITECTURA.md         ← topología, puertos, zonas, escenarios
├── sqlmap/
│   ├── automate_sqlmap.sh      ← detección + enumeración + dump
│   ├── resultados_sqlmap.md
│   └── output/                 ← logs de ejecución
├── docs/
│   └── DOCUMENTACION.md        ← local only (no se commitea)
├── v1-insecure/
│   ├── app.py                  ← monolítico, vulnerable
│   ├── seed.py                 ← usuarios texto plano (idempotente)
│   ├── docker-entrypoint.sh
│   ├── Dockerfile
│   ├── requirements.txt        ← flask==3.0.3
│   └── templates/
└── v2-secure/
    ├── run.py                  ← HTTPS puerto 8443
    ├── seed.py                 ← usuarios con bcrypt
    ├── docker-entrypoint.sh
    ├── certs/                  ← gen_cert.sh (pems ignorados por git)
    ├── Dockerfile
    ├── requirements.txt        ← flask + dotenv + bcrypt + flask-wtf
    ├── .env.example
    └── app/
        ├── __init__.py         ← factory + CSRFProtect + security headers
        ├── auth.py             ← login/register/logout (bcrypt)
        ├── files.py            ← CRUD de archivos (owner_id)
        ├── config.py           ← config segura + rutas TLS
        ├── database.py
        └── templates/
```

---

## Cómo levantar las apps

```bash
cd /home/lemos/Documents/Proyects/seg-work

# Levantar (primera vez construye las imágenes)
DOCKER_HOST=unix:///var/run/docker.sock docker compose up --build -d

# Levantar (sin reconstruir)
DOCKER_HOST=unix:///var/run/docker.sock docker compose up -d

# Bajar
DOCKER_HOST=unix:///var/run/docker.sock docker compose down

# Estado / logs
DOCKER_HOST=unix:///var/run/docker.sock docker compose ps
DOCKER_HOST=unix:///var/run/docker.sock docker compose logs -f v1-insecure
```

> El `DOCKER_HOST=...` es necesario en esta máquina porque Docker está instalado
> como paquete del sistema (no Docker Desktop). En otras máquinas basta con
> `docker compose up --build`. También se puede fijar: `docker context use default`.

**URLs:**
- v1 insegura → http://localhost:5000 (HTTP)
- v2 segura   → https://localhost:8443 (HTTPS, cert autofirmado)

**Ejecución local (sin Docker):** ver README.md.

**Credenciales sembradas (ambas versiones):** `admin/admin123`, `ana/123456`, `pedro/password`.

---

## Docker (Fase 4)

- Volúmenes nombrados: `v1-db`, `v2-db`, `v1-uploads`, `v2-uploads` (persistencia en `/data`)
- Red bridge interna `seg-net`
- Entrypoint `docker-entrypoint.sh`: siembra la BD (idempotente) y arranca la app
- Healthcheck con `urllib` (imágenes slim no traen `curl`)
- `restart: unless-stopped`
- DB dentro del contenedor: `/data/database.db` (vía env `DB_PATH`/`DATABASE`)

---

## Vulnerabilidades en V1 (intencionales)

| # | Vulnerabilidad | Dónde verla en el código |
|---|---|---|
| 1 | SQL Injection | `app.py` login/register/upload/update — concatenación directa |
| 2 | Command Injection (RCE) | `app.py` `/server_status` — `os.popen(command)` |
| 3 | XSS reflejado | `templates/login.html` — `{{ error \| safe }}` |
| 4 | XSS almacenado | `templates/dashboard.html` — `{{ f.filename \| safe }}` |
| 5 | CSRF | Endpoints POST sin token anti-CSRF |
| 6 | Contraseña en texto plano | `seed.py` / `app.py` — INSERT sin hashing |
| 7 | Subida sin validación | `upload_file()` — cualquier tipo y tamaño |
| 8 | Sin autenticación en endpoints | Rutas de `/files` sin verificar sesión |
| 9 | Acceso a archivos de otros | `SELECT * FROM files` sin filtro por usuario |
| 10 | Secret key hardcodeada | `app.secret_key = "admin123"` |
| 11 | Errores con info interna | Error de login muestra la query SQL |
| 12 | Debug mode activo | `app.run(debug=True, host="0.0.0.0")` |

Mapeo completo a OWASP Top 10 2021 en `mapeo_owasp.md`.

---

## Correcciones en V2

| Vulnerabilidad | Archivo | Solución |
|---|---|---|
| SQL Injection | `auth.py`, `files.py` | Queries parametrizadas con `?` |
| RCE | — | Endpoint `/server_status` eliminado |
| XSS | `templates/` | Escape de plantillas (sin `\|safe`) |
| CSRF | `__init__.py`, templates | Flask-WTF `CSRFProtect` + `{{ csrf_token() }}` + Referer estricto |
| Contraseña plana | `auth.py` | bcrypt (`hash_password`/`check_password`) |
| Archivos sin validar | `files.py`, `config.py` | Whitelist + límite 5 MB + UUID en disco |
| Sin autenticación | `auth.py`, `files.py` | Decorador `@login_required` |
| Acceso entre usuarios | `files.py` | Filtro por `owner_id` |
| Secret key hardcodeada | `config.py` | `os.environ.get("SECRET_KEY")` |
| Errores informativos | `auth.py` | Mensaje genérico |
| Debug mode | `run.py` | `debug=False` |
| Sin TLS | `run.py`, `certs/` | HTTPS 8443 + HSTS + headers de seguridad |

---

## Git

Repositorio: https://github.com/nilsonlemoos/seg-work.git

**Ramas (una por fase):**
- `feat/v1-owasp-fase0-1` — Fases 0-1 (seeds, RCE, XSS, CSRF, mapeo OWASP)
- `feat/v2-fortificacion-https` — Fase 2 (HTTPS/TLS + CSRF + headers)
- `feat/sqlmap-fase3` — Fase 3 (SQLmap automatizado)
- `feat/fase4-despliegue` — Fase 4 (Docker refinado + arquitectura)
- `feat/fase5-documentacion` — Fase 5 (documentación)

**Local only (no versionados):** `GUIA_PRUEBAS.md`, `docs/DOCUMENTACION.md`.
