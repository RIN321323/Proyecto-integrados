import re
from django import forms
from django.core.validators import RegexValidator
from .models import Madre, Parto, RecienNacido

class MadreForm(forms.ModelForm):
    # Accept both formatted and unformatted RUT input (dots/dash optional);
    # final formatting is applied in clean_rut().
    rut_validator = RegexValidator(
        regex=r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$',
        message='El formato del RUT debe ser XX.XXX.XXX-X (por ejemplo: 12.345.678-9)'
    )
    rut = forms.CharField(
        validators=[rut_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Formato: XX.XXX.XXX-X (Ej: 12.345.678-9)',
            'pattern': r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$'
        })
    )

    def clean_rut(self):
        from .utils import normalize_rut, format_rut, validate_rut
        raw = self.cleaned_data.get('rut', '')

        # Si ya está en formato correcto, solo validamos
        if re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', raw):
            clean = re.sub(r'[^0-9kK]', '', raw).upper()
            if not validate_rut(clean):
                raise forms.ValidationError('El dígito verificador no coincide. Revise el último dígito del RUT')
            return raw

        # Si no está formateado, intentamos formatearlo
        clean = re.sub(r'[^0-9kK]', '', raw).upper()
        
        # Validaciones básicas
        if not clean or len(clean) < 2:
            raise forms.ValidationError('El formato del RUT debe ser XX.XXX.XXX-X (por ejemplo: 12.345.678-9)')
        
        number = clean[:-1]
        if not number.isdigit():
            raise forms.ValidationError('El RUT debe contener solo números y un dígito verificador')
        
        if int(number) < 1000000:
            raise forms.ValidationError('El RUT debe ser mayor a 1.000.000')
        
        # Si el RUT es válido, lo formateamos y retornamos
        if validate_rut(clean):
            formatted = format_rut(clean)
            # Si el formato resultante no coincide con el patrón esperado
            if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', formatted):
                raise forms.ValidationError('El formato del RUT debe ser XX.XXX.XXX-X (por ejemplo: 12.345.678-9)')
            return formatted
            
        raise forms.ValidationError('El dígito verificador no coincide. Revise el último dígito del RUT')
    
    class Meta:
        model = Madre
        fields = ['rut', 'nombres', 'apellidos', 'fecha_nacimiento', 
                 'estado_civil', 'direccion', 'telefono', 'prevision']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 XXXX XXXX'
            }),
            'prevision': forms.Select(attrs={'class': 'form-select'}),
        }

class PartoForm(forms.ModelForm):
    # The browser's datetime-local uses the 'T' separator (YYYY-MM-DDTHH:MM).
    # Provide a DateTimeField with matching input_formats and widget format so
    # the form will validate when the user submits from the template.
    fecha_hora = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }, format='%Y-%m-%dT%H:%M'),
        # Accept several common formats: browser 'datetime-local', ISO with space,
        # and the DD-MM-YYYY HH:MM format used by templates in this project.
        input_formats=[
            '%Y-%m-%dT%H:%M',  # browser datetime-local
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%d-%m-%Y %H:%M',   # form uses day-month-year in templates
        ]
    )
    class Meta:
        model = Parto
        fields = ['fecha_hora', 'tipo_parto', 'semanas_gestacion', 
                 'tipo_anestesia', 'complicaciones', 'observaciones']
        widgets = {
            # fecha_hora widget is provided explicitly above so we don't
            # need to redefine it here. Keep other widgets below.
            'tipo_parto': forms.Select(attrs={'class': 'form-select'}),
            'semanas_gestacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '20',
                'max': '45'
            }),
            'tipo_anestesia': forms.Select(attrs={'class': 'form-select'}),
            'complicaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

class RecienNacidoForm(forms.ModelForm):
    class Meta:
        model = RecienNacido
        fields = ['hora_nacimiento', 'sexo', 'peso', 'talla', 
                 'apgar_1', 'apgar_5', 'estado', 'observaciones']
        widgets = {
            'hora_nacimiento': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'peso': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.1',
                'max': '6.0'
            }),
            'talla': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '20',
                'max': '60'
            }),
            'apgar_1': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10'
            }),
            'apgar_5': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10'
            }),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

