# Notas de sesión — seg-work

Resumen de todo lo construido en esta sesión por si se pierde el contexto.

---

## Qué es el proyecto

Actividad universitaria de seguridad que compara dos versiones de la misma app web:

- **v1-insecure**: app Flask con 8 vulnerabilidades intencionales (sin SecDevOps)
- **v2-secure**: misma app corregida aplicando prácticas SecDevOps

Funcionalidades: login, registro, subida de archivos, CRUD (GET, POST, PUT, DELETE).

---

## Stack

- Python 3.12 + Flask 3.0
- SQLite (base de datos en archivo local)
- HTML + Bootstrap 5 (sin frameworks JS)
- Docker + Docker Compose (para que el docente no instale nada)

---

## Estructura de archivos

```
seg-work/
├── docker-compose.yml
├── .gitignore
├── README.md                        ← instrucciones para el docente
├── NOTAS_SESION.md                  ← este archivo
├── v1-insecure/
│   ├── app.py                       ← todo en un solo archivo, vulnerable
│   ├── Dockerfile
│   ├── requirements.txt             ← solo flask==3.0.3
│   └── templates/
│       ├── login.html
│       ├── register.html
│       └── dashboard.html
├── v2-secure/
│   ├── run.py                       ← entry point
│   ├── Dockerfile
│   ├── requirements.txt             ← flask + python-dotenv
│   ├── .env.example
│   └── app/
│       ├── __init__.py              ← factory function create_app()
│       ├── auth.py                  ← blueprint: login, register, logout
│       ├── files.py                 ← blueprint: CRUD de archivos
│       ├── config.py                ← configuración desde variables de entorno
│       ├── database.py              ← init_db, get_db, close_db
│       └── templates/
│           ├── login.html
│           ├── register.html
│           └── dashboard.html
└── report/
    └── informe_tecnico.md           ← informe completo para entregar
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
```

> El `DOCKER_HOST=...` es necesario en esta máquina porque Docker está instalado como paquete del sistema (no Docker Desktop). En otras máquinas basta con `docker compose up --build`.

**URLs:**
- V1 insegura → http://localhost:5000
- V2 segura   → http://localhost:5001

---

## Credenciales

No hay usuarios predefinidos. La base de datos arranca vacía. Hay que registrarse en cada versión:

- **V1** → http://localhost:5000/register — cualquier usuario y contraseña
- **V2** → http://localhost:5001/register — contraseña mínimo 8 caracteres

---

## Vulnerabilidades en V1 (intencionales)

| # | Vulnerabilidad | Dónde verla en el código |
|---|---|---|
| 1 | SQL Injection | `app.py` líneas del login y register — concatenación directa en queries |
| 2 | Contraseña en texto plano | `app.py` — INSERT sin hashing |
| 3 | Subida sin validación | `upload_file()` — acepta cualquier tipo y tamaño |
| 4 | Sin autenticación en endpoints | Todas las rutas de `/files` sin verificar sesión |
| 5 | Acceso a archivos de otros usuarios | `SELECT * FROM files` sin filtro por usuario |
| 6 | Secret key hardcodeada | `app.secret_key = "admin123"` |
| 7 | Errores con info interna | Mensaje de error muestra la query SQL ejecutada |
| 8 | Debug mode activo | `app.run(debug=True, host="0.0.0.0")` |

---

## Correcciones en V2

| Vulnerabilidad | Archivo | Solución |
|---|---|---|
| SQL Injection | `auth.py`, `files.py` | Queries parametrizadas con `?` |
| Contraseña plana | `auth.py` | `generate_password_hash` / `check_password_hash` |
| Archivos sin validar | `files.py`, `config.py` | Whitelist de extensiones + límite 5 MB + `uuid` como nombre en disco |
| Sin autenticación | `auth.py`, `files.py` | Decorador `@login_required` en todos los endpoints |
| Acceso entre usuarios | `files.py` | Todas las queries filtran por `owner_id = session["user_id"]` |
| Secret key hardcodeada | `config.py` | `os.environ.get("SECRET_KEY")` + `.env` en `.gitignore` |
| Errores informativos | `auth.py` | `flash("Credenciales inválidas.")` — sin detalle interno |
| Debug mode | `run.py` | `debug=False, host="0.0.0.0"` |

---

## Problema que se resolvió durante la sesión

Docker no tenía acceso a internet para bajar paquetes pip porque el DNS del sistema (`127.0.0.53`) no es accesible desde los contenedores. Se solucionó creando `/etc/docker/daemon.json`:

```json
{"dns": ["8.8.8.8", "8.8.4.4"]}
```

Y reiniciando: `sudo systemctl restart docker`

---

## Git

Repositorio local inicializado en `/home/lemos/Documents/Proyects/seg-work`.  
Sin remote configurado — para subir a GitHub/GitLab:

```bash
git remote add origin https://github.com/tu-usuario/seg-work.git
git push -u origin master
```

---

## Entregables listos

- [x] Código v1 con vulnerabilidades documentadas en el código
- [x] Código v2 corregido con SecDevOps
- [x] `report/informe_tecnico.md` — informe técnico completo para entregar
- [x] `README.md` — instrucciones de ejecución para el docente
- [x] Docker Compose — el docente solo corre un comando
