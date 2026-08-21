# apps/dashboard_app/models.py
"""
Modelos para el dashboard - Configuraciones y widgets personalizables.
"""

import uuid
from django.db import models


class ConfiguracionDashboard(models.Model):
    """
    Configuración personalizada del dashboard por usuario.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField(
        'auth_app.Usuario',
        on_delete=models.CASCADE,
        related_name='configuracion_dashboard',
        verbose_name='Usuario'
    )
    widgets_activos = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Widgets activos'
    )
    tema = models.CharField(max_length=20, default='claro', verbose_name='Tema')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuracion_dashboard'
        verbose_name = 'Configuración de dashboard'
        verbose_name_plural = 'Configuraciones de dashboard'

    def __str__(self) -> str:
        return f"Dashboard de {self.usuario}"
