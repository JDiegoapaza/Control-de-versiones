# apps/rehabilitacion_app/admin.py
"""Administración de programas de rehabilitación."""

from django.contrib import admin
from .models import ProgramaRehabilitacion, Rehabilitacion


@admin.register(ProgramaRehabilitacion)
class ProgramaRehabilitacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'duracion_dias', 'activo')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('tipo', 'activo')
    ordering = ('nombre',)
    readonly_fields = ('creado_en', 'actualizado_en')


@admin.register(Rehabilitacion)
class RehabilitacionAdmin(admin.ModelAdmin):
    list_display = ('interno', 'programa', 'estado', 'progreso', 'fecha_inicio')
    search_fields = ('interno__nombre', 'interno__cedula')
    list_filter = ('estado',)
    ordering = ('-creado_en',)
    readonly_fields = ('creado_en', 'actualizado_en')
