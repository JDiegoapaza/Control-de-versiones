# apps/dashboard_app/services.py
"""Servicio de lógica del dashboard."""

from django.utils import timezone
from datetime import timedelta


class DashboardService:
    """Genera estadísticas para el dashboard."""

    @staticmethod
    def get_estadisticas_generales() -> dict:
        """Retorna estadísticas generales del sistema."""
        from apps.internos_app.models import Interno
        from apps.evaluaciones_app.models import Evaluacion
        from apps.rehabilitacion_app.models import Rehabilitacion

        return {
            'total_internos': Interno.objects.filter(activo=True).count(),
            'total_evaluaciones': Evaluacion.objects.filter(completada=True).count(),
            'en_rehabilitacion': Rehabilitacion.objects.filter(estado='en_proceso').count(),
            'evaluaciones_pendientes': Evaluacion.objects.filter(completada=False, activo=True).count(),
        }
