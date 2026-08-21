# apps/internos_app/services.py
"""
Servicio de lógica de negocio para internos.
Separa la lógica de las vistas (principio de capas).
"""

from typing import Optional
from django.utils import timezone
from .models import Interno


class InternoService:
    """Encapsula la lógica de negocio para la gestión de internos."""

    @staticmethod
    def soft_delete(interno: Interno) -> None:
        """Elimina lógicamente un interno."""
        interno.activo = False
        interno.eliminado_en = timezone.now()
        interno.save(update_fields=['activo', 'eliminado_en'])

    @staticmethod
    def buscar_por_cedula(cedula: str) -> Optional[Interno]:
        """Busca un interno por número de cédula."""
        try:
            return Interno.objects.get(cedula=cedula, activo=True)
        except Interno.DoesNotExist:
            return None

    @staticmethod
    def get_internos_activos():
        """Retorna queryset de internos activos."""
        return Interno.objects.filter(activo=True)

    @staticmethod
    def cambiar_estado(interno: Interno, nuevo_estado: str) -> Interno:
        """Cambia el estado de un interno."""
        estados_validos = [c[0] for c in Interno.ESTADO_CHOICES]
        if nuevo_estado not in estados_validos:
            raise ValueError(f"Estado inválido: {nuevo_estado}")
        interno.estado = nuevo_estado
        interno.save(update_fields=['estado', 'actualizado_en'])
        return interno
