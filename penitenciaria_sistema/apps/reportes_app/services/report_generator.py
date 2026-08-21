# apps/reportes_app/services/report_generator.py
"""
Generador central de datos para reportes.
Produce dicts estructurados que los exportadores consumen.
NO toca la capa de presentación.
"""

import logging
from datetime import datetime
from django.utils import timezone
from django.db.models import Count, Avg, Q

logger = logging.getLogger(__name__)


# ── helpers ────────────────────────────────────────────────────────────────────

def _safe(fn):
    """Ejecuta fn() y devuelve su resultado; en error devuelve {}."""
    try:
        return fn()
    except Exception as e:
        logger.warning(f'[ReportGenerator] {fn.__name__}: {e}')
        return {}


# ── builders por tipo ──────────────────────────────────────────────────────────

def build_internos(parametros: dict = None) -> dict:
    """Genera datos completos de internos."""
    from apps.internos_app.models import Interno

    qs = Interno.objects.filter(activo=True)
    total = qs.count()

    por_estado = list(
        qs.values('estado').annotate(n=Count('id')).order_by('-n')
    )
    por_sexo = list(
        qs.values('sexo').annotate(n=Count('id')).order_by('-n')
    )
    por_centro = list(
        qs.values('centro_penitenciario').annotate(n=Count('id')).order_by('-n')[:10]
    )

    filas = []
    for i in qs.order_by('apellido', 'nombre').select_related()[:500]:
        filas.append({
            'nombre_completo': i.nombre_completo(),
            'cedula': i.cedula,
            'sexo': i.get_sexo_display(),
            'estado': i.get_estado_display(),
            'delito': i.delito or '—',
            'centro': i.centro_penitenciario or '—',
            'celda': i.celda or '—',
            'ingreso': i.fecha_ingreso.strftime('%d/%m/%Y') if i.fecha_ingreso else '—',
        })

    return {
        'tipo': 'internos',
        'titulo': 'Reporte de Internos',
        'generado': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'total': total,
        'por_estado': por_estado,
        'por_sexo': por_sexo,
        'por_centro': por_centro,
        'filas': filas,
    }


def build_evaluaciones(parametros: dict = None) -> dict:
    """Genera datos completos de evaluaciones psicológicas."""
    from apps.evaluaciones_app.models import Evaluacion

    qs = Evaluacion.objects.filter(activo=True).select_related('interno', 'psicoplogo')
    total = qs.count()
    completadas = qs.filter(completada=True).count()
    pendientes = qs.filter(estado='pendiente').count()
    en_proceso = qs.filter(estado='en_proceso').count()

    promedio_riesgo = qs.filter(
        completada=True, calificacion_riesgo__isnull=False
    ).aggregate(p=Avg('calificacion_riesgo'))['p']

    por_nivel = list(
        qs.filter(completada=True).exclude(nivel_riesgo=None)
        .values('nivel_riesgo').annotate(n=Count('id')).order_by('-n')
    )

    filas = []
    for ev in qs.order_by('-fecha_creacion')[:500]:
        filas.append({
            'titulo': ev.titulo,
            'interno': ev.interno.nombre_completo() if ev.interno else '—',
            'psicologo': str(ev.psicoplogo) if ev.psicoplogo else '—',
            'estado': ev.get_estado_display(),
            'nivel_riesgo': ev.get_nivel_riesgo_display() if ev.nivel_riesgo else '—',
            'calificacion': f'{ev.calificacion_riesgo:.1f}%' if ev.calificacion_riesgo else '—',
            'fecha': ev.fecha_creacion.strftime('%d/%m/%Y') if ev.fecha_creacion else '—',
        })

    return {
        'tipo': 'evaluaciones',
        'titulo': 'Reporte de Evaluaciones Psicológicas',
        'generado': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'total': total,
        'completadas': completadas,
        'pendientes': pendientes,
        'en_proceso': en_proceso,
        'promedio_riesgo': round(promedio_riesgo, 1) if promedio_riesgo else None,
        'por_nivel': por_nivel,
        'filas': filas,
    }


