# apps/reportes_app/views.py
"""
Vistas para el módulo de reportes.
  /reportes/                    → Lista de reportes
  /reportes/nuevo/              → Crear reporte
  /reportes/<pk>/               → Detalle visual (HTML)
  /reportes/<pk>/pdf/           → Descarga PDF
  /reportes/<pk>/excel/         → Descarga Excel
  /reportes/<pk>/csv/           → Descarga CSV
  /reportes/<pk>/json/          → Descarga JSON
  /reportes/api/                → API DRF
  /reportes/api/<pk>/           → API DRF detalle
"""

import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Reporte
from .serializers import ReporteSerializer
from .report_service import ReporteService
from .services.report_generator import generar_datos
from .services.pdf_exporter import export_pdf
from .services.excel_exporter import export_excel
from .services.csv_exporter import export_csv
from .utils.report_builders import (
    build_context_for_template,
    NIVEL_RIESGO_COLORS, ESTADO_COLORS, EVENTO_ICONS,
)

logger = logging.getLogger(__name__)

# Tipos de reporte disponibles (mapa valor → etiqueta)
TIPOS_REPORTE = [
    ('internos',      'Internos'),
    ('evaluaciones',  'Evaluaciones Psicológicas'),
    ('rehabilitacion','Rehabilitación'),
    ('auditoria',     'Auditoría de Seguridad'),
    ('estadistico',   'Estadístico General'),
    ('ia_predictiva', 'IA Predictiva de Riesgo'),
]

# filename pattern por tipo
FILENAMES = {
    'internos':      'reporte_internos',
    'evaluaciones':  'reporte_evaluaciones',
    'rehabilitacion':'reporte_rehabilitacion',
    'auditoria':     'reporte_auditoria',
    'estadistico':   'reporte_estadistico',
    'ia_predictiva': 'reporte_ia_predictiva',
    'individual':    'reporte_internos',
    'comparativo':   'reporte_estadistico',
}


# ── WEB: Lista ─────────────────────────────────────────────────────────────────

class ReporteListWebView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Reporte.objects.filter(generado_por=request.user).order_by('-fecha_solicitud')
        tipo_f = request.GET.get('tipo', '')
        if tipo_f:
            qs = qs.filter(tipo=tipo_f)
        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page'))
        return render(request, 'reportes/lista.html', {
            'titulo': 'Reportes del Sistema',
            'reportes': page,
            'tipos': TIPOS_REPORTE,
            'tipo_filter': tipo_f,
        })


# ── WEB: Crear ─────────────────────────────────────────────────────────────────

class ReporteCreateWebView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'reportes/form.html', {
            'titulo': 'Nuevo Reporte',
            'accion': 'Generar reporte',
            'tipos': TIPOS_REPORTE,
        })

    def post(self, request):
        titulo = request.POST.get('titulo', '').strip()
        tipo   = request.POST.get('tipo', 'estadistico')

        if not titulo:
            messages.error(request, '❌ El título es obligatorio.')
            return render(request, 'reportes/form.html', {
                'titulo': 'Nuevo Reporte',
                'accion': 'Generar reporte',
                'tipos': TIPOS_REPORTE,
                'form_data': request.POST,
            })

        try:
            reporte = Reporte.objects.create(
                titulo=titulo,
                tipo=tipo,
                formato='json',   # interno; exportación se elige en detalle
                generado_por=request.user,
                parametros={},
            )
            ReporteService.generar_reporte(reporte)
            messages.success(request, f'✅ Reporte "{reporte.titulo}" generado correctamente.')
            return redirect('reportes:detalle', pk=reporte.pk)
        except Exception as e:
            logger.error(f'Error creando reporte: {e}', exc_info=True)
            messages.error(request, f'❌ Error al generar reporte: {e}')
            return render(request, 'reportes/form.html', {
                'titulo': 'Nuevo Reporte',
                'accion': 'Generar reporte',
                'tipos': TIPOS_REPORTE,
                'form_data': request.POST,
            })


# ── WEB: Detalle visual ────────────────────────────────────────────────────────

