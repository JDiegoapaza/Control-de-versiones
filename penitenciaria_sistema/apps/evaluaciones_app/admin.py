# apps/evaluaciones_app/admin.py
"""Administración de evaluaciones psicológicas."""

from django.contrib import admin
from .models import Evaluacion


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'interno', 'psicoplogo', 'estado', 'completada', 'nivel_riesgo', 'fecha_creacion')
    search_fields = ('titulo', 'interno__nombre', 'interno__cedula', 'psicoplogo__username')
    list_filter = ('estado', 'completada', 'nivel_riesgo', 'activo')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'fecha_completada')
    date_hierarchy = 'fecha_creacion'
