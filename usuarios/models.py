from django.db import models
from django.conf import settings

class Perfil(models.Model):
    ROLES = (
        ('matrona', 'Matrona'),
        ('usuario', 'Usuario'),
        ('administrador', 'Administrador'),
        ('etc', 'ETC'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario')
    foto = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    # Campo opcional para la foto de perfil

    def __str__(self):
        return f"{self.user.username} - {self.rol}"