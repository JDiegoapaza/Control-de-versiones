# apps/evaluaciones_app/models.py
"""
Modelos para evaluaciones psicológicas de internos.
Gestiona el ciclo completo: creación, aplicación y resultados.
"""

import uuid
from django.db import models
from django.utils import timezone


class Evaluacion(models.Model):
    """
    Evaluación psicológica aplicada a un interno.
    """

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    NIVEL_RIESGO_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('critico', 'Crítico'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=255, verbose_name='Título')
    # ForeignKey a Interno - se usa string para evitar import circular
    interno = models.ForeignKey(
        'internos_app.Interno',
        on_delete=models.PROTECT,
        related_name='evaluaciones',
        null=True, blank=True,
        verbose_name='Interno evaluado'
    )
    # ForeignKey al usuario psicólogo
    psicoplogo = models.ForeignKey(
        'auth_app.Usuario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='evaluaciones_realizadas',
        verbose_name='Psicólogo responsable'
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    completada = models.BooleanField(default=False, verbose_name='Completada')
    nivel_riesgo = models.CharField(
        max_length=10, choices=NIVEL_RIESGO_CHOICES, null=True, blank=True, verbose_name='Nivel de riesgo'
    )
    calificacion_riesgo = models.FloatField(null=True, blank=True, verbose_name='Calificación de riesgo (%)')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    resultados = models.JSONField(default=dict, blank=True, verbose_name='Resultados')

    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    fecha_completada = models.DateTimeField(null=True, blank=True, verbose_name='Fecha completada')

    # Soft delete
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'evaluaciones'
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['completada']),
            models.Index(fields=['estado']),
        ]

    def __str__(self) -> str:
        return f"{self.titulo} - {self.get_estado_display()}"

    def completar(self) -> None:
        """Marca la evaluación como completada."""
        self.completada = True
        self.estado = 'completada'
        self.fecha_completada = timezone.now()
        self.save()
