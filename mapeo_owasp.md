# Mapeo de Vulnerabilidades — OWASP Top 10 2021

Documento de trazabilidad técnica que mapea las 11 vulnerabilidades intencionales de la **v1-insecure** contra las categorías del **OWASP Top 10 2021** (A01–A10).

> Aplicación de referencia: `v1-insecure/` (Flask + SQLite).
> Severidad según escala CVSS v3.1 (estimada para el contexto del laboratorio).

---

## Resumen ejecutivo

| # | Vulnerabilidad | Categoría OWASP 2021 | Severidad |
|---|---|---|---|
| 1 | SQL Injection (login/registro/CRUD) | **A03:2021** Injection | Crítica (9.8) |
| 2 | Contraseñas en texto plano | **A02:2021** Cryptographic Failures | Crítica (9.1) |
| 3 | Secret key hardcodeada | **A02:2021** Cryptographic Failures | Alta (7.5) |
| 4 | Subida de archivos sin validación | **A08:2021** Software and Data Integrity Failures | Crítica (9.8) |
| 5 | Acceso a endpoints sin autenticación | **A01:2021** Broken Access Control | Alta (8.1) |
| 6 | Acceso a archivos de otros usuarios (IDOR) | **A01:2021** Broken Access Control | Alta (8.1) |
| 7 | Errores que revelan información interna | **A05:2021** Security Misconfiguration | Media (5.3) |
| 8 | Debug mode activo | **A05:2021** Security Misconfiguration | Alta (7.5) |
| 9 | **Ejecución Remota de Código (RCE)** | **A03:2021** Injection | **Crítica (10.0)** |
| 10 | **Stored XSS** en nombre de archivo | **A03:2021** Injection | **Alta (8.2)** |
| 11 | **Reflected XSS** en error de login | **A03:2021** Injection | **Media (6.1)** |
| 12 | **CSRF** en login/registro/logout/upload | **A07:2021** Identification and Authentication Failures | Media (5.3) |

> **Nota de rigor**: el OWASP Top 10 2021 agrupa SQLi, XSS y command injection dentro de **A03:2021 Injection**. El CSRF no tiene categoría propia en 2021 y se suele mapear a A01 o A07; aquí se mapea a **A07** por su naturaleza de autenticación/sesión (y se anota A01 como alternativo).

---

## Detalle técnico por vulnerabilidad

### VULN-01 — SQL Injection
- **OWASP:** A03:2021 Injection
- **Severidad:** Crítica (9.8)
- **Ubicación:** `v1-insecure/app.py` — login, register, upload, download, update, delete
- **Descripción:** Las queries se construyen por concatenación directa de strings del usuario sin parametrizar.
- **Explotación (login):**
  ```sql
  Usuario: ' OR 1=1 --
  Password: x
  ```
- **Impacto:** Bypass de autenticación, exfiltración/alteración de toda la base de datos, posible dumping de credenciales.

---

### VULN-02 — Contraseñas en texto plano
- **OWASP:** A02:2021 Cryptographic Failures
- **Severidad:** Crítica (9.1)
- **Ubicación:** `v1-insecure/app.py` (INSERT en register) y `v1-insecure/seed.py`
- **Descripción:** Las contraseñas se almacenan tal cual en la columna `password` (ver `seed.py` → `admin/admin123`).
- **Explotación:**
  ```bash
  sqlite3 v1-insecure/database.db "SELECT * FROM users;"
  # 1|admin|admin123
  ```
- **Impacto:** Compromiso total de credenciales si la DB se filtra.

---

### VULN-03 — Secret key hardcodeada
- **OWASP:** A02:2021 Cryptographic Failures
- **Severidad:** Alta (7.5)
- **Ubicación:** `v1-insecure/app.py:8`
- **Descripción:** `app.secret_key = "admin123"` — clave fija conocida.
- **Explotación:** Forjar cookies de sesión con Flask (`flask-unsign`).
- **Impacto:** Suplantación de sesiones arbitrarias.

---

### VULN-04 — Subida de archivos sin validación
- **OWASP:** A08:2021 Software and Data Integrity Failures
- **Severidad:** Crítica (9.8)
- **Ubicación:** `v1-insecure/app.py` — `upload_file()`
- **Descripción:** Acepta cualquier tipo/tamaño/nombre; se guarda con el nombre original del usuario (`file.save(os.path.join(...))`), permitiendo path traversal y webshells.
- **Explotación:** Subir `shell.php` o un nombre como `../../app.py`.
- **Impacto:** Ejecución de código (si el servidor sirve el upload), sobrescritura de archivos arbitrarios.

---

### VULN-05 — Endpoints sin autenticación
- **OWASP:** A01:2021 Broken Access Control
- **Severidad:** Alta (8.1)
- **Ubicación:** `v1-insecure/app.py` — rutas `/dashboard`, `/files`, `/files/upload`, `/files/<id>`
- **Descripción:** Ninguna ruta verifica sesión; la API es totalmente abierta.
- **Explotación:** `curl -X POST http://localhost:5000/files/upload -F "file=@test.txt"` sin cookie.
- **Impacto:** Uso no autorizado completo de la aplicación.

---

### VULN-06 — IDOR (acceso a archivos de otros usuarios)
- **OWASP:** A01:2021 Broken Access Control
- **Severidad:** Alta (8.1)
- **Ubicación:** `v1-insecure/app.py` — `dashboard()` y `list_files()` (`SELECT * FROM files`)
- **Descripción:** No se filtra por propietario; cualquier usuario autenticado ve/descarga archivos de todos.
- **Explotación:** Dos cuentas (`ana` y `pedro`): el dashboard de una lista los archivos de la otra.
- **Impacto:** Fuga de datos entre usuarios.

