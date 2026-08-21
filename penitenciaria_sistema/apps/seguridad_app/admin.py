# apps/seguridad_app/admin.py
"""Administración de auditoría y seguridad."""

from django.contrib import admin
from .models import LogAuditoria, ConfiguracionSeguridad


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('tipo_evento', 'usuario', 'ip_address', 'estado', 'fecha')
    search_fields = ('usuario__username', 'ip_address', 'descripcion', 'accion')
    list_filter = ('tipo_evento', 'estado')
    ordering = ('-fecha',)
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'


@admin.register(ConfiguracionSeguridad)
class ConfiguracionSeguridadAdmin(admin.ModelAdmin):
    list_display = ('clave', 'valor', 'activo', 'actualizado_en')
    search_fields = ('clave', 'descripcion')
    list_filter = ('activo',)
    ordering = ('clave',)
    readonly_fields = ('creado_en', 'actualizado_en')
