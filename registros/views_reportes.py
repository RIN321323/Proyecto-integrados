from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from .utils import GeneradorREM

@login_required
def reporte_rem(request):
    if request.method == 'POST':
        try:
            fecha_inicio = datetime.strptime(request.POST['fecha_inicio'], '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(request.POST['fecha_fin'], '%Y-%m-%d').date()
            
            if fecha_inicio > fecha_fin:
                messages.error(request, 'La fecha de inicio debe ser anterior a la fecha final.')
                return render(request, 'registros/reporte_rem.html')
            
            generador = GeneradorREM(fecha_inicio, fecha_fin)
            
            
            tipo_reporte = request.POST.get('tipo_reporte')
            if tipo_reporte == 'bs22':
                datos = generador.rem_bs22()
            elif tipo_reporte == 'a09':
                datos = generador.rem_a09()
            elif tipo_reporte == 'a04':
                datos = generador.rem_a04()
            else:
                messages.error(request, 'Tipo de reporte no válido.')
                return render(request, 'registros/reporte_rem.html')
         
            if request.POST.get('formato') == 'excel':
                if tipo_reporte == 'datos_completos':
                    from .excel_export import exportar_datos_excel
                    return exportar_datos_excel(fecha_inicio, fecha_fin)
                else:
                    excel_data = generador.exportar_excel()
                    response = HttpResponse(
                        excel_data,
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    response['Content-Disposition'] = f'attachment; filename=REM_{tipo_reporte}_{fecha_inicio}_{fecha_fin}.xlsx'
                    return response
            
            return render(request, 'registros/reporte_rem.html', {
                'datos': datos,
                'tipo_reporte': tipo_reporte,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            })
            
        except ValueError as e:
            messages.error(request, f'Error en el formato de las fechas: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error al generar el reporte: {str(e)}')
    
    return render(request, 'registros/reporte_rem.html')