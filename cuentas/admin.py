from django.contrib import admin
from .models import Usuario, Rol
from .models import InviteCode

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("username", "rol", "is_active", "is_staff")

admin.site.register(Rol)

@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'single_use', 'used', 'uses_count', 'max_uses', 'expires_at', 'created_by', 'used_by', 'created_at', 'used_at')
    readonly_fields = ('created_at', 'used_at', 'used_by', 'uses_count')
    search_fields = ('code',)
    list_filter = ('single_use','used')
