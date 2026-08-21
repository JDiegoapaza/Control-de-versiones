# apps/dashboard_app/views.py
"""
Vistas del Dashboard Principal.
Separa vistas HTML (LoginRequiredMixin/login_required)
de APIs REST (JWTAuthentication).
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.http import JsonResponse
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)


def _get_stats_safe():
    """
    Obtiene estadísticas generales del sistema de forma segura.
    Retorna un dict con valores por defecto si algún modelo falla.
    """
    stats = {
        'total_internos': 0,
        'total_evaluaciones': 0,
        'evaluaciones_mes': 0,
        'promedio_riesgo': 'N/A',
        'en_rehabilitacion': 0,
        'internos_por_estado': [],
        'chart_internos_estado': json.dumps({'labels': [], 'data': [], 'backgroundColor': []}),
        'chart_evaluaciones_mes': json.dumps({'labels': [], 'data': [], 'borderColor': '#3b82f6', 'backgroundColor': 'rgba(59,130,246,0.1)'}),
        'ultimas_evaluaciones': [],
        'ultimos_internos': [],
    }

    try:
        from apps.internos_app.models import Interno
        stats['total_internos'] = Interno.objects.filter(activo=True).count()
        internos_por_estado = list(
            Interno.objects.filter(activo=True).values('estado').annotate(cantidad=Count('id'))
        )
        stats['internos_por_estado'] = internos_por_estado
        stats['ultimos_internos'] = Interno.objects.filter(activo=True).order_by('-fecha_registro')[:5]

        # Gráfico de internos por estado
        colores = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
        stats['chart_internos_estado'] = json.dumps({
            'labels': [e.get('estado', 'Desconocido') for e in internos_por_estado],
            'data': [e.get('cantidad', 0) for e in internos_por_estado],
            'backgroundColor': colores[:len(internos_por_estado)],
        })
    except Exception as e:
        logger.warning(f'No se pudo obtener datos de internos: {e}')

    try:
        from apps.evaluaciones_app.models import Evaluacion
        stats['total_evaluaciones'] = Evaluacion.objects.filter(completada=True).count()

        fecha_mes_anterior = timezone.now() - timedelta(days=30)
        stats['evaluaciones_mes'] = Evaluacion.objects.filter(
            fecha_creacion__gte=fecha_mes_anterior,
            completada=True
        ).count()

        # Promedio real de calificación de riesgo (usando Avg, no Count)
        avg_result = Evaluacion.objects.filter(
            completada=True,
            calificacion_riesgo__isnull=False
        ).aggregate(promedio=Avg('calificacion_riesgo'))
        promedio = avg_result.get('promedio')
        stats['promedio_riesgo'] = f"{promedio:.1f}%" if promedio is not None else 'N/A'

        # Últimas evaluaciones
        stats['ultimas_evaluaciones'] = Evaluacion.objects.filter(
            completada=True
        ).select_related('interno', 'psicoplogo').order_by('-fecha_creacion')[:5]

        # Gráfico evaluaciones por mes (últimos 6 meses)
        evaluaciones_meses = []
        labels_meses = []
        for i in range(6, 0, -1):
            f_inicio = timezone.now() - timedelta(days=i * 30)
            f_fin = timezone.now() - timedelta(days=(i - 1) * 30)
            cnt = Evaluacion.objects.filter(
                fecha_creacion__range=[f_inicio, f_fin],
                completada=True
            ).count()
            evaluaciones_meses.append(cnt)
            labels_meses.append(f_inicio.strftime('%b %Y'))
        stats['chart_evaluaciones_mes'] = json.dumps({
            'labels': labels_meses,
            'data': evaluaciones_meses,
            'borderColor': '#3b82f6',
            'backgroundColor': 'rgba(59,130,246,0.1)',
        })
    except Exception as e:
        logger.warning(f'No se pudo obtener datos de evaluaciones: {e}')

    try:
        from apps.rehabilitacion_app.models import Rehabilitacion
        stats['en_rehabilitacion'] = Rehabilitacion.objects.filter(estado='en_proceso').count()
    except Exception as e:
        logger.warning(f'No se pudo obtener datos de rehabilitación: {e}')

    return stats


@login_required(login_url='/login/')
def dashboard_view(request):
    """
    Vista principal del dashboard.
    Protegida con @login_required → redirige a /login/ si no hay sesión.
    Muestra estadísticas adaptadas al rol del usuario.
    """
    usuario = request.user
    stats = _get_stats_safe()

    ia_stats = _get_ia_stats()
    contexto = {
        'titulo': 'Dashboard',
        'subtitulo': 'Panel de Control',
        'fecha_actual': timezone.now(),
        **stats,
        **ia_stats,
    }

    # ===== ESTADÍSTICAS POR ROL =====
    if hasattr(usuario, 'rol') and usuario.rol:
        rol_nombre = usuario.rol.nombre

        if rol_nombre == 'administrador':
            try:
                from apps.auth_app.models import Usuario as UsuarioModel
                contexto['total_usuarios'] = UsuarioModel.objects.filter(activo=True).count()
            except Exception:
                contexto['total_usuarios'] = 0

            try:
                from apps.seguridad_app.models import LogAuditoria
                hace_24h = timezone.now() - timedelta(hours=24)
                contexto['intentos_fallidos_24h'] = LogAuditoria.objects.filter(
                    tipo_evento='LOGIN_FALLIDO',
                    fecha__gte=hace_24h
                ).count()
            except Exception:
                contexto['intentos_fallidos_24h'] = 0

        elif rol_nombre == 'psicologo':
            try:
                from apps.evaluaciones_app.models import Evaluacion
                contexto['mis_evaluaciones'] = Evaluacion.objects.filter(
                    psicoplogo=usuario, completada=True
                ).count()
                contexto['evaluaciones_pendientes'] = Evaluacion.objects.filter(
                    psicoplogo=usuario, completada=False
                ).count()
            except Exception:
                contexto['mis_evaluaciones'] = 0
                contexto['evaluaciones_pendientes'] = 0

            try:
                from apps.internos_app.models import Interno
                contexto['mis_pacientes'] = Interno.objects.filter(
                    evaluaciones__psicoplogo=usuario
                ).distinct().count()
            except Exception:
                contexto['mis_pacientes'] = 0

    # Logs recientes del usuario autenticado
    try:
        from apps.seguridad_app.models import LogAuditoria
        contexto['logs_recientes'] = LogAuditoria.objects.filter(
            usuario=usuario
        ).order_by('-fecha')[:10]
    except Exception:
        contexto['logs_recientes'] = []

    return render(request, 'dashboard/index.html', contexto)


@login_required(login_url='/login/')
def estadisticas_ajax(request):
    """
    Endpoint AJAX para estadísticas en tiempo real.
    Retorna JSON con datos actualizados para actualización sin recarga.
    """
    tipo = request.GET.get('tipo', 'general')
    datos = {}

    if tipo == 'internos':
        try:
            from apps.internos_app.models import Interno
            datos = {
                'total': Interno.objects.filter(activo=True).count(),
                'estados': list(
                    Interno.objects.filter(activo=True).values('estado').annotate(cantidad=Count('id'))
                ),
            }
        except Exception as e:
            datos = {'error': str(e)}

    elif tipo == 'evaluaciones':
        try:
            from apps.evaluaciones_app.models import Evaluacion
            datos = {
                'total': Evaluacion.objects.filter(completada=True).count(),
                'este_mes': Evaluacion.objects.filter(
                    fecha_creacion__gte=timezone.now() - timedelta(days=30),
                    completada=True
                ).count(),
                'pendientes': Evaluacion.objects.filter(completada=False).count(),
            }
        except Exception as e:
            datos = {'error': str(e)}

    elif tipo == 'seguridad':
        try:
            from apps.seguridad_app.models import LogAuditoria
            from apps.auth_app.models import Usuario as UsuarioModel
            hace_24h = timezone.now() - timedelta(hours=24)
            datos = {
                'intentos_fallidos_24h': LogAuditoria.objects.filter(
                    tipo_evento='LOGIN_FALLIDO',
                    fecha__gte=hace_24h
                ).count(),
                'usuarios_activos': UsuarioModel.objects.filter(activo=True).count(),
            }
        except Exception as e:
            datos = {'error': str(e)}

    else:
        try:
            from apps.internos_app.models import Interno
            from apps.evaluaciones_app.models import Evaluacion
            from apps.rehabilitacion_app.models import Rehabilitacion
            from apps.auth_app.models import Usuario as UsuarioModel
            datos = {
                'total_internos': Interno.objects.filter(activo=True).count(),
                'total_evaluaciones': Evaluacion.objects.filter(completada=True).count(),
                'en_rehabilitacion': Rehabilitacion.objects.filter(estado='en_proceso').count(),
                'usuarios_sistema': UsuarioModel.objects.filter(activo=True).count(),
            }
        except Exception as e:
            datos = {'error': str(e)}

    return JsonResponse(datos, safe=False)


def _get_ia_stats():
    """Stats de IA para el dashboard."""
    stats = {'predicciones_total': 0, 'criticos': 0, 'altos': 0}
    try:
        from apps.ia_app.models import PrediccionRiesgo
        stats['predicciones_total'] = PrediccionRiesgo.objects.count()
        stats['criticos'] = PrediccionRiesgo.objects.filter(nivel_riesgo='critico').count()
        stats['altos'] = PrediccionRiesgo.objects.filter(nivel_riesgo='alto').count()
    except Exception:
        pass
    return stats
