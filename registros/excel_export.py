from django.http import HttpResponse
from io import BytesIO
from datetime import datetime
from django.utils import timezone



def exportar_datos_excel(fecha_inicio=None, fecha_fin=None):
    """
    Exporta todos los datos de partos y recién nacidos a un archivo Excel
    con múltiples hojas y formato mejorado.
    Si fecha_inicio y fecha_fin son None, exporta todos los partos.
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
        # Obtener los datos - evaluar el queryset para asegurarse de que se ejecute
        partos_qs = Parto.objects.select_related('madre', 'created_by').prefetch_related('recien_nacidos').order_by('-fecha_hora')
        
        # Filtrar por fecha solo si se proporcionaron fechas válidas
        if fecha_inicio and fecha_fin:
            partos = partos_qs.filter(
                fecha_hora__date__range=[fecha_inicio, fecha_fin]
            )
        else:
            # Si no hay fechas, exportar todos los partos
            partos = partos_qs
        
        # Evaluar el queryset para obtener la lista (limitar a 10000 para evitar problemas de memoria)
        partos_list = list(partos[:10000])
        
        # Datos de las madres
        datos_madres = []
        for parto in partos_list:
            try:
                edad = (parto.fecha_hora.date() - parto.madre.fecha_nacimiento).days // 365
            except:
                edad = None
            datos_madres.append({
                'RUT': parto.madre.rut,
                'Nombres': parto.madre.nombres,
                'Apellidos': parto.madre.apellidos,
                'Fecha Nacimiento': parto.madre.fecha_nacimiento,
                'Edad': edad,
                'Estado Civil': parto.madre.estado_civil,
                'Dirección': parto.madre.direccion,
                'Teléfono': parto.madre.telefono,
                'Previsión': parto.madre.prevision
            })

        # Datos de los partos
        datos_partos = []
        for parto in partos_list:
            # Convertir datetime con timezone a naive datetime para Excel
            fecha_hora_naive = parto.fecha_hora
            if timezone.is_aware(fecha_hora_naive):
                # Convertir a la zona horaria local y luego a naive
                fecha_hora_naive = timezone.localtime(fecha_hora_naive).replace(tzinfo=None)
            
            created_at_naive = parto.created_at
            if timezone.is_aware(created_at_naive):
                # Convertir a la zona horaria local y luego a naive
                created_at_naive = timezone.localtime(created_at_naive).replace(tzinfo=None)
            
            datos_partos.append({
                'RUT Madre': parto.madre.rut,
                'Fecha y Hora': fecha_hora_naive,
                'Tipo Parto': parto.tipo_parto,
                'Semanas Gestación': parto.semanas_gestacion,
                'Tipo Anestesia': parto.tipo_anestesia,
                'Complicaciones': parto.complicaciones or '',
                'Observaciones': parto.observaciones or '',
                'Registrado por': parto.created_by.get_full_name() if parto.created_by and parto.created_by.get_full_name() else (parto.created_by.username if parto.created_by else 'Sistema'),
                'Fecha Registro': created_at_naive
            })

        # Datos de recién nacidos
        datos_rn = []
        for parto in partos_list:
            for rn in parto.recien_nacidos.all():
                # Convertir hora_nacimiento a naive si es datetime con timezone
                hora_nacimiento_naive = rn.hora_nacimiento
                if hora_nacimiento_naive and timezone.is_aware(hora_nacimiento_naive):
                    # Convertir a la zona horaria local y luego a naive
                    hora_nacimiento_naive = timezone.localtime(hora_nacimiento_naive).replace(tzinfo=None)
                
                datos_rn.append({
                    'RUT Madre': parto.madre.rut,
                    'Fecha Parto': parto.fecha_hora.date(),
                    'Hora Nacimiento': hora_nacimiento_naive,
                    'Sexo': 'Masculino' if rn.sexo == 'M' else 'Femenino',
                    'Peso (kg)': float(rn.peso) if rn.peso else None,
                    'Talla (cm)': float(rn.talla) if rn.talla else None,
                    'APGAR 1min': rn.apgar_1,
                    'APGAR 5min': rn.apgar_5,
                    'Estado': rn.estado,
                    'Observaciones': rn.observaciones or ''
                })

        # Crear DataFrames - usar columnas definidas si están vacíos
        if datos_madres:
            df_madres = pd.DataFrame(datos_madres)
        else:
            df_madres = pd.DataFrame(columns=['RUT', 'Nombres', 'Apellidos', 'Fecha Nacimiento', 'Edad', 'Estado Civil', 'Dirección', 'Teléfono', 'Previsión'])
        
        if datos_partos:
            df_partos = pd.DataFrame(datos_partos)
        else:
            df_partos = pd.DataFrame(columns=['RUT Madre', 'Fecha y Hora', 'Tipo Parto', 'Semanas Gestación', 'Tipo Anestesia', 'Complicaciones', 'Observaciones', 'Registrado por', 'Fecha Registro'])
        
        if datos_rn:
            df_rn = pd.DataFrame(datos_rn)
        else:
            df_rn = pd.DataFrame(columns=['RUT Madre', 'Fecha Parto', 'Hora Nacimiento', 'Sexo', 'Peso (kg)', 'Talla (cm)', 'APGAR 1min', 'APGAR 5min', 'Estado', 'Observaciones'])

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
    
    # Generar nombre de archivo
    if fecha_inicio and fecha_fin:
        filename = f'Registros_Partos_{fecha_inicio}_{fecha_fin}.xlsx'
    else:
        filename = f'Registros_Partos_Completo_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response