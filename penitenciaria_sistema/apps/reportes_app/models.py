# apps/reportes_app/models.py
"""
Modelos para generación y gestión de reportes del sistema.
NOTA: Se agregaron tipos nuevos a TIPO_CHOICES (compatibles con max_length=20 existente).
      NO se requiere migración porque solo se agregan opciones al CharField.
"""

import uuid
from django.db import models
from django.utils import timezone


class Reporte(models.Model):

    TIPO_CHOICES = [
        # Tipos originales — mantener para compatibilidad
        ('estadistico',   'Estadístico General'),
        ('individual',    'Individual (Internos)'),
        ('comparativo',   'Comparativo'),
        ('auditoria',     'Auditoría de Seguridad'),
        # Tipos nuevos
        ('internos',      'Internos'),
        ('evaluaciones',  'Evaluaciones Psicológicas'),
        ('rehabilitacion','Rehabilitación'),
        ('ia_predictiva', 'IA Predictiva de Riesgo'),
    ]

    FORMATO_CHOICES = [
        ('pdf',   'PDF'),
        ('excel', 'Excel'),
        ('json',  'JSON'),
        ('csv',   'CSV'),
    ]

    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('generando',  'Generando'),
        ('completado', 'Completado'),
        ('error',      'Error'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo         = models.CharField(max_length=200, verbose_name='Título')
    tipo           = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    formato        = models.CharField(max_length=10, choices=FORMATO_CHOICES, default='json',
                                      verbose_name='Formato interno')
    estado         = models.CharField(max_length=20, choices=ESTADO_CHOICES,
                                      default='pendiente', verbose_name='Estado')
    generado_por   = models.ForeignKey(
        'auth_app.Usuario', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reportes',
        verbose_name='Generado por',
    )
    parametros     = models.JSONField(default=dict, blank=True, verbose_name='Parámetros')
    resultado      = models.TextField(blank=True, verbose_name='Datos (JSON interno)')
    error_mensaje  = models.TextField(blank=True, verbose_name='Mensaje de error')
    fecha_solicitud  = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de solicitud')
    fecha_generacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de generación')

    class Meta:
        db_table        = 'reportes'
        verbose_name    = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering        = ['-fecha_solicitud']

    def __str__(self) -> str:
        return f'{self.titulo} ({self.get_tipo_display()}) — {self.get_estado_display()}'

    def get_datos(self) -> dict:
        """
        Devuelve los datos estructurados parseando resultado (JSON).
        Útil para acceso rápido desde templates o API.
        """
        import json
        if not self.resultado:
            return {}
        try:
            return json.loads(self.resultado)
        except (json.JSONDecodeError, TypeError):
            return {}
