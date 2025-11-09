# Prototipo PI1 - Obstetricia

Resumen rápido

Este repositorio contiene una aplicación Django para registro de partos (madres, partos, recién nacidos). Incluye utilidades de búsqueda/creación rápida de madre, exportes a Excel y formularios compuestos.

Requisitos

- Python 3.10+ (este repo se ha probado en 3.11/3.12 en desarrollo)
- Virtualenv / venv
- Dependencias listadas en `requirements.txt` (si no existe, instale Django y pandas/openpyxl):

    pip install django pandas openpyxl

Configuración local (Windows PowerShell)

```powershell
# Crear virtualenv
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"

# Instalar dependencias
pip install -r requirements.txt  # si existe
# o mínimo
pip install django pandas openpyxl

# Migraciones
python manage.py migrate

# Crear superuser
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver
```

Pruebas

```powershell
& ".\.venv\Scripts\Activate.ps1"
python manage.py test
```

Notas de seguridad (producción)

- Asegúrese de configurar `DEBUG = False` en `obstetricia/settings.py`.
- Establezca `ALLOWED_HOSTS` apropiadamente.
- Habilite `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, y HSTS (`SECURE_HSTS_SECONDS`).
- Use un secreto fuerte en `SECRET_KEY` (no lo deje en el repo).

Mejoras aplicadas en esta ronda

- Tests básicos para el endpoint `madre_create` (happy path + duplicate RUT).
- Validación cliente en modal "Crear Madre" para evitar envíos vacíos.
- Índices DB sugeridos en campos frecuentemente consultados (`Madre.rut`, `Parto.fecha_hora`, `RecienNacido.hora_nacimiento`).

Siguientes pasos recomendados

- Ejecutar `python manage.py makemigrations` y revisar migraciones.
- Añadir más tests de integración para el flujo completo de registro de parto.
- Añadir CI (GitHub Actions) para ejecutar tests automáticamente.
- Revisión de accesibilidad y consistencia visual de la UI.

Si quieres que aplique migraciones, añada más tests o configure CI, dime cuál prefieres y lo hago.
