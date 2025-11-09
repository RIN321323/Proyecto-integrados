from django.http import HttpResponse
from io import BytesIO
from datetime import datetime



def exportar_datos_excel(fecha_inicio, fecha_fin):
    """
    Exporta todos los datos de partos y recién nacidos a un archivo Excel
    con múltiples hojas y formato mejorado.
    """
    # Import pandas lazily so tests that don't call export don't require it
    try:
        import pandas as pd
    except Exception:
        return HttpResponse('Export unavailable: pandas not installed', status=500)

    # Import models here to avoid touching Django settings at module import time
    from .models import Madre, Parto, RecienNacido

    # Crear un archivo Excel con múltiples hojas
    output = BytesIO()
    # Use a context manager for ExcelWriter to ensure resources are flushed/closed
    # and be compatible with different pandas/openpyxl versions.
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Obtener los datos
        partos = Parto.objects.filter(
            fecha_hora__date__range=[fecha_inicio, fecha_fin]
        ).select_related('madre', 'created_by').prefetch_related('recien_nacidos')

        # Datos de las madres
        datos_madres = []
        for parto in partos:
            datos_madres.append({
                'RUT': parto.madre.rut,
                'Nombres': parto.madre.nombres,
                'Apellidos': parto.madre.apellidos,
                'Fecha Nacimiento': parto.madre.fecha_nacimiento,
                'Edad': (parto.fecha_hora.date() - parto.madre.fecha_nacimiento).days // 365,
                'Estado Civil': parto.madre.estado_civil,
                'Dirección': parto.madre.direccion,
                'Teléfono': parto.madre.telefono,
                'Previsión': parto.madre.prevision
            })

        # Datos de los partos
        datos_partos = []
        for parto in partos:
            datos_partos.append({
                'RUT Madre': parto.madre.rut,
                'Fecha y Hora': parto.fecha_hora,
                'Tipo Parto': parto.tipo_parto,
                'Semanas Gestación': parto.semanas_gestacion,
                'Tipo Anestesia': parto.tipo_anestesia,
                'Complicaciones': parto.complicaciones,
                'Observaciones': parto.observaciones,
                'Registrado por': parto.created_by.get_full_name() if parto.created_by else '',
                'Fecha Registro': parto.created_at
            })

        # Datos de recién nacidos
        datos_rn = []
        for parto in partos:
            for rn in parto.recien_nacidos.all():
                datos_rn.append({
                    'RUT Madre': parto.madre.rut,
                    'Fecha Parto': parto.fecha_hora.date(),
                    'Hora Nacimiento': rn.hora_nacimiento,
                    'Sexo': 'Masculino' if rn.sexo == 'M' else 'Femenino',
                    'Peso (kg)': rn.peso,
                    'Talla (cm)': rn.talla,
                    'APGAR 1min': rn.apgar_1,
                    'APGAR 5min': rn.apgar_5,
                    'Estado': rn.estado,
                    'Observaciones': rn.observaciones
                })

        # Crear DataFrames
        df_madres = pd.DataFrame(datos_madres)
        df_partos = pd.DataFrame(datos_partos)
        df_rn = pd.DataFrame(datos_rn)

        # Guardar en diferentes hojas
        df_madres.to_excel(writer, sheet_name='Madres', index=False)
        df_partos.to_excel(writer, sheet_name='Partos', index=False)
        df_rn.to_excel(writer, sheet_name='Recién Nacidos', index=False)

        # Ajustar el ancho de las columnas en cada hoja
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(worksheet.columns, 1):
                max_length = 0
                column = worksheet.column_dimensions[worksheet.cell(row=1, column=idx).column_letter]
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except Exception:
                        pass
                adjusted_width = (max_length + 2)
                column.width = min(adjusted_width, 50)  # Máximo 50 caracteres de ancho

    # Después del context manager el escritor ha sido cerrado y el buffer contiene los datos
    output.seek(0)

    # Crear la respuesta HTTP
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=Registros_Partos_{fecha_inicio}_{fecha_fin}.xlsx'
    
    return response