class PartoCompletoForm(forms.Form):
    """
    Formulario que combina los tres formularios anteriores para un registro completo
    """
    def __init__(self, *args, prefixes=None, allow_old_parto=False, **kwargs):
        """Initialize nested forms. If `prefixes` is provided it must be a
        3-tuple (madre_prefix, parto_prefix, recien_prefix) and will be used
        so each subform's HTML name/id are namespaced and avoid collisions
        when rendered together in a single <form>.
        """
        super().__init__(*args, **kwargs)
        if prefixes:
            madre_prefix, parto_prefix, recien_prefix = prefixes
            self.madre_form = MadreForm(*args, prefix=madre_prefix, **kwargs)
            self.parto_form = PartoForm(*args, prefix=parto_prefix, **kwargs)
            self.recien_nacido_form = RecienNacidoForm(*args, prefix=recien_prefix, **kwargs)
        else:
            self.madre_form = MadreForm(*args, **kwargs)
            self.parto_form = PartoForm(*args, **kwargs)
            self.recien_nacido_form = RecienNacidoForm(*args, **kwargs)
        # If caller requests allowing old parto registration, set a flag on the
        # provisional Parto instance so its model-level clean() can bypass the
        # 48-hour restriction.
        try:
            if allow_old_parto:
                setattr(self.parto_form.instance, '_allow_old_parto', True)
        except Exception:
            pass
        
    def is_valid(self):
        madre_ok = self.madre_form.is_valid()
        parto_ok = self.parto_form.is_valid()
        if not (madre_ok and parto_ok):
            # still run recien_nacido_form.is_valid to populate errors, but without provisional context
            self.recien_nacido_form.is_valid()
            return False

        # Attach provisional parto datetime to the recien_nacido instance so its clean() can use it
        provisional_dt = self.parto_form.cleaned_data.get('fecha_hora')
        if provisional_dt:
            try:
                # set attributes on the model instance used by the form so RN.clean can use them
                self.recien_nacido_form.instance._parto_fecha_hora = provisional_dt
                semanas = self.parto_form.cleaned_data.get('semanas_gestacion')
                if semanas is not None:
                    # attach provisional semanas as integer
                    try:
                        self.recien_nacido_form.instance._parto_semanas = int(semanas)
                    except Exception:
                        pass
            except Exception:
                pass

        rn_ok = self.recien_nacido_form.is_valid()
        # If RN form reported invalid but has no errors (some model-level
        # ValidationError can be missed in edge cases), try to run the
        # model-level clean and attach messages explicitly so callers/tests
        # can inspect `recien_nacido_form.errors` reliably.
        if not rn_ok and not self.recien_nacido_form.errors:
            from django.core.exceptions import ValidationError
            try:
                # Ensure provisional context is present on instance
                inst = self.recien_nacido_form.instance
                # Call model.clean() directly to surface ValidationError
                inst.clean()
            except ValidationError as e:
                # Attach all messages as non-field errors on the RN form
                for msg in getattr(e, 'messages', [str(e)]):
                    self.recien_nacido_form.add_error(None, msg)
                rn_ok = False
            except Exception:
                # If something else fails, mark RN as invalid to be safe
                self.recien_nacido_form.add_error(None, 'Error en validación de recién nacido')
                rn_ok = False

        return madre_ok and parto_ok and rn_ok

    def save(self, commit=True):
        if not self.is_valid():
            raise ValueError("Formulario no válido")
            
        madre = self.madre_form.save(commit=commit)
        if commit:
            parto = self.parto_form.save(commit=False)
            parto.madre = madre
            parto.save()
            
            recien_nacido = self.recien_nacido_form.save(commit=False)
            recien_nacido.parto = parto
            recien_nacido.save()
            
            return madre, parto, recien_nacido
        return madre