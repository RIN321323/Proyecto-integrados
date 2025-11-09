from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Madre(models.Model):
    ESTADO_CIVIL_CHOICES = [
        ('soltera', 'Soltera'),
        ('casada', 'Casada'),
        ('viuda', 'Viuda'),
        ('divorciada', 'Divorciada'),
        ('conviviente', 'Conviviente'),
    ]

    PREVISION_CHOICES = [
        ('fonasa_a', 'Fonasa A'),
        ('fonasa_b', 'Fonasa B'),
        ('fonasa_c', 'Fonasa C'),
        ('fonasa_d', 'Fonasa D'),
        ('isapre', 'Isapre'),
        ('particular', 'Particular'),
        ('prais', 'PRAIS'),
        ('otra', 'Otra'),
    ]

    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT", db_index=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    estado_civil = models.CharField(max_length=20, choices=ESTADO_CIVIL_CHOICES)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=15)
    prevision = models.CharField(max_length=20, choices=PREVISION_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='madres_creadas'
    )

    def clean(self):
        # Normalize rut first
        try:
            from .utils import normalize_rut, format_rut
            norm = normalize_rut(self.rut)
            if norm:
                self.rut = format_rut(norm)
        except Exception:
            pass
        from django.core.exceptions import ValidationError
        from datetime import date
        import re

        # Validar edad mínima y máxima
        if self.fecha_nacimiento:
            edad = (date.today() - self.fecha_nacimiento).days // 365
            if edad < 12:
                raise ValidationError('La paciente debe tener al menos 12 años.')
            if edad > 60:
                raise ValidationError('Por favor, verifique la fecha de nacimiento.')


        # Validar dígito verificador del RUT
        rut_limpio = self.rut.replace('.', '').replace('-', '')
        dv = rut_limpio[-1].upper()
        rut_numero = int(rut_limpio[:-1])
        
        calculated_dv = self.calcular_dv(rut_numero)
        if dv != calculated_dv:
            raise ValidationError('El RUT ingresado no es válido.')

        # Validar formato del teléfono: aceptar varios formatos comunes (+56 9 9xxxxxxxx, 9xxxxxxxx, with spaces/dashes)
        if self.telefono:
            if not re.match(r'^[0-9\+\s\-()]{7,20}$', self.telefono):
                raise ValidationError('El formato del teléfono parece inválido. Use +56 9 XXXXXXXX o formato local.')

    @staticmethod
    def calcular_dv(rut):
        multiplicador = 2
        suma = 0
        while rut > 0:
            suma += (rut % 10) * multiplicador
            multiplicador += 1
            if multiplicador > 7:
                multiplicador = 2
            rut //= 10
        resto = suma % 11
        if resto == 0:
            return 'K'
        elif resto == 1:
            return '0'
        else:
            return str(11 - resto)

    @property
    def edad(self):
        from datetime import date
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.rut}"

    class Meta:
        verbose_name = "Madre"
        verbose_name_plural = "Madres"

