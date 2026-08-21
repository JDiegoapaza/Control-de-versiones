# apps/dashboard_app/admin.py
"""Administración del dashboard."""

from django.contrib import admin
from .models import ConfiguracionDashboard


@admin.register(ConfiguracionDashboard)
class ConfiguracionDashboardAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tema', 'actualizado_en')
    search_fields = ('usuario__username',)
    ordering = ('usuario__username',)
    readonly_fields = ('creado_en', 'actualizado_en')
