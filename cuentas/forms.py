from django import forms
from django.core.exceptions import ValidationError
from .models import Usuario, Rol
import re

class LoginForm(forms.Form):
    username = forms.CharField(label="Usuario")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

class ProfesionalRegistroForm(forms.Form):
    # Áreas disponibles
    AREAS_CHOICES = [
        ('obstetricia', 'Obstetricia'),
        ('ginecologia', 'Ginecología'),
        ('enfermeria', 'Enfermería'),
        ('pediatria', 'Pediatría'),
        ('anestesiologia', 'Anestesiología'),
        ('medicina_familiar', 'Medicina Familiar'),
    ]
    
    nombre = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su nombre'})
    )
    apellido = forms.CharField(
        label="Apellido",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su apellido'})
    )
    run = forms.CharField(
        label="RUN",
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'})
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56912345678'})
    )
    area = forms.ChoiceField(
        label="Área",
        choices=AREAS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres'})
    )
    password_confirm = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita la contraseña'})
    )
    
    def clean_run(self):
        run = self.cleaned_data.get('run')
        if run:
            # Limpiar el RUN (quitar puntos y espacios)
            run = run.replace('.', '').replace(' ', '').upper()
            # Validar formato: debe ser XXXXXXXX-X
            if not re.match(r'^\d{7,8}-[\dkK]$', run):
                raise ValidationError('El RUN debe tener el formato: 12345678-9')
            
            # Verificar si ya existe
            if Usuario.objects.filter(run=run).exists():
                raise ValidationError('Este RUN ya está registrado en el sistema')
        return run
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Limpiar el teléfono (quitar espacios, guiones, paréntesis)
            telefono = re.sub(r'[\s\-\(\)]', '', telefono)
            # Validar que contenga solo números y opcionalmente +
            if not re.match(r'^\+?\d{8,15}$', telefono):
                raise ValidationError('Ingrese un número de teléfono válido')
        return telefono
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Las contraseñas no coinciden')
        
        return cleaned_data
