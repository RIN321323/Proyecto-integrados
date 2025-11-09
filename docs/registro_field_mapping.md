Registro de Parto — mapeo de campos POST (prefijos)

Cuando la vista `registros:registro_parto` utiliza los prefijos `('madre','parto','recien')`, los inputs enviados en el POST deben tener los siguientes `name` (clave) esperadas:

- Madre (prefix `madre`)
  - madre-rut
  - madre-nombres
  - madre-apellidos
  - madre-fecha_nacimiento (YYYY-MM-DD)
  - madre-estado_civil
  - madre-direccion
  - madre-telefono
  - madre-prevision

- Parto (prefix `parto`)
  - parto-fecha_hora (datetime-local: YYYY-MM-DDTHH:MM)
  - parto-tipo_parto
  - parto-semanas_gestacion
  - parto-tipo_anestesia
  - parto-complicaciones
  - parto-observaciones

- Recién Nacido (prefix `recien`)
  - recien-hora_nacimiento (HH:MM)
  - recien-sexo
  - recien-peso
  - recien-talla
  - recien-apgar_1
  - recien-apgar_5
  - recien-estado
  - recien-observaciones

Notas:
- El prefijo se une con `-` al nombre del campo en el ModelForm: `<prefix>-<field_name>`.
- Asegúrate de que el JavaScript de la plantilla seleccione los inputs por `name` (o usando `{{ form.FIELD.html_name }}`) si el formulario usa `prefix`.
- Si el POST muestra claves duplicadas (ej. `observaciones` sin prefijo varias veces), indica que el HTML se está renderizando sin usar los `prefix` y habrá conflictos — el payload sólo contendrá el último valor para ese name y las otras entradas se perderán.

Ver también: `registros/forms.py` (PartoCompletoForm), `registros/views.py` (registro_parto) — por defecto la app usa `prefixes=('madre','parto','recien')` para evitar colisiones.