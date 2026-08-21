# apps/auth_app/admin.py
"""Administración de modelos de autenticación."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol, TokenRefresh, SesionUsuario, IntentofallaloLogin, RecuperacionPassword


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'creado_en')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('activo',)
    ordering = ('nombre',)
    readonly_fields = ('creado_en', 'actualizado_en')


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'activo', 'bloqueado')
    search_fields = ('username', 'email', 'cedula', 'first_name', 'last_name')
    list_filter = ('activo', 'bloqueado', 'rol')
    ordering = ('first_name', 'last_name')
    readonly_fields = ('creado_por', 'ultimo_login', 'ultimo_login_ip', 'fecha_cambio_password')

    fieldsets = UserAdmin.fieldsets + (
        ('Datos adicionales', {
            'fields': ('cedula', 'rol', 'telefono', 'especialidad', 'centro_penitenciario')
        }),
        ('Seguridad', {
            'fields': ('activo', 'bloqueado', 'razon_bloqueo', 'intentos_fallidos',
                       'fecha_desbloqueo', 'debe_cambiar_password', 'ultimo_login_ip')
        }),
    )


@admin.register(TokenRefresh)
class TokenRefreshAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'activo', 'fecha_creacion', 'fecha_expiracion')
    search_fields = ('usuario__username',)
    list_filter = ('activo',)
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion',)


@admin.register(SesionUsuario)
class SesionUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ip_address', 'dispositivo', 'activa', 'fecha_creacion')
    search_fields = ('usuario__username', 'ip_address')
    list_filter = ('activa',)
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion',)


@admin.register(IntentofallaloLogin)
class IntentoFallidoLoginAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'razon', 'fecha')
    search_fields = ('username', 'ip_address')
    ordering = ('-fecha',)
    readonly_fields = ('fecha',)


@admin.register(RecuperacionPassword)
class RecuperacionPasswordAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'usado', 'fecha_creacion', 'fecha_expiracion')
    search_fields = ('usuario__username',)
    list_filter = ('usado',)
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion',)