def build_rehabilitacion(parametros: dict = None) -> dict:
    """Genera datos completos de rehabilitación."""
    from apps.rehabilitacion_app.models import Rehabilitacion, ProgramaRehabilitacion

    qs = Rehabilitacion.objects.all().select_related('interno', 'programa')
    total = qs.count()
    completados = qs.filter(estado='completado').count()
    en_proceso = qs.filter(estado='en_proceso').count()
    abandonados = qs.filter(estado='abandonado').count()
    pendientes = qs.filter(estado='pendiente').count()

    por_programa = list(
        qs.values('programa__nombre').annotate(n=Count('id')).order_by('-n')[:10]
    )
    por_tipo = list(
        qs.values('programa__tipo').annotate(n=Count('id')).order_by('-n')
    )

    avg_progreso = qs.filter(estado='en_proceso').aggregate(p=Avg('progreso'))['p']

    programas = list(
        ProgramaRehabilitacion.objects.filter(activo=True)
        .values('nombre', 'tipo', 'duracion_dias')
        .order_by('nombre')
    )

    filas = []
    for r in qs.order_by('-creado_en')[:500]:
        filas.append({
            'interno': r.interno.nombre_completo() if r.interno else '—',
            'programa': r.programa.nombre if r.programa else '—',
            'tipo': r.programa.get_tipo_display() if r.programa else '—',
            'estado': r.get_estado_display(),
            'progreso': f'{r.progreso:.0f}%',
            'inicio': r.fecha_inicio.strftime('%d/%m/%Y') if r.fecha_inicio else '—',
            'fin_previsto': r.fecha_fin_prevista.strftime('%d/%m/%Y') if r.fecha_fin_prevista else '—',
        })

    return {
        'tipo': 'rehabilitacion',
        'titulo': 'Reporte de Rehabilitación',
        'generado': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'total': total,
        'completados': completados,
        'en_proceso': en_proceso,
        'abandonados': abandonados,
        'pendientes': pendientes,
        'avg_progreso': round(avg_progreso, 1) if avg_progreso else 0,
        'por_programa': por_programa,
        'por_tipo': por_tipo,
        'programas': programas,
        'filas': filas,
    }


def build_auditoria(parametros: dict = None) -> dict:
    """Genera datos de auditoría ISO 27001."""
    from apps.seguridad_app.models import LogAuditoria

    qs = LogAuditoria.objects.all().select_related('usuario').order_by('-fecha')
    total = qs.count()

    exitosos = qs.filter(estado='EXITOSO').count()
    fallidos = qs.filter(estado='FALLIDO').count()
    errores = qs.filter(estado='ERROR').count()

    por_evento = list(
        qs.values('tipo_evento').annotate(n=Count('id')).order_by('-n')[:10]
    )
    por_usuario = list(
        qs.filter(usuario__isnull=False)
        .values('usuario__username').annotate(n=Count('id')).order_by('-n')[:10]
    )

    filas = []
    for log in qs[:200]:
        filas.append({
            'evento': log.tipo_evento,
            'usuario': str(log.usuario) if log.usuario else 'Anónimo',
            'ip': log.ip_address or '—',
            'descripcion': (log.descripcion or '')[:120],
            'estado': log.estado,
            'fecha': log.fecha.strftime('%d/%m/%Y %H:%M') if log.fecha else '—',
        })

    return {
        'tipo': 'auditoria',
        'titulo': 'Reporte de Auditoría de Seguridad',
        'generado': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'total': total,
        'exitosos': exitosos,
        'fallidos': fallidos,
        'errores': errores,
        'por_evento': por_evento,
        'por_usuario': por_usuario,
        'filas': filas,
    }


