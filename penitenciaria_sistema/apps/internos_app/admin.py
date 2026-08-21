# apps/internos_app/admin.py
"""Administración de internos del centro penitenciario."""

from django.contrib import admin
from .models import Interno


@admin.register(Interno)
class InternoAdmin(admin.ModelAdmin):
    list_display = ('cedula', 'apellido', 'nombre', 'estado', 'centro_penitenciario', 'celda', 'activo')
    search_fields = ('cedula', 'nombre', 'apellido', 'delito')
    list_filter = ('estado', 'sexo', 'activo', 'centro_penitenciario')
    ordering = ('apellido', 'nombre')
    readonly_fields = ('creado_en', 'actualizado_en', 'fecha_registro')
    date_hierarchy = 'fecha_ingreso'
    fieldsets = (
        ('Datos personales', {
            'fields': ('nombre', 'apellido', 'cedula', 'fecha_nacimiento', 'sexo')
        }),
        ('Estado legal', {
            'fields': ('estado', 'delito', 'fecha_ingreso', 'fecha_liberacion_prevista')
        }),
        ('Ubicación', {
            'fields': ('centro_penitenciario', 'celda')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Auditoría', {
            'fields': ('activo', 'eliminado_en', 'creado_en', 'actualizado_en', 'fecha_registro'),
            'classes': ('collapse',)
        }),
    )
