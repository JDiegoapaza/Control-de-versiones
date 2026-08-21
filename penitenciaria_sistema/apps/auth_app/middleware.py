# apps/auth_app/middleware.py
"""
Middleware de autenticación JWT.
Verifica tokens JWT en cabeceras de peticiones.
"""

import logging

logger = logging.getLogger(__name__)


class JWTAuthMiddleware:
    """
    Middleware ligero para procesamiento de JWT.
    La validación real la hace DRF JWTAuthentication.
    Este middleware puede usarse para lógica adicional (ej: blacklist de tokens).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar token si está presente (sin reemplazar la autenticación de DRF)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            # TODO: Verificar blacklist de tokens revocados si aplica
            # self._verificar_blacklist(token)

        return self.get_response(request)
