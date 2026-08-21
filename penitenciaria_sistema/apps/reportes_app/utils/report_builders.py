# apps/reportes_app/utils/report_builders.py
"""
Utilidades para construir el contexto de los templates de detalle.
Convierte el dict de datos en estructuras fáciles de usar en Django templates.
"""

import json


def parse_resultado(reporte) -> dict:
    """
    Parsea el campo resultado (JSON) de un Reporte y devuelve un dict.
    Si el campo está vacío o es inválido, devuelve un dict vacío.
    """
    if not reporte.resultado:
        return {}
    try:
        return json.loads(reporte.resultado)
    except (json.JSONDecodeError, TypeError):
        return {}


def build_context_for_template(reporte) -> dict:
    """
    Construye el contexto completo para el template de detalle.
    Siempre devuelve datos frescos regenerando desde la base de datos.
    """
    from apps.reportes_app.services.report_generator import generar_datos
    datos = generar_datos(reporte.tipo, reporte.parametros or {})
    return datos


NIVEL_RIESGO_COLORS = {
    'bajo':    ('success',  '✅'),
    'medio':   ('warning',  '⚠️'),
    'alto':    ('danger',   '🔴'),
    'critico': ('dark',     '🚨'),
}

ESTADO_COLORS = {
    'completado':  'success',
    'en_proceso':  'info',
    'pendiente':   'warning',
    'abandonado':  'danger',
}

EVENTO_ICONS = {
    'LOGIN_EXITOSO':   'bi-box-arrow-in-right text-success',
    'LOGIN_FALLIDO':   'bi-x-circle text-danger',
    'LOGIN_BLOQUEADO': 'bi-shield-x text-danger',
    'LOGOUT':          'bi-box-arrow-right text-secondary',
    'CREAR':           'bi-plus-circle text-primary',
    'EDITAR':          'bi-pencil text-warning',
    'ELIMINAR':        'bi-trash text-danger',
    'VER':             'bi-eye text-info',
    'EXPORTAR':        'bi-download text-primary',
    'ERROR':           'bi-bug text-danger',
}
