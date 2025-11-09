import re


def calculate_dv(rut_number: str) -> str:
    """Calculate verification digit for Chilean RUT."""
    reversed_digits = map(int, reversed(str(rut_number)))
    factors = (2, 3, 4, 5, 6, 7)
    s = 0
    for d, f in zip(reversed_digits, factors * 2):  # Use factors * 2 to handle longer numbers
        s += d * f
    dv = 11 - (s % 11)
    if dv == 11:
        return '0'
    if dv == 10:
        return 'K'
    return str(dv)

def validate_rut(rut: str) -> bool:
    """Validate Chilean RUT. Returns True if valid."""
    if not rut:
        return False
    
    clean = re.sub(r'[^0-9kK]', '', rut).upper()
    if len(clean) < 2:
        return False
    
    number = clean[:-1]
    dv = clean[-1]
   
    if not number.isdigit():
        return False
    if int(number) < 1000000:  
        return False
    
    expected_dv = calculate_dv(number)
    return dv == expected_dv

def normalize_rut(raw: str) -> str:
    """Return cleaned rut: only digits + dv (uppercase), no dots or dash.
    Returns empty string if the RUT is invalid."""
    if not raw:
        return ''
    s = re.sub(r'[^0-9kK]', '', raw)
    s = s.upper()
    if not validate_rut(s):
        return ''
    return s


def format_rut(clean: str) -> str:
    """Format a cleaned rut (digits+dv) into XX.XXX.XXX-X style if possible."""
    if not clean:
        return ''
   
    dv = clean[-1]
    num = clean[:-1]
    
    parts = []
    while len(num) > 3:
        parts.insert(0, num[-3:])
        num = num[:-3]
    if num:
        parts.insert(0, num)
    return '.'.join(parts) + '-' + dv
from datetime import datetime
from django.db.models import Count, Q
from .models import Parto, RecienNacido

class GeneradorREM:
    def __init__(self, fecha_inicio, fecha_fin):
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.partos = Parto.objects.filter(
            fecha_hora__date__range=[fecha_inicio, fecha_fin]
        ).select_related('madre').prefetch_related('recien_nacidos')

    def rem_bs22(self):
        """
        Genera datos para el REM-BS22 (Atenciones de Obstetricia y Ginecología)
        """
    
        datos = {
            'total_partos': 0,
            'partos_por_tipo': {
                'vaginal': 0,
                'cesarea': 0,
                'forceps': 0
            },
            'partos_por_edad': {
                'menor_15': 0,
                '15_19': 0,
                '20_24': 0,
                '25_29': 0,
                '30_34': 0,
                '35_mas': 0
            },
            'anestesia': {
                'ninguna': 0,
                'local': 0,
                'epidural': 0,
                'raquidea': 0,
                'general': 0
            }
        }

       
        tipos_parto = self.partos.values('tipo_parto').annotate(
            total=Count('id')
        )
        for tipo in tipos_parto:
            datos['partos_por_tipo'][tipo['tipo_parto']] = tipo['total']
            datos['total_partos'] += tipo['total']

       
        for parto in self.partos:
            edad = (parto.fecha_hora.date() - parto.madre.fecha_nacimiento).days // 365
            if edad < 15:
                datos['partos_por_edad']['menor_15'] += 1
            elif edad <= 19:
                datos['partos_por_edad']['15_19'] += 1
            elif edad <= 24:
                datos['partos_por_edad']['20_24'] += 1
            elif edad <= 29:
                datos['partos_por_edad']['25_29'] += 1
            elif edad <= 34:
                datos['partos_por_edad']['30_34'] += 1
            else:
                datos['partos_por_edad']['35_mas'] += 1

       
        tipos_anestesia = self.partos.values('tipo_anestesia').annotate(
            total=Count('id')
        )
        for tipo in tipos_anestesia:
            datos['anestesia'][tipo['tipo_anestesia']] = tipo['total']

        return datos

    def rem_a09(self):
        """
        Genera datos para el REM-A09 (Egresos Hospitalarios)
        """
        datos = {
            'egresos_total': 0,
            'motivo_egreso': {
                'alta': 0,
                'traslado': 0,
                'defuncion': 0
            },
            'estadia_promedio': 0  
        }

   
        return datos

    def rem_a04(self):
        """
        Genera datos para el REM-A04 (Defunciones)
        """
        datos = {
            'defunciones_total': 0,
            'defunciones_por_edad': {
                'menor_1_hora': 0,
                '1_23_horas': 0,
                '1_7_dias': 0,
                '8_27_dias': 0,
                '28_dias_mas': 0
            }
        }


        recien_nacidos = RecienNacido.objects.filter(
            parto__fecha_hora__date__range=[self.fecha_inicio, self.fecha_fin],
            estado='fallecido'
        )
        datos['defunciones_total'] = recien_nacidos.count()

        return datos

    def exportar_excel(self):
        """
        Exporta los datos a Excel incluyendo todos los REM
        """
        import pandas as pd
        from io import BytesIO

 
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')


        datos_bs22 = self.rem_bs22()
        df_bs22 = pd.DataFrame([datos_bs22])
        df_bs22.to_excel(writer, sheet_name='REM-BS22', index=False)

        datos_a09 = self.rem_a09()
        df_a09 = pd.DataFrame([datos_a09])
        df_a09.to_excel(writer, sheet_name='REM-A09', index=False)

        datos_a04 = self.rem_a04()
        df_a04 = pd.DataFrame([datos_a04])
        df_a04.to_excel(writer, sheet_name='REM-A04', index=False)

        writer.save()
        return output.getvalue()