class ReporteDetailWebView(LoginRequiredMixin, View):
    def get(self, request, pk):
        reporte = get_object_or_404(Reporte, pk=pk)

        # Regenerar datos frescos desde la base de datos
        datos = generar_datos(reporte.tipo, reporte.parametros or {})

        return render(request, 'reportes/detalle.html', {
            'titulo': reporte.titulo,
            'reporte': reporte,
            'datos': datos,
            'nivel_colores': NIVEL_RIESGO_COLORS,
            'estado_colores': ESTADO_COLORS,
            'evento_icons': EVENTO_ICONS,
        })


# ── Exportación: PDF ───────────────────────────────────────────────────────────

class ReporteDownloadPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        reporte = get_object_or_404(Reporte, pk=pk)
        datos = generar_datos(reporte.tipo, reporte.parametros or {})
        pdf_bytes = export_pdf(datos)

        filename = FILENAMES.get(reporte.tipo, 'reporte')
        # Detectar si xhtml2pdf devolvió HTML (sin instalar)
        content_type = 'application/pdf'
        ext = 'pdf'
        if pdf_bytes[:5] == b'<!DOC' or pdf_bytes[:4] == b'<htm' or pdf_bytes[:14] == b'<!DOCTYPE html':
            content_type = 'text/html; charset=utf-8'
            ext = 'html'

        resp = HttpResponse(pdf_bytes, content_type=content_type)
        resp['Content-Disposition'] = f'attachment; filename="{filename}.{ext}"'
        return resp


# ── Exportación: Excel ─────────────────────────────────────────────────────────

class ReporteDownloadExcelView(LoginRequiredMixin, View):
    def get(self, request, pk):
        reporte = get_object_or_404(Reporte, pk=pk)
        datos = generar_datos(reporte.tipo, reporte.parametros or {})
        xlsx_bytes = export_excel(datos)

        filename = FILENAMES.get(reporte.tipo, 'reporte')
        # Detect fallback CSV
        if xlsx_bytes[:3] == b'\xef\xbb\xbf' or isinstance(xlsx_bytes, bytes) and b'PK' not in xlsx_bytes[:4]:
            ct = 'text/csv; charset=utf-8-sig'
            ext = 'csv'
        else:
            ct = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ext = 'xlsx'

        resp = HttpResponse(xlsx_bytes, content_type=ct)
        resp['Content-Disposition'] = f'attachment; filename="{filename}.{ext}"'
        return resp


# ── Exportación: CSV ───────────────────────────────────────────────────────────

class ReporteDownloadCSVView(LoginRequiredMixin, View):
    def get(self, request, pk):
        reporte = get_object_or_404(Reporte, pk=pk)
        datos = generar_datos(reporte.tipo, reporte.parametros or {})
        csv_bytes = export_csv(datos)

        filename = FILENAMES.get(reporte.tipo, 'reporte')
        resp = HttpResponse(csv_bytes, content_type='text/csv; charset=utf-8-sig')
        resp['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        return resp


# ── Exportación: JSON ──────────────────────────────────────────────────────────

class ReporteDownloadJSONView(LoginRequiredMixin, View):
    def get(self, request, pk):
        reporte = get_object_or_404(Reporte, pk=pk)
        datos = generar_datos(reporte.tipo, reporte.parametros or {})
        json_bytes = json.dumps(datos, ensure_ascii=False, indent=2, default=str).encode('utf-8')

        filename = FILENAMES.get(reporte.tipo, 'reporte')
        resp = HttpResponse(json_bytes, content_type='application/json; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="{filename}.json"'
        return resp


# ── Eliminar reporte ───────────────────────────────────────────────────────────

class ReporteDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        reporte = get_object_or_404(Reporte, pk=pk, generado_por=request.user)
        titulo = reporte.titulo
        reporte.delete()
        messages.success(request, f'✅ Reporte "{titulo}" eliminado.')
        return redirect('reportes:lista')


# ── DRF API ────────────────────────────────────────────────────────────────────

class ReporteListCreateView(generics.ListCreateAPIView):
    serializer_class = ReporteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'formato', 'estado']
    ordering = ['-fecha_solicitud']

    def get_queryset(self):
        return Reporte.objects.filter(generado_por=self.request.user)

    def perform_create(self, serializer):
        reporte = serializer.save(generado_por=self.request.user)
        ReporteService.generar_reporte(reporte)


class ReporteRetrieveView(generics.RetrieveAPIView):
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer
    permission_classes = [IsAuthenticated]
