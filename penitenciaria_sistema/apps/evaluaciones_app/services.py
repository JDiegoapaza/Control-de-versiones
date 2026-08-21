# apps/evaluaciones_app/services.py
"""
Servicio de lógica de negocio para evaluaciones psicológicas.
"""

from typing import Optional
from django.utils import timezone
from .models import Evaluacion


class EvaluacionService:
    """Encapsula la lógica de negocio para evaluaciones."""

    @staticmethod
    def completar_evaluacion(evaluacion: Evaluacion, resultados: dict) -> Evaluacion:
        """Marca una evaluación como completada con sus resultados."""
        evaluacion.resultados = resultados
        evaluacion.completada = True
        evaluacion.estado = 'completada'
        evaluacion.fecha_completada = timezone.now()
        evaluacion.save()
        return evaluacion

    @staticmethod
    def calcular_nivel_riesgo(score: float) -> str:
        """Calcula el nivel de riesgo en base al score."""
        if score < 0.25:
            return 'bajo'
        elif score < 0.50:
            return 'medio'
        elif score < 0.75:
            return 'alto'
        else:
            return 'critico'

    @staticmethod
    def get_evaluaciones_pendientes(psicologo=None):
        """Retorna evaluaciones pendientes, opcionalmente filtradas por psicólogo."""
        qs = Evaluacion.objects.filter(completada=False, activo=True)
        if psicologo:
            qs = qs.filter(psicoplogo=psicologo)
        return qs