def build_estadistico(parametros: dict = None) -> dict:
    """Genera resumen estadístico global del sistema."""
    data = {
        'tipo': 'estadistico',
        'titulo': 'Reporte Estadístico General',
        'generado': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    data.update(_safe(lambda: {
        'internos': build_internos().get('total', 0),
        'internos_por_estado': build_internos().get('por_estado', []),
    }))
    data.update(_safe(lambda: {
        'evaluaciones': build_evaluaciones().get('total', 0),
        'evaluaciones_completadas': build_evaluaciones().get('completadas', 0),
        'evaluaciones_por_nivel': build_evaluaciones().get('por_nivel', []),
        'promedio_riesgo': build_evaluaciones().get('promedio_riesgo'),
    }))
    data.update(_safe(lambda: {
        'rehabilitaciones': build_rehabilitacion().get('total', 0),
        'rehabilitaciones_completadas': build_rehabilitacion().get('completados', 0),
    }))
    data.update(_safe(lambda: {
        'predicciones_ia': __import__(
            'apps.ia_app.models', fromlist=['PrediccionRiesgo']
        ).PrediccionRiesgo.objects.count(),
        'ia_por_nivel': list(
            __import__('apps.ia_app.models', fromlist=['PrediccionRiesgo'])
            .PrediccionRiesgo.objects.values('nivel_riesgo')
            .annotate(n=Count('id')).order_by('-n')
        ),
        'criticos': __import__(
            'apps.ia_app.models', fromlist=['PrediccionRiesgo']
        ).PrediccionRiesgo.objects.filter(nivel_riesgo='critico').count(),
    }))
    return data


def build_ia_predictiva(parametros: dict = None) -> dict:
    """Genera reporte de predicciones IA."""
    from apps.ia_app.models import PrediccionRiesgo

    qs = PrediccionRiesgo.objects.all().select_related('interno', 'generado_por')
    total = qs.count()

    por_nivel = list(
        qs.values('nivel_riesgo').annotate(n=Count('id')).order_by('-n')
    )
    avg_confianza = qs.aggregate(p=Avg('confianza'))['p']
    avg_score = qs.aggregate(p=Avg('score'))['p']

    criticos = list(
        qs.filter(nivel_riesgo='critico')
        .select_related('interno')
        .order_by('-fecha_prediccion')[:20]
    )

    filas = []
    for p in qs.order_by('-fecha_prediccion')[:500]:
        filas.append({
            'interno': p.interno.nombre_completo() if p.interno else '—',
            'cedula': p.interno.cedula if p.interno else '—',
            'nivel_riesgo': p.get_nivel_riesgo_display(),
            'score': f'{p.score * 100:.1f}',
            'confianza': f'{p.confianza:.0f}%',
            'modelo': p.modelo_version,
            'fecha': p.fecha_prediccion.strftime('%d/%m/%Y %H:%M') if p.fecha_prediccion else '—',
        })

    criticos_filas = []
    for p in criticos:
        criticos_filas.append({
            'interno': p.interno.nombre_completo() if p.interno else '—',
            'cedula': p.interno.cedula if p.interno else '—',
            'score': f'{p.score * 100:.1f}',
            'confianza': f'{p.confianza:.0f}%',
            'fecha': p.fecha_prediccion.strftime('%d/%m/%Y %H:%M') if p.fecha_prediccion else '—',
        })

    return {
        'tipo': 'ia_predictiva',
        'titulo': 'Reporte de IA Predictiva de Riesgo',
        'generado': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'total': total,
        'por_nivel': por_nivel,
        'avg_confianza': round(avg_confianza, 1) if avg_confianza else 0,
        'avg_score': round((avg_score or 0) * 100, 1),
        'criticos_filas': criticos_filas,
        'filas': filas,
    }


# ── mapa tipo → builder ────────────────────────────────────────────────────────

BUILDERS = {
    'internos': build_internos,
    'evaluaciones': build_evaluaciones,
    'rehabilitacion': build_rehabilitacion,
    'auditoria': build_auditoria,
    'estadistico': build_estadistico,
    'ia_predictiva': build_ia_predictiva,
    # legado
    'individual': build_internos,
    'comparativo': build_estadistico,
}


def generar_datos(tipo: str, parametros: dict = None) -> dict:
    """Punto de entrada principal. Devuelve dict de datos según tipo."""
    builder = BUILDERS.get(tipo, build_estadistico)
    return builder(parametros or {})
