# apps/ia_app/models.py
"""
Modelos para el módulo de Inteligencia Artificial.
Gestiona predicciones, modelos entrenados y resultados.
"""

import uuid
from django.db import models
from django.utils import timezone


class PrediccionRiesgo(models.Model):
    """
    Predicción de nivel de riesgo generada por IA para un interno.
    """

    NIVEL_RIESGO_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('critico', 'Crítico'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interno = models.ForeignKey(
        'internos_app.Interno',
        on_delete=models.CASCADE,
        related_name='predicciones_ia',
        verbose_name='Interno'
    )
    nivel_riesgo = models.CharField(max_length=10, choices=NIVEL_RIESGO_CHOICES, verbose_name='Nivel de riesgo')
    score = models.FloatField(verbose_name='Puntuación (0-1)')
    confianza = models.FloatField(default=0.0, verbose_name='Confianza (%)')
    factores = models.JSONField(default=dict, blank=True, verbose_name='Factores determinantes')
    modelo_version = models.CharField(max_length=50, default='v1.0', verbose_name='Versión del modelo')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')

    # Auditoría
    fecha_prediccion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de predicción')
    generado_por = models.ForeignKey(
        'auth_app.Usuario',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='predicciones_generadas',
        verbose_name='Generado por'
    )

    class Meta:
        db_table = 'predicciones_riesgo'
        verbose_name = 'Predicción de riesgo IA'
        verbose_name_plural = 'Predicciones de riesgo IA'
        ordering = ['-fecha_prediccion']

    def __str__(self) -> str:
        return f"Predicción {self.interno} - Riesgo: {self.get_nivel_riesgo_display()} ({self.score:.2f})"
