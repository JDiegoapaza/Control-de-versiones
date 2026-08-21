# apps/rehabilitacion_app/services.py
"""Servicio de lógica de negocio para rehabilitación."""

from .models import Rehabilitacion, ProgramaRehabilitacion


class RehabilitacionService:
    """Encapsula la lógica de negocio para programas de rehabilitación."""

    @staticmethod
    def asignar_programa(interno, programa: ProgramaRehabilitacion) -> Rehabilitacion:
        """Asigna un programa de rehabilitación a un interno."""
        rehabilitacion, created = Rehabilitacion.objects.get_or_create(
            interno=interno,
            programa=programa,
            defaults={'estado': 'pendiente'}
        )
        return rehabilitacion

    @staticmethod
    def actualizar_progreso(rehabilitacion: Rehabilitacion, progreso: float) -> Rehabilitacion:
        """Actualiza el progreso de una rehabilitación."""
        rehabilitacion.progreso = min(100.0, max(0.0, progreso))
        if rehabilitacion.progreso >= 100:
            rehabilitacion.estado = 'completado'
        elif rehabilitacion.progreso > 0:
            rehabilitacion.estado = 'en_proceso'
        rehabilitacion.save()
        return rehabilitacion
