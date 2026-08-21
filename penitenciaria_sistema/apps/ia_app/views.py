# apps/ia_app/views.py
"""
Vistas para el módulo de IA.
  /ia/      → interfaz web
  /ia/api/  → API DRF
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import PrediccionRiesgo
from .serializers import PrediccionRiesgoSerializer
from .services import IAService


NIVEL_COLORES = {
    'bajo': 'success',
    'medio': 'warning',
    'alto': 'danger',
    'critico': 'dark',
}


# ── WEB VIEWS ─────────────────────────────────────────────────────────────────

class IAListWebView(LoginRequiredMixin, View):
    def get(self, request):
        qs = PrediccionRiesgo.objects.all().select_related('interno', 'generado_por')
        nivel = request.GET.get('nivel', '')
        if nivel:
            qs = qs.filter(nivel_riesgo=nivel)
        qs = qs.order_by('-fecha_prediccion')
        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page'))

        from apps.internos_app.models import Interno
        from django.db.models import Count
        stats = {
            'total': PrediccionRiesgo.objects.count(),
            'critico': PrediccionRiesgo.objects.filter(nivel_riesgo='critico').count(),
            'alto': PrediccionRiesgo.objects.filter(nivel_riesgo='alto').count(),
            'medio': PrediccionRiesgo.objects.filter(nivel_riesgo='medio').count(),
            'bajo': PrediccionRiesgo.objects.filter(nivel_riesgo='bajo').count(),
        }

        return render(request, 'ia/lista.html', {
            'titulo': 'Módulo de Inteligencia Artificial',
            'predicciones': page,
            'nivel_filter': nivel,
            'nivel_choices': PrediccionRiesgo.NIVEL_RIESGO_CHOICES,
            'nivel_colores': NIVEL_COLORES,
            'stats': stats,
        })


class IAAnalizarView(LoginRequiredMixin, View):
    """Seleccionar interno para analizar con IA."""

    def get(self, request):
        from apps.internos_app.models import Interno
        internos = Interno.objects.filter(activo=True).order_by('apellido')
        return render(request, 'ia/analizar.html', {
            'titulo': 'Analizar Riesgo con IA',
            'internos': internos,
        })

    def post(self, request):
        from apps.internos_app.models import Interno
        interno_id = request.POST.get('interno')
        if not interno_id:
            messages.error(request, '❌ Debe seleccionar un interno.')
            return redirect('ia:analizar')
        try:
            interno = Interno.objects.get(pk=interno_id, activo=True)
            prediccion = IAService.predecir_riesgo(interno, usuario=request.user)
            messages.success(request, f'✅ Análisis completado: {prediccion.get_nivel_riesgo_display().upper()} (Score: {prediccion.score*100:.1f}/100)')
            return redirect('ia:detalle', pk=prediccion.pk)
        except Exception as e:
            messages.error(request, f'❌ Error al analizar: {str(e)}')
            return redirect('ia:analizar')


class IADetalleWebView(LoginRequiredMixin, View):
    def get(self, request, pk):
        pred = get_object_or_404(PrediccionRiesgo, pk=pk)
        factores = pred.factores or {}
        factores_det = factores.get('factores_determinantes', {})
        recomendaciones = factores.get('recomendaciones', [])
        features = factores.get('features', {})
        score_raw = factores.get('score_raw', pred.score * 100)

        return render(request, 'ia/detalle.html', {
            'titulo': f'Análisis IA: {pred.interno.nombre_completo()}',
            'prediccion': pred,
            'factores_det': factores_det,
            'recomendaciones': recomendaciones,
            'features': features,
            'score_raw': score_raw,
            'nivel_color': NIVEL_COLORES.get(pred.nivel_riesgo, 'secondary'),
        })


# ── DRF API ────────────────────────────────────────────────────────────────────

class PrediccionRiesgoListCreateView(generics.ListCreateAPIView):
    serializer_class = PrediccionRiesgoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['nivel_riesgo', 'modelo_version']
    ordering = ['-fecha_prediccion']

    def get_queryset(self):
        return PrediccionRiesgo.objects.all().select_related('interno', 'generado_por')

    def perform_create(self, serializer):
        serializer.save(generado_por=self.request.user)


class PrediccionRiesgoRetrieveView(generics.RetrieveAPIView):
    queryset = PrediccionRiesgo.objects.all()
    serializer_class = PrediccionRiesgoSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_predecir(request, interno_pk):
    """API endpoint para generar predicción vía POST."""
    from apps.internos_app.models import Interno
    try:
        interno = Interno.objects.get(pk=interno_pk, activo=True)
        pred = IAService.predecir_riesgo(interno, usuario=request.user)
        return Response(PrediccionRiesgoSerializer(pred).data)
    except Interno.DoesNotExist:
        return Response({'error': 'Interno no encontrado'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