class Parto(models.Model):
    TIPO_PARTO_CHOICES = [
        ('vaginal', 'Vaginal'),
        ('cesarea', 'Cesárea'),
        ('forceps', 'Fórceps'),
    ]

    TIPO_ANESTESIA_CHOICES = [
        ('ninguna', 'Ninguna'),
        ('local', 'Local'),
        ('epidural', 'Epidural'),
        ('raquidea', 'Raquídea'),
        ('general', 'General'),
    ]

    madre = models.ForeignKey(Madre, on_delete=models.CASCADE, related_name='partos')
    fecha_hora = models.DateTimeField(db_index=True)
    tipo_parto = models.CharField(max_length=20, choices=TIPO_PARTO_CHOICES)
    semanas_gestacion = models.IntegerField(
        validators=[MinValueValidator(20), MaxValueValidator(45)]
    )
    tipo_anestesia = models.CharField(max_length=20, choices=TIPO_ANESTESIA_CHOICES)
    complicaciones = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='partos_registrados'
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        from datetime import timedelta
        from django.utils import timezone

        # Validar que la fecha no sea futura (use timezone-aware now)
        now = timezone.now()
        if self.fecha_hora and self.fecha_hora > now:
            raise ValidationError('La fecha y hora no puede ser futura.')

        # Validar que la fecha no sea anterior a 48 horas
        # Allow bypass when instance has been flagged (e.g., via a form wrapper)
        allow_old = getattr(self, '_allow_old_parto', False)
        if not allow_old and self.fecha_hora and self.fecha_hora < now - timedelta(hours=48):
            raise ValidationError('No se pueden registrar partos con más de 48 horas de antigüedad.')

        # Validar edad gestacional
        if self.semanas_gestacion:
            if self.semanas_gestacion < 20:
                raise ValidationError('La edad gestacional no puede ser menor a 20 semanas.')
            if self.semanas_gestacion > 45:
                raise ValidationError('La edad gestacional no puede ser mayor a 45 semanas.')

    def save(self, *args, **kwargs):
        # Registrar usuario que crea/modifica el registro
        if not self.pk and not self.created_by:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.created_by = User.get_current_user() if hasattr(User, 'get_current_user') else None
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Parto de {self.madre} - {self.fecha_hora.date()}"

    class Meta:
        verbose_name = "Parto"
        verbose_name_plural = "Partos"
        ordering = ['-fecha_hora']  # Ordenar por fecha descendente

