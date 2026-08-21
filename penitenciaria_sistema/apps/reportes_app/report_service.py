# apps/reportes_app/report_service.py
"""
Servicio principal de reportes — mantiene interfaz pública existente
y delega a la nueva arquitectura services/.
"""

import json
import logging
from django.utils import timezone
from .models import Reporte
from .services.report_generator import generar_datos

logger = logging.getLogger(__name__)


class ReporteService:
    """Fachada pública compatible con código existente."""

    @staticmethod
    def generar_reporte(reporte: Reporte) -> Reporte:
        """
        Genera datos estructurados y los persiste en reporte.resultado (JSON).
        """
        try:
            reporte.estado = 'generando'
            reporte.save(update_fields=['estado'])

            datos = generar_datos(reporte.tipo, reporte.parametros or {})

            reporte.estado = 'completado'
            reporte.fecha_generacion = timezone.now()
            reporte.resultado = json.dumps(datos, ensure_ascii=False, default=str)
            reporte.save()
            return reporte

        except Exception as e:
            logger.error(f'Error generando reporte {reporte.id}: {e}', exc_info=True)
            reporte.estado = 'error'
            reporte.error_mensaje = str(e)
            reporte.save(update_fields=['estado', 'error_mensaje'])
            return reporte
