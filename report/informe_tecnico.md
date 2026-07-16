# Informe Técnico — Aplicación de Gestión de Archivos
## SecDevOps: De una Versión Vulnerable a una Versión Segura

---

## 1. Contexto Inicial de la Aplicación

### 1.1 Descripción General

Se desarrolló una aplicación web de gestión de archivos con las siguientes funcionalidades:

- **Autenticación**: registro e inicio de sesión de usuarios
- **Subida de archivos**: carga de documentos al servidor
- **CRUD de archivos**: operaciones GET, POST, PUT y DELETE sobre los archivos

La aplicación fue construida en dos versiones: una inicial sin consideraciones de seguridad (v1) y una segunda versión con prácticas de SecDevOps aplicadas (v2).

### 1.2 Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.x |
| Framework web | Flask 3.0 |
| Base de datos | SQLite |
| Frontend | HTML5 + Bootstrap 5 |
| Gestión de dependencias | pip / requirements.txt |

### 1.3 Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/login` | Página de inicio de sesión |
| POST | `/login` | Autenticar usuario |
| GET | `/register` | Página de registro |
| POST | `/register` | Crear cuenta |
| GET | `/logout` | Cerrar sesión |
| GET | `/dashboard` | Panel principal del usuario |
| GET | `/files` | Listar archivos |
| POST | `/files/upload` | Subir archivo |
| GET | `/files/<id>` | Descargar archivo |
| PUT | `/files/<id>` | Renombrar archivo |
| DELETE | `/files/<id>` | Eliminar archivo |

---

## 2. Problemas de Seguridad en V1 (Sin SecDevOps)

### 2.1 SQL Injection

**Severidad: CRÍTICA** | OWASP A03:2021 – Injection

**Descripción:**  
Las consultas SQL en v1 se construyen concatenando directamente los valores ingresados por el usuario en los strings de las queries, sin ningún tipo de sanitización ni parametrización.

**Código vulnerable (v1):**
```python
# Login — vulnerable a SQL Injection
query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"

# Un atacante puede ingresar como usuario: ' OR '1'='1
# Query resultante: SELECT * FROM users WHERE username = '' OR '1'='1' AND password = ''
# Resultado: el atacante accede sin conocer ninguna credencial válida
```

**Impacto:**
- Bypass de autenticación completo
- Extracción, modificación o eliminación de toda la base de datos
- Escalada de privilegios

---

### 2.2 Contraseñas Almacenadas en Texto Plano

**Severidad: CRÍTICA** | OWASP A02:2021 – Cryptographic Failures

**Descripción:**  
Las contraseñas se guardan en la base de datos exactamente como el usuario las ingresa, sin ningún proceso de hashing.

**Código vulnerable (v1):**
```python
conn.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')")
```

**Impacto:**
- Si la base de datos es comprometida, todas las contraseñas quedan expuestas inmediatamente
- Riesgo de reutilización de credenciales en otros servicios (credential stuffing)

---

### 2.3 Subida de Archivos sin Validación

**Severidad: ALTA** | OWASP A04:2021 – Insecure Design

**Descripción:**  
El endpoint de subida acepta cualquier tipo de archivo, de cualquier tamaño, sin ninguna restricción.

**Código vulnerable (v1):**
```python
filename = file.filename  # Nombre original sin sanitizar
file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
```

**Impacto:**
- Subida de archivos maliciosos (scripts PHP, ejecutables)
- Denegación de servicio por archivos de gran tamaño
- Path traversal: nombre `../../app.py` sobreescribe archivos del servidor

---

### 2.4 Ausencia de Autenticación en Endpoints

**Severidad: ALTA** | OWASP A01:2021 – Broken Access Control

**Descripción:**  
Los endpoints de gestión de archivos (upload, download, update, delete) no verifican si existe una sesión activa. Cualquier usuario, incluso sin cuenta, puede hacer peticiones directas a la API.

**Impacto:**
- Cualquier persona puede subir, descargar, modificar o eliminar archivos
- No existe control de acceso entre usuarios (Broken Object Level Authorization)

---

### 2.5 Exposición de Datos de Todos los Usuarios

**Severidad: ALTA** | OWASP A01:2021 – Broken Access Control

**Descripción:**  
El dashboard y el endpoint GET `/files` retornan los archivos de **todos** los usuarios registrados.

**Código vulnerable (v1):**
```python
files = conn.execute("SELECT * FROM files").fetchall()  # Sin filtro por usuario
```

**Impacto:**
- Violación de privacidad total entre usuarios
- Un usuario puede ver, descargar y eliminar archivos de otros

---

### 2.6 Secretos Hardcodeados en el Código

**Severidad: ALTA** | OWASP A02:2021 – Cryptographic Failures

**Descripción:**  
La clave secreta de la aplicación está escrita directamente en el código fuente.

**Código vulnerable (v1):**
```python
app.secret_key = "admin123"
```

**Impacto:**
- Al subir el código a un repositorio público, cualquiera puede falsificar cookies de sesión
- Clave predecible y corta, vulnerable a fuerza bruta

---

### 2.7 Mensajes de Error Informativos

**Severidad: MEDIA** | OWASP A05:2021 – Security Misconfiguration

**Descripción:**  
Los errores exponen información interna como queries SQL ejecutadas.

**Código vulnerable (v1):**
```python
error = "Usuario o contraseña incorrectos. Query ejecutada: " + query
```

**Impacto:**
- Facilita el proceso de reconocimiento para un atacante
- Revela estructura interna de la base de datos

---

### 2.8 Modo Debug Activo con Host Abierto

**Severidad: MEDIA** | OWASP A05:2021 – Security Misconfiguration

**Descripción:**  
La aplicación corre con `debug=True` y escucha en todas las interfaces (`0.0.0.0`).