class RecienNacido(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    ESTADO_CHOICES = [
        ('vivo', 'Vivo'),
        ('fallecido', 'Fallecido'),
    ]

    parto = models.ForeignKey(Parto, on_delete=models.CASCADE, related_name='recien_nacidos')
    hora_nacimiento = models.TimeField(db_index=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    peso = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        validators=[MinValueValidator(0.1), MaxValueValidator(6.0)]
    )
    talla = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(20), MaxValueValidator(60)]
    )
    apgar_1 = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    apgar_5 = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='vivo')
    observaciones = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        from datetime import datetime, timedelta
        import logging
        logger = logging.getLogger(__name__)
        # Validar hora de nacimiento con respecto a la hora del parto
        # Use parto_id to avoid accessing related descriptor when FK not assigned yet
        parto_obj = None
        if getattr(self, 'parto_id', None):
            try:
                parto_obj = Parto.objects.get(pk=self.parto_id)
            except Parto.DoesNotExist:
                parto_obj = None

        # If there's a provisional parto datetime attached (from combined form), prefer it
        provisional_dt = getattr(self, '_parto_fecha_hora', None)
        if provisional_dt and self.hora_nacimiento:
            # Build datetimes on the same date to compute an accurate seconds delta
            try:
                nacimiento_dt = datetime.combine(provisional_dt.date(), self.hora_nacimiento)
                if provisional_dt.tzinfo is not None:
                    # preserve timezone awareness
                    nacimiento_dt = nacimiento_dt.replace(tzinfo=provisional_dt.tzinfo)
                delta_seconds = abs((nacimiento_dt - provisional_dt).total_seconds())
                logger.info('RecienNacido.clean provisional compare: parto=%s nacimiento=%s delta_seconds=%s',
                            provisional_dt.isoformat(), getattr(nacimiento_dt, 'isoformat', lambda: str(nacimiento_dt))(), delta_seconds)
                if delta_seconds > 5400:  # more than 90 minutes
                    raise ValidationError('La hora de nacimiento no puede diferir en más de 1 hora de la hora del parto.')
            except TypeError:
                # Fallback to previous minutes granularity if types mismatch
                hora_parto = provisional_dt.time()
                minutos_parto = hora_parto.hour * 60 + hora_parto.minute
                minutos_nacimiento = self.hora_nacimiento.hour * 60 + self.hora_nacimiento.minute
                if abs(minutos_nacimiento - minutos_parto) > 60:
                    raise ValidationError('La hora de nacimiento no puede diferir en más de 1 hora de la hora del parto.')

        if parto_obj and self.hora_nacimiento:
            try:
                parto_dt = parto_obj.fecha_hora
                nacimiento_dt = datetime.combine(parto_dt.date(), self.hora_nacimiento)
                if parto_dt.tzinfo is not None:
                    nacimiento_dt = nacimiento_dt.replace(tzinfo=parto_dt.tzinfo)
                delta_seconds = abs((nacimiento_dt - parto_dt).total_seconds())
                logger.info('RecienNacido.clean compare: parto=%s nacimiento=%s delta_seconds=%s',
                            parto_dt.isoformat(), getattr(nacimiento_dt, 'isoformat', lambda: str(nacimiento_dt))(), delta_seconds)
                if delta_seconds > 5400:
                    raise ValidationError('La hora de nacimiento no puede diferir en más de 1 hora de la hora del parto.')
            except TypeError:
                hora_parto = parto_obj.fecha_hora.time()
                # Convertir a minutos para comparar
                minutos_parto = hora_parto.hour * 60 + hora_parto.minute
                minutos_nacimiento = self.hora_nacimiento.hour * 60 + self.hora_nacimiento.minute
                if abs(minutos_nacimiento - minutos_parto) > 60:
                    raise ValidationError('La hora de nacimiento no puede diferir en más de 1 hora de la hora del parto.')

        # Validar peso según edad gestacional
        # Preferir semanas desde el objeto parto si existe, sino usar la provisional adjuntada por el formulario combinado
        semanas = None
        if parto_obj and getattr(parto_obj, 'semanas_gestacion', None) is not None:
            semanas = parto_obj.semanas_gestacion
        else:
            semanas = getattr(self, '_parto_semanas', None)

        if self.peso and semanas:
            peso_min = 0.3  # 300g
            if semanas >= 37:  # A término
                if self.peso < 2.0:  # 2000g
                    raise ValidationError('El peso es muy bajo para un bebé a término.')
                if self.peso > 5.0:  # 5000g
                    raise ValidationError('El peso es muy alto, por favor verificar.')
            else:  # Pretérmino
                if self.peso < peso_min:
                    raise ValidationError(f'El peso no puede ser menor a {peso_min}kg.')
                if self.peso > 4.0:  # 4000g
                    raise ValidationError('El peso es muy alto para un bebé pretérmino.')

        # Validar talla
        if self.talla:
            if self.talla < 25:  # 25cm
                raise ValidationError('La talla es muy baja, por favor verificar.')
            if self.talla > 60:  # 60cm
                raise ValidationError('La talla es muy alta, por favor verificar.')

        # Validar APGAR
        if self.apgar_1 is not None and self.apgar_5 is not None:
            if self.apgar_5 < self.apgar_1:
                raise ValidationError('El APGAR a los 5 minutos no puede ser menor que el APGAR al minuto.')
            if self.apgar_1 == 0 and self.estado == 'vivo':
                raise ValidationError('Un APGAR de 0 al minuto no es compatible con estado "vivo".')

    def save(self, *args, **kwargs):
        # Calcular riesgo basado en APGAR
        if self.apgar_1 is not None:
            if self.apgar_1 <= 3:
                self.riesgo = 'alto'
            elif self.apgar_1 <= 6:
                self.riesgo = 'medio'
            else:
                self.riesgo = 'bajo'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"RN de {self.parto.madre} - {self.hora_nacimiento}"

    class Meta:
        verbose_name = "Recién Nacido"
        verbose_name_plural = "Recién Nacidos"

class SesionUsuario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    
    def __str__(self):
        return f"Sesión de {self.usuario.username} - {self.fecha_inicio}"

    class Meta:
        verbose_name = "Sesión de Usuario"
        verbose_name_plural = "Sesiones de Usuario"
