# apps/reportes_app/services/pdf_exporter.py
"""
Exportador PDF usando xhtml2pdf (reportlab wrapper).
Si no está disponible, genera un HTML imprimible como fallback.
"""

import io
import logging
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# Mapa tipo → template PDF
PDF_TEMPLATES = {
    'internos':      'reportes/export/internos_pdf.html',
    'evaluaciones':  'reportes/export/evaluaciones_pdf.html',
    'rehabilitacion':'reportes/export/rehabilitacion_pdf.html',
    'auditoria':     'reportes/export/auditoria_pdf.html',
    'estadistico':   'reportes/export/estadistico_pdf.html',
    'ia_predictiva': 'reportes/export/ia_predictiva_pdf.html',
    # legados
    'individual':    'reportes/export/internos_pdf.html',
    'comparativo':   'reportes/export/estadistico_pdf.html',
}


def export_pdf(datos: dict) -> bytes:
    """
    Genera PDF a partir del dict de datos.
    Intenta xhtml2pdf; si no está, devuelve HTML para imprimir.
    """
    tipo = datos.get('tipo', 'estadistico')
    template = PDF_TEMPLATES.get(tipo, 'reportes/export/estadistico_pdf.html')
    html_str = render_to_string(template, {'datos': datos})

    try:
        from xhtml2pdf import pisa
        buf = io.BytesIO()
        pisa_status = pisa.CreatePDF(
            src=html_str,
            dest=buf,
            encoding='utf-8',
        )
        if pisa_status.err:
            logger.warning(f'xhtml2pdf error: {pisa_status.err}; usando HTML fallback')
            return html_str.encode('utf-8')
        return buf.getvalue()

    except ImportError:
        logger.info('xhtml2pdf no instalado; devolviendo HTML para imprimir')
        return html_str.encode('utf-8')
