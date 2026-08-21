# apps/seguridad_app/views.py
"""Vistas DRF para auditoría y seguridad."""

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import LogAuditoria, ConfiguracionSeguridad
from .serializers import LogAuditoriaSerializer, ConfiguracionSeguridadSerializer


class LogAuditoriaListView(generics.ListAPIView):
    """Lista de logs de auditoría (solo lectura)."""
    serializer_class = LogAuditoriaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_evento', 'estado']
    search_fields = ['usuario__username', 'ip_address', 'descripcion']
    ordering = ['-fecha']

    def get_queryset(self):
        return LogAuditoria.objects.all().select_related('usuario')


class ConfiguracionSeguridadListView(generics.ListAPIView):
    """Lista de configuraciones de seguridad."""
    queryset = ConfiguracionSeguridad.objects.filter(activo=True)
    serializer_class = ConfiguracionSeguridadSerializer
    permission_classes = [IsAuthenticated]


# ── WEB VIEW para seguridad ────────────────────────────────────────────────────
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.core.paginator import Paginator


class LogAuditoriaWebView(LoginRequiredMixin, View):
    def get(self, request):
        qs = LogAuditoria.objects.all().select_related('usuario').order_by('-fecha')
        paginator = Paginator(qs, 30)
        page = paginator.get_page(request.GET.get('page'))
        return render(request, 'seguridad/logs.html', {
            'titulo': 'Logs de Auditoría',
            'logs': page,
        })