---

### VULN-07 — Errores con información interna
- **OWASP:** A05:2021 Security Misconfiguration
- **Severidad:** Media (5.3)
- **Ubicación:** `v1-insecure/app.py` — login (`error = "... Query ejecutada: " + query`)
- **Descripción:** Se expone la query SQL completa, revelando el esquema de la DB y detalles de implementación.
- **Impacto:** Reconocimiento facilitado para el atacante.

---

### VULN-08 — Debug mode activo
- **OWASP:** A05:2021 Security Misconfiguration
- **Severidad:** Alta (7.5)
- **Ubicación:** `v1-insecure/app.py` — `app.run(debug=True, ...)`
- **Descripción:** El debugger interactivo de Werkzeug queda expuesto.
- **Explotación:** `GET /no-existe` → console de ejecución de código (RCE asistido por debugger).
- **Impacto:** Ejecución remota de código con credenciales del debugger.

---

### VULN-09 — Ejecución Remota de Código (RCE) — NUEVO
- **OWASP:** A03:2021 Injection (Command Injection)
- **Severidad:** **Crítica (10.0)**
- **Ubicación:** `v1-insecure/app.py` — `server_status()`; `v1-insecure/templates/server_status.html`
- **Descripción:** El endpoint de diagnóstico `/server_status` recibe un `command` por POST/GET y lo pasa **directamente** a `os.popen()` sin validación ni sanitización.
- **Explotación:**
  ```bash
  curl -X POST http://localhost:5000/server_status -d "command=id"
  curl "http://localhost:5000/server_status?command=cat%20/etc/passwd"
  curl -X POST http://localhost:5000/server_status -d "command=whoami;ls -la /"
  ```
- **Impacto:** Control total del sistema operativo del contenedor/servidor: lectura de archivos, exfiltración, pivoteo, ransomware.

---

### VULN-10 — Stored XSS — NUEVO
- **OWASP:** A03:2021 Injection (Cross-Site Scripting)
- **Severidad:** Alta (8.2)
- **Ubicación:** `v1-insecure/templates/dashboard.html` — `{{ f.filename | safe }}`
- **Descripción:** El nombre de un archivo subido (o renombrado vía PUT) se almacena en la DB y se renderiza en el dashboard **sin escapar** (filtro `|safe`). El vector persiste para todos los visitantes.
- **Explotación:**
  ```bash
  # Payload sin '/' (evita crear subdirectorios al guardar el archivo)
  curl -X POST http://localhost:5000/files/upload \
    -F "file=@x.txt;filename=<img src=x onerror=alert(document.cookie)>.txt"
  # Luego visitar /dashboard → se ejecuta el script
  ```
  O vía PUT (renombrar) sobre un archivo existente.
- **Impacto:** Robo de cookies de sesión, secuestro de sesión, keylogging, defacement.

---

### VULN-11 — Reflected XSS — NUEVO
- **OWASP:** A03:2021 Injection (Cross-Site Scripting)
- **Severidad:** Media (6.1)
- **Ubicación:** `v1-insecure/templates/login.html` — `{{ error | safe }}`
- **Descripción:** El mensaje de error del login incluye el input del usuario (dentro de la query SQL) y se renderiza con `|safe`, reflejando el payload sin escapar.
- **Explotación:**
  ```text
  Usuario: <script>alert(1)</script>
  Password: x
  ```
- **Impacto:** Ejecución de script en el contexto de la víctima (requiere interacción para que visite una URL con el payload).

---

### VULN-12 — CSRF — NUEVO
- **OWASP:** A07:2021 Identification and Authentication Failures
- **Severidad:** Media (5.3)
- **Ubicación:** `v1-insecure/app.py` (login, register, logout, upload) y templates correspondientes
- **Descripción:** Las transacciones de cambio de estado carecen **por completo** de tokens anti-CSRF. El `logout` además opera por **GET** (abusable con un `<img>`).
- **Explotación:**
  ```html
  <!-- desde un sitio externo, contra la víctima autenticada -->
  <img src="http://localhost:5000/logout">
  <form action="http://localhost:5000/files/upload" method="POST" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit">
  </form>
  ```
- **Impacto:** Logout forzado (DoS de sesión), subida de archivos maliciosos o registro de cuentas en nombre de la víctima.

---

## Notas sobre la versión v2 (sanitizada)

Las 12 vulnerabilidades se corrigen en `v2-secure/` de la siguiente forma:

| Vulnerabilidad | Mitigación en v2 |
|---|---|
| SQLi | Queries parametrizadas (`?`) |
| Passwords | Hash **bcrypt** (`bcrypt` lib) en registro y verificación |
| Secret key | Variable de entorno |
| Upload | Whitelist de extensiones + límite 5 MB + nombre UUID |
| Sin auth / IDOR | Decorador `@login_required` + filtro por `owner_id` |
| Errores / debug | Mensajes genéricos + `debug=False` |
| RCE | Endpoint no existe (sin funcionalidad de ejecución) |
| XSS | Autoescape de Jinja2 activo (sin `\|safe` en ningún lado) |
| CSRF | Pendiente de implementar en Fase 2 (token real) |

> **Deuda detectada en auditoría**: el `csrf_token` que aparece en `v2-secure/app/templates/login.html` es un placeholder que el backend **no verifica** (`session.get('_id','')`). No constituye protección real. Se planifica un token CSRF real en la Fase 2.
