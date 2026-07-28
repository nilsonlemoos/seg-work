# seg-work — Aplicación de Gestión de Archivos

Proyecto académico que demuestra el impacto de SecDevOps comparando versiones de la misma aplicación web.

---

## Cómo ejecutar

**Requisito único: tener [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.**

```bash
docker-compose up --build
```

Las tres versiones quedan disponibles en:

| Versión | URL | Descripción |
|---|---|---|
| V1 — Insegura | http://localhost:5000 | Con vulnerabilidades intencionales |
| V2 — Segura | http://localhost:5001 | Corregida con SecDevOps |
| Unificada | http://localhost:5002 | Selector de modo (seguro/inseguro) en una sola app |

Para detener: `Ctrl+C` y luego `docker-compose down`.

**Ejecución local (sin Docker):**

```bash
cd unificada
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

---

## Estructura del proyecto

```
seg-work/
├── docker-compose.yml         # Levanta las tres versiones con un comando
├── v1-insecure/               # Versión con vulnerabilidades intencionales
│   ├── app.py                 # Aplicación monolítica (Flask)
│   ├── templates/             # HTML: login, registro, dashboard
│   ├── Dockerfile
│   └── requirements.txt
├── v2-secure/                 # Versión corregida con SecDevOps
│   ├── app/
│   │   ├── auth.py            # Módulo de autenticación
│   │   ├── files.py           # Módulo CRUD de archivos
│   │   ├── config.py          # Configuración segura
│   │   ├── database.py        # Acceso a base de datos
│   │   └── templates/         # HTML: login, registro, dashboard
│   ├── run.py
│   ├── Dockerfile
│   └── requirements.txt
├── unificada/                 # Versión unificada (estilo DVWA)
│   ├── app.py                 # App con toggle seguro/inseguro
│   ├── templates/
│   │   ├── base.html          # Layout con selector de modo en navbar
│   │   ├── login.html
│   │   ├── register.html
│   │   └── dashboard.html     # UI cambia según el modo activo
│   ├── Dockerfile
│   └── requirements.txt
└── report/
    └── informe_tecnico.md     # Análisis completo de vulnerabilidades
```

---

## Versión Unificada (estilo DVWA)

La carpeta `unificada/` combina ambas versiones en una sola aplicación con un **selector de modo** en el navbar:

- **Modo Inseguro**: SQL Injection, contraseñas en texto plano, sin auth, sin validación de archivos, expone queries en errores
- **Modo Seguro**: Queries parametrizadas, bcrypt, login_required, whitelist de extensiones, mensajes genéricos

El modo se persiste en la sesión y se puede cambiar desde cualquier página con el botón "Cambiar modo".

---

## Vulnerabilidades demostradas en V1 vs soluciones en V2

| # | Vulnerabilidad | OWASP | V1 | V2 |
|---|---|---|---|---|
| 1 | SQL Injection | A03 | ❌ Concatenación directa | ✅ Queries parametrizadas |
| 2 | Contraseñas en texto plano | A02 | ❌ Sin hashing | ✅ bcrypt (Werkzeug) |
| 3 | Archivos sin validación | A04 | ❌ Cualquier tipo y tamaño | ✅ Whitelist + límite 5 MB |
| 4 | Endpoints sin autenticación | A01 | ❌ API abierta | ✅ Decorador `@login_required` |
| 5 | Acceso a archivos de otros usuarios | A01 | ❌ Sin filtro por usuario | ✅ Filtro por `owner_id` |
| 6 | Secret key hardcodeada | A02 | ❌ `"admin123"` en código | ✅ Variable de entorno |
| 7 | Errores con info interna | A05 | ❌ Muestra queries SQL | ✅ Mensajes genéricos |
| 8 | Debug mode activo | A05 | ❌ `debug=True` | ✅ `debug=False` |

