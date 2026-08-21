# apps/rehabilitacion_app/models.py
"""
Modelos para programas de rehabilitación de internos.
Gestiona planes, actividades y seguimiento de progreso.
"""

import uuid
from django.db import models
from django.utils import timezone


class ProgramaRehabilitacion(models.Model):
    """Define un programa o plan de rehabilitación disponible."""

    TIPO_CHOICES = [
        ('educativo', 'Educativo'),
        ('laboral', 'Laboral'),
        ('psicologico', 'Psicológico'),
        ('deportivo', 'Deportivo'),
        ('artistico', 'Artístico'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200, verbose_name='Nombre del programa')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    duracion_dias = models.PositiveIntegerField(default=30, verbose_name='Duración (días)')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'programas_rehabilitacion'
        verbose_name = 'Programa de rehabilitación'
        verbose_name_plural = 'Programas de rehabilitación'
        ordering = ['nombre']

    def __str__(self) -> str:
        return f"{self.nombre} ({self.get_tipo_display()})"


class Rehabilitacion(models.Model):
    """
    Asignación de un interno a un programa de rehabilitación.
    Rastrea el estado y progreso individual.
    """

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('abandonado', 'Abandonado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interno = models.ForeignKey(
        'internos_app.Interno',
        on_delete=models.CASCADE,
        related_name='rehabilitaciones',
        verbose_name='Interno'
    )
    programa = models.ForeignKey(
        ProgramaRehabilitacion,
        on_delete=models.PROTECT,
        related_name='asignaciones',
        null=True, blank=True,
        verbose_name='Programa'
    )
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    progreso = models.FloatField(default=0.0, verbose_name='Progreso (%)')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    fecha_inicio = models.DateField(default=timezone.now, verbose_name='Fecha de inicio')
    fecha_fin_prevista = models.DateField(null=True, blank=True, verbose_name='Fecha fin prevista')
    fecha_fin_real = models.DateField(null=True, blank=True, verbose_name='Fecha fin real')

    # Auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rehabilitaciones'
        verbose_name = 'Rehabilitación'
        verbose_name_plural = 'Rehabilitaciones'
        ordering = ['-creado_en']

    def __str__(self) -> str:
        return f"{self.interno} - {self.get_estado_display()}"
