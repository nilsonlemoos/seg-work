# seg-work — Aplicación de Gestión de Archivos

Proyecto académico que demuestra el impacto de SecDevOps comparando dos versiones de la misma aplicación.

## Estructura

```
seg-work/
├── v1-insecure/    # Versión con vulnerabilidades intencionales
├── v2-secure/      # Versión corregida con SecDevOps
└── report/         # Informe técnico completo
```

## Ejecutar V1 (insegura)

```bash
cd v1-insecure
pip install -r requirements.txt
python app.py
# Abre http://localhost:5000
```

## Ejecutar V2 (segura)

```bash
cd v2-secure
pip install -r requirements.txt
cp .env.example .env        # Edita con tu SECRET_KEY
python run.py
# Abre http://localhost:5001
```

## Vulnerabilidades demostradas en V1

| # | Vulnerabilidad | OWASP |
|---|---|---|
| 1 | SQL Injection en login y queries | A03 |
| 2 | Contraseñas en texto plano | A02 |
| 3 | Subida de archivos sin validación | A04 |
| 4 | Endpoints sin autenticación | A01 |
| 5 | Acceso a archivos de otros usuarios | A01 |
| 6 | Secret key hardcodeada | A02 |
| 7 | Errores que exponen queries SQL | A05 |
| 8 | Debug mode activo en producción | A05 |

Ver `report/informe_tecnico.md` para el análisis completo.
