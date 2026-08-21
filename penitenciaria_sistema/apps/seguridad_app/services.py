# apps/seguridad_app/services.py
"""Servicio de auditoría y seguridad."""

from .models import LogAuditoria


class AuditoriaService:
    """Servicio para registrar eventos de auditoría."""

    @staticmethod
    def registrar(
        tipo_evento: str,
        descripcion: str = '',
        usuario=None,
        ip_address: str = None,
        user_agent: str = '',
        estado: str = 'EXITOSO',
        datos_adicionales: dict = None,
    ) -> LogAuditoria:
        """Registra un evento de auditoría en la base de datos."""
        return LogAuditoria.objects.create(
            tipo_evento=tipo_evento,
            descripcion=descripcion,
            usuario=usuario,
            ip_address=ip_address,
            user_agent=user_agent,
            estado=estado,
            datos_adicionales=datos_adicionales or {},
        )