**Código vulnerable (v1):**
```python
app.run(debug=True, host="0.0.0.0", port=5000)
```

**Impacto:**
- El debugger interactivo de Werkzeug es accesible desde la red
- Permite ejecución arbitraria de código Python en el servidor

---

## 3. Soluciones Aplicadas con SecDevOps en V2

### 3.1 Principios SecDevOps Aplicados

SecDevOps (Security Development Operations) integra la seguridad en cada etapa del ciclo de desarrollo de software, a diferencia del enfoque tradicional donde la seguridad se revisa al final. Los principios aplicados fueron:

- **Shift Left**: identificar y corregir vulnerabilidades durante el desarrollo, no después
- **Least Privilege**: cada componente tiene acceso únicamente a lo que necesita
- **Defense in Depth**: múltiples capas de seguridad
- **Secure by Default**: la configuración predeterminada es segura

---

### 3.2 Corrección: SQL Injection → Queries Parametrizadas

**Solución:** Uso de `?` como placeholder y paso de parámetros como tupla separada.

```python
# V2 — Sin SQL Injection posible
user = db.execute(
    "SELECT * FROM users WHERE username = ?", (username,)
).fetchone()
```

El driver de SQLite nunca interpreta el valor del usuario como código SQL; lo trata estrictamente como dato.

---

### 3.3 Corrección: Contraseñas → Hashing con Werkzeug/bcrypt

**Solución:** Uso de `generate_password_hash` y `check_password_hash` de Werkzeug, que implementan bcrypt internamente.

```python
# Registro
generate_password_hash(password)  # Almacena hash salted

# Login
check_password_hash(user["password_hash"], password)  # Compara sin exponer el hash
```

Aunque la base de datos sea comprometida, las contraseñas no son recuperables.

---

### 3.4 Corrección: Subida de Archivos → Validación Estricta

**Solución:** Whitelist de extensiones, límite de tamaño, nombre aleatorio y `secure_filename`.

```python
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "txt", "docx"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Nombre aleatorio en disco — previene path traversal y colisiones
stored_name = f"{uuid.uuid4().hex}.{ext}"
file.save(os.path.join(upload_path, stored_name))
```

---

### 3.5 Corrección: Control de Acceso → Decorador `@login_required`

**Solución:** Decorador que verifica la sesión antes de ejecutar cualquier endpoint protegido.

```python
def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped

@files_bp.route("/files/upload", methods=["POST"])
@login_required
def upload_file():
    ...
```

---

### 3.6 Corrección: Acceso entre Usuarios → Filtro por `owner_id`

**Solución:** Todas las queries de archivos filtran por el `user_id` de la sesión activa.

```python
# Solo retorna archivos del usuario autenticado
files = db.execute(
    "SELECT * FROM files WHERE owner_id = ?", (session["user_id"],)
).fetchall()

# Al eliminar, verifica propiedad antes de actuar
f = db.execute(
    "SELECT * FROM files WHERE id = ? AND owner_id = ?",
    (file_id, session["user_id"]),
).fetchone()
```

---

### 3.7 Corrección: Secretos → Variables de Entorno

**Solución:** La clave secreta se carga desde el entorno, nunca del código fuente. El archivo `.env` está en `.gitignore`.

```python
# config.py
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32))
```

```bash
# .env (nunca subido a git)
SECRET_KEY=clave-larga-aleatoria-generada-con-openssl-rand
```

---

### 3.8 Corrección: Mensajes de Error y Debug

**Solución:** Mensajes genéricos para el usuario; `debug=False`; escucha solo en localhost.

```python
# Mensaje genérico — no revela si el usuario existe
flash("Credenciales inválidas.", "danger")

# run.py
app.run(debug=False, host="127.0.0.1", port=5001)
```

---

## 4. Tabla Comparativa de Vulnerabilidades

| Vulnerabilidad | OWASP | V1 | V2 |
|---|---|---|---|
| SQL Injection | A03 | ❌ Concatenación directa | ✅ Queries parametrizadas |
| Contraseñas texto plano | A02 | ❌ Sin hashing | ✅ bcrypt via Werkzeug |
| Archivos sin validación | A04 | ❌ Sin restricciones | ✅ Whitelist + límite 5MB |
| Sin autenticación | A01 | ❌ Endpoints abiertos | ✅ `@login_required` |
| Acceso entre usuarios | A01 | ❌ Sin filtro por usuario | ✅ Filtro por `owner_id` |
| Secretos hardcodeados | A02 | ❌ `"admin123"` en código | ✅ Variables de entorno |
| Errores informativos | A05 | ❌ Muestra queries SQL | ✅ Mensajes genéricos |
| Debug en producción | A05 | ❌ `debug=True, host="0.0.0.0"` | ✅ `debug=False, host="127.0.0.1"` |

---

## 5. Conclusiones

La transición de v1 a v2 demuestra que la seguridad no requiere complejidad adicional significativa: las mismas funcionalidades se implementan con las mismas herramientas, pero tomando decisiones correctas desde el diseño.

El enfoque **SecDevOps** garantiza que la seguridad no sea un paso final, sino una condición de cada línea de código. Las vulnerabilidades identificadas en v1 corresponden a las categorías más frecuentes del OWASP Top 10, y todas fueron corregidas sin cambiar la funcionalidad de la aplicación.

**Lecciones clave:**
1. Nunca construir queries SQL con concatenación de strings
2. Nunca almacenar contraseñas sin hashing
3. Nunca confiar en el nombre o tipo de archivo enviado por el cliente
4. Nunca dejar endpoints sin autenticación en aplicaciones que manejan datos de usuario
5. Nunca poner secretos en el código fuente

---

*Informe generado como parte de la actividad académica sobre SecDevOps.*
