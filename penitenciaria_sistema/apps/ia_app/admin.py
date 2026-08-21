# apps/ia_app/admin.py
"""Administración del módulo de Inteligencia Artificial."""

from django.contrib import admin
from .models import PrediccionRiesgo


@admin.register(PrediccionRiesgo)
class PrediccionRiesgoAdmin(admin.ModelAdmin):
    list_display = ('interno', 'nivel_riesgo', 'score', 'confianza', 'modelo_version', 'fecha_prediccion')
    search_fields = ('interno__nombre', 'interno__cedula')
    list_filter = ('nivel_riesgo', 'modelo_version')
    ordering = ('-fecha_prediccion',)
    readonly_fields = ('fecha_prediccion',)
