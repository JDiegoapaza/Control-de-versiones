# apps/rehabilitacion_app/views.py
"""
Vistas para rehabilitación.
  /rehabilitacion/      → interfaz web
  /rehabilitacion/api/  → API DRF
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import ProgramaRehabilitacion, Rehabilitacion
from .serializers import ProgramaRehabilitacionSerializer, RehabilitacionSerializer


# ── WEB VIEWS ─────────────────────────────────────────────────────────────────

class RehabilitacionListWebView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Rehabilitacion.objects.all().select_related('interno', 'programa')
        estado = request.GET.get('estado', '')
        if estado:
            qs = qs.filter(estado=estado)
        qs = qs.order_by('-creado_en')
        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page'))
        return render(request, 'rehabilitacion/lista.html', {
            'titulo': 'Programas de Rehabilitación',
            'rehabilitaciones': page,
            'estado_filter': estado,
            'estado_choices': Rehabilitacion.ESTADO_CHOICES,
            'total': Rehabilitacion.objects.count(),
            'programas': ProgramaRehabilitacion.objects.filter(activo=True).count(),
        })


class RehabilitacionCreateWebView(LoginRequiredMixin, View):
    def get(self, request):
        from apps.internos_app.models import Interno
        return render(request, 'rehabilitacion/form.html', {
            'titulo': 'Asignar Programa de Rehabilitación',
            'accion': 'Asignar',
            'internos': Interno.objects.filter(activo=True).order_by('apellido'),
            'programas': ProgramaRehabilitacion.objects.filter(activo=True).order_by('nombre'),
            'estado_choices': Rehabilitacion.ESTADO_CHOICES,
        })

    def post(self, request):
        d = request.POST
        from apps.internos_app.models import Interno
        try:
            interno = Interno.objects.get(pk=d.get('interno'))
            programa_id = d.get('programa')
            programa = ProgramaRehabilitacion.objects.get(pk=programa_id) if programa_id else None
            progreso = d.get('progreso', '0')
            rehab = Rehabilitacion.objects.create(
                interno=interno,
                programa=programa,
                estado=d.get('estado', 'pendiente'),
                progreso=float(progreso) if progreso else 0,
                observaciones=d.get('observaciones', '').strip(),
                fecha_inicio=d.get('fecha_inicio') or None,
                fecha_fin_prevista=d.get('fecha_fin_prevista') or None,
            )
            messages.success(request, f'✅ Rehabilitación asignada correctamente.')
            return redirect('rehabilitacion:lista')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            from apps.internos_app.models import Interno
            return render(request, 'rehabilitacion/form.html', {
                'titulo': 'Asignar Programa de Rehabilitación',
                'accion': 'Asignar',
                'internos': Interno.objects.filter(activo=True).order_by('apellido'),
                'programas': ProgramaRehabilitacion.objects.filter(activo=True),
                'estado_choices': Rehabilitacion.ESTADO_CHOICES,
                'form_data': d,
            })


class RehabilitacionDetailWebView(LoginRequiredMixin, View):
    def get(self, request, pk):
        rehab = get_object_or_404(Rehabilitacion, pk=pk)
        return render(request, 'rehabilitacion/detalle.html', {
            'titulo': 'Detalle de Rehabilitación',
            'rehab': rehab,
        })


class RehabilitacionEditWebView(LoginRequiredMixin, View):
    def get(self, request, pk):
        rehab = get_object_or_404(Rehabilitacion, pk=pk)
        from apps.internos_app.models import Interno
        return render(request, 'rehabilitacion/form.html', {
            'titulo': 'Editar Rehabilitación',
            'accion': 'Guardar cambios',
            'rehab': rehab,
            'internos': Interno.objects.filter(activo=True).order_by('apellido'),
            'programas': ProgramaRehabilitacion.objects.filter(activo=True),
            'estado_choices': Rehabilitacion.ESTADO_CHOICES,
        })

    def post(self, request, pk):
        rehab = get_object_or_404(Rehabilitacion, pk=pk)
        d = request.POST
        try:
            rehab.estado = d.get('estado', rehab.estado)
            progreso = d.get('progreso')
            rehab.progreso = float(progreso) if progreso else rehab.progreso
            rehab.observaciones = d.get('observaciones', rehab.observaciones).strip()
            rehab.fecha_fin_prevista = d.get('fecha_fin_prevista') or rehab.fecha_fin_prevista
            if rehab.estado == 'completado':
                from django.utils import timezone
                rehab.fecha_fin_real = timezone.now().date()
            rehab.save()
            messages.success(request, '✅ Rehabilitación actualizada.')
            return redirect('rehabilitacion:detalle', pk=rehab.pk)
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('rehabilitacion:editar', pk=pk)


class RehabilitacionDeleteWebView(LoginRequiredMixin, View):
    def post(self, request, pk):
        rehab = get_object_or_404(Rehabilitacion, pk=pk)
        rehab.delete()
        messages.success(request, '✅ Registro eliminado.')
        return redirect('rehabilitacion:lista')


# Programas
class ProgramaListWebView(LoginRequiredMixin, View):
    def get(self, request):
        programas = ProgramaRehabilitacion.objects.filter(activo=True).order_by('nombre')
        return render(request, 'rehabilitacion/programas.html', {
            'titulo': 'Programas Disponibles',
            'programas': programas,
        })


class ProgramaCreateWebView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'rehabilitacion/programa_form.html', {
            'titulo': 'Nuevo Programa',
            'accion': 'Crear',
            'tipo_choices': ProgramaRehabilitacion.TIPO_CHOICES,
        })

    def post(self, request):
        d = request.POST
        try:
            ProgramaRehabilitacion.objects.create(
                nombre=d.get('nombre', '').strip(),
                tipo=d.get('tipo', 'educativo'),
                descripcion=d.get('descripcion', '').strip(),
                duracion_dias=int(d.get('duracion_dias', 30)),
            )
            messages.success(request, '✅ Programa creado correctamente.')
            return redirect('rehabilitacion:programas')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('rehabilitacion:programa_crear')


# ── DRF API ────────────────────────────────────────────────────────────────────

class ProgramaListCreateView(generics.ListCreateAPIView):
    queryset = ProgramaRehabilitacion.objects.filter(activo=True)
    serializer_class = ProgramaRehabilitacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['tipo', 'activo']
    search_fields = ['nombre']


class ProgramaRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProgramaRehabilitacion.objects.all()
    serializer_class = ProgramaRehabilitacionSerializer
    permission_classes = [IsAuthenticated]


class RehabilitacionListCreateView(generics.ListCreateAPIView):
    serializer_class = RehabilitacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['estado']
    ordering = ['-creado_en']

    def get_queryset(self):
        return Rehabilitacion.objects.all().select_related('interno', 'programa')


class RehabilitacionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rehabilitacion.objects.all()
    serializer_class = RehabilitacionSerializer
    permission_classes = [IsAuthenticated]
