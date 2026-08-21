# apps/seguridad_app/middleware.py
"""
Middleware de auditoría y rate limiting.
Registra acciones y controla intentos de acceso.
"""

import logging
from django.utils import timezone
from django.http import JsonResponse

logger = logging.getLogger('apps.seguridad_app')


class AuditoriaMiddleware:
    """
    Middleware que registra peticiones HTTP relevantes para auditoría.
    Solo registra métodos de escritura (POST, PUT, PATCH, DELETE).
    """

    METODOS_AUDITABLES = {'POST', 'PUT', 'PATCH', 'DELETE'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Registrar sólo métodos que modifican datos
        if request.method in self.METODOS_AUDITABLES and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                from apps.seguridad_app.models import LogAuditoria

                # Mapeamos métodos HTTP a TIPO_EVENTO_CHOICES válidos
                metodo_to_evento = {
                    'POST':   'CREAR',
                    'PUT':    'EDITAR',
                    'PATCH':  'EDITAR',
                    'DELETE': 'ELIMINAR',
                }
                tipo_evento = metodo_to_evento.get(request.method, 'EDITAR')

                LogAuditoria.objects.create(
                    usuario=request.user,
                    tipo_evento=tipo_evento,
                    descripcion=f"{request.method} {request.path}",
                    ip_address=self._get_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    estado='EXITOSO' if response.status_code < 400 else 'FALLIDO',
                )
            except Exception as e:
                logger.warning(f"No se pudo registrar auditoría: {e}")

        return response

    @staticmethod
    def _get_ip(request) -> str:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class RateLimitMiddleware:
    """
    Middleware de rate limiting para endpoints de autenticación.
    Placeholder: implementar con django-ratelimit o Redis en producción.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # TODO: Implementar rate limiting real con Redis o django-ratelimit
        return self.get_response(request)
