# apps/reportes_app/admin.py
"""Administración de reportes."""

from django.contrib import admin
from .models import Reporte


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'formato', 'estado', 'generado_por', 'fecha_solicitud')
    search_fields = ('titulo', 'generado_por__username')
    list_filter = ('tipo', 'formato', 'estado')
    ordering = ('-fecha_solicitud',)
    readonly_fields = ('fecha_solicitud', 'fecha_generacion')
