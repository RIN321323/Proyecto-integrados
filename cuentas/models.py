from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone

class Rol(models.Model):
    nombre = models.CharField(max_length=30, unique=True)  # "usuario", "superusuario"
    def __str__(self): return self.nombre

class Usuario(AbstractUser):
    # username, password, first_name, last_name, email, is_active... ya vienen
    rol = models.ForeignKey(Rol, null=True, blank=True, on_delete=models.SET_NULL)
    run = models.CharField(max_length=12, unique=True, null=True, blank=True, help_text="RUN sin puntos, con guión y dígito verificador")
    telefono = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        db_table = "usuario"  # si quieres que la tabla se llame 'usuario'


class InviteCode(models.Model):
    code = models.CharField(max_length=64, unique=True)
    single_use = models.BooleanField(default=True)
    used = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    used_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(default=timezone.now)
    used_at = models.DateTimeField(null=True, blank=True)
    # New fields for expiry and usage limits
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(null=True, blank=True, help_text='Max number of times this code can be used. Null = unlimited')
    uses_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Invite Code'
        verbose_name_plural = 'Invite Codes'

    def __str__(self):
        return self.code

    def mark_used(self, user=None):
        """Mark code as used: increment uses_count, set used flag when limits reached or single_use."""
        self.uses_count = (self.uses_count or 0) + 1
        if self.single_use:
            self.used = True
        if self.max_uses is not None and self.uses_count >= self.max_uses:
            self.used = True
        self.used_by = user
        self.used_at = timezone.now()
        self.save()

    def reserve(self):
        """Reserve a use slot without setting used_by/used_at (called on initial acceptance).
        This increments uses_count but does not set used_by/used_at.
        """
        self.uses_count = (self.uses_count or 0) + 1
        if self.max_uses is not None and self.uses_count >= self.max_uses:
            self.used = True
        self.save()

    def consume(self, user=None):
        """Finalize consumption: set used_by and used_at and mark used flag if single_use.
        Does NOT increment uses_count (assumes reserve() already did).
        """
        if self.single_use:
            self.used = True
        if self.max_uses is not None and self.uses_count >= self.max_uses:
            self.used = True
        self.used_by = user
        self.used_at = timezone.now()
        self.save()

    def is_valid(self):
        """Return True if the code is currently valid (not expired and under max_uses)."""
        from django.utils import timezone as _tz
        now = _tz.now()
        if self.expires_at and self.expires_at < now:
            return False
        if self.max_uses is not None and self.uses_count >= self.max_uses:
            return False
        if self.single_use and self.used:
            return False
        return True


# atencion
#Si ya tienes tablas usuario y rol en MySQL, usa estos nombres para no romper tu ER. Si son nuevas, Django las crea con migrate.