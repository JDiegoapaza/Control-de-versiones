# apps/evaluaciones_app/views.py
"""
Vistas para evaluaciones psicológicas.
  /evaluaciones/      → interfaz web
  /evaluaciones/api/  → API DRF
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator
from django.utils import timezone

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Evaluacion
from .serializers import EvaluacionSerializer


# ── WEB VIEWS ─────────────────────────────────────────────────────────────────

class EvaluacionListWebView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Evaluacion.objects.filter(activo=True).select_related(
            'interno',
            'psicoplogo'
        )

        q = request.GET.get('q', '')
        estado = request.GET.get('estado', '')
        riesgo = request.GET.get('riesgo', '')

        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(titulo__icontains=q) |
                Q(interno__nombre__icontains=q) |
                Q(interno__cedula__icontains=q)
            )

        if estado:
            qs = qs.filter(estado=estado)

        if riesgo:
            qs = qs.filter(nivel_riesgo=riesgo)

        qs = qs.order_by('-fecha_creacion')

        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page'))

        return render(request, 'evaluaciones/lista.html', {
            'titulo': 'Evaluaciones Psicológicas',
            'evaluaciones': page,
            'q': q,
            'estado_filter': estado,
            'riesgo_filter': riesgo,
            'estado_choices': Evaluacion.ESTADO_CHOICES,
            'riesgo_choices': Evaluacion.NIVEL_RIESGO_CHOICES,
            'total': Evaluacion.objects.filter(activo=True).count(),
        })


class EvaluacionCreateWebView(LoginRequiredMixin, View):

    def get(self, request):
        from apps.internos_app.models import Interno

        internos = Interno.objects.filter(
            activo=True
        ).order_by('apellido')

        return render(request, 'evaluaciones/form.html', {
            'titulo': 'Nueva Evaluación',
            'accion': 'Crear evaluación',
            'internos': internos,
            'estado_choices': Evaluacion.ESTADO_CHOICES,
            'riesgo_choices': Evaluacion.NIVEL_RIESGO_CHOICES,
            'form_data': {},
        })

    def post(self, request):
        d = request.POST

        from apps.internos_app.models import Interno

        try:
            interno_id = d.get('interno')

            interno = (
                Interno.objects.get(pk=interno_id)
                if interno_id else None
            )

            cal = d.get('calificacion_riesgo')

            evaluacion = Evaluacion.objects.create(
                titulo=d.get('titulo', '').strip(),
                interno=interno,
                psicoplogo=request.user,
                estado=d.get('estado', 'pendiente'),
                nivel_riesgo=d.get('nivel_riesgo') or None,
                calificacion_riesgo=float(cal) if cal else None,
                observaciones=d.get('observaciones', '').strip(),
            )

            messages.success(
                request,
                f'✅ Evaluación "{evaluacion.titulo}" creada correctamente.'
            )

            return redirect('evaluaciones:lista')

        except Exception as e:

            internos = Interno.objects.filter(
                activo=True
            ).order_by('apellido')

            messages.error(
                request,
                f'❌ Error al crear evaluación: {str(e)}'
            )

            return render(request, 'evaluaciones/form.html', {
                'titulo': 'Nueva Evaluación',
                'accion': 'Crear evaluación',
                'internos': internos,
                'estado_choices': Evaluacion.ESTADO_CHOICES,
                'riesgo_choices': Evaluacion.NIVEL_RIESGO_CHOICES,
                'form_data': d,
            })


class EvaluacionDetailWebView(LoginRequiredMixin, View):

    def get(self, request, pk):

        ev = get_object_or_404(
            Evaluacion,
            pk=pk,
            activo=True
        )

        return render(request, 'evaluaciones/detalle.html', {
            'titulo': f'Evaluación: {ev.titulo}',
            'evaluacion': ev,
        })


class EvaluacionEditWebView(LoginRequiredMixin, View):

    def get(self, request, pk):

        ev = get_object_or_404(
            Evaluacion,
            pk=pk,
            activo=True
        )

        from apps.internos_app.models import Interno

        internos = Interno.objects.filter(
            activo=True
        ).order_by('apellido')

        return render(request, 'evaluaciones/form.html', {
            'titulo': f'Editar: {ev.titulo}',
            'accion': 'Guardar cambios',
            'evaluacion': ev,
            'internos': internos,
            'estado_choices': Evaluacion.ESTADO_CHOICES,
            'riesgo_choices': Evaluacion.NIVEL_RIESGO_CHOICES,
            'form_data': {},
        })

    def post(self, request, pk):

        ev = get_object_or_404(
            Evaluacion,
            pk=pk,
            activo=True
        )

        d = request.POST

        from apps.internos_app.models import Interno

        try:

            interno_id = d.get('interno')

            if interno_id:
                ev.interno = Interno.objects.get(pk=interno_id)

            ev.titulo = d.get('titulo', ev.titulo).strip()

            ev.estado = d.get('estado', ev.estado)

            ev.nivel_riesgo = (
                d.get('nivel_riesgo') or ev.nivel_riesgo
            )

            cal = d.get('calificacion_riesgo')

            ev.calificacion_riesgo = (
                float(cal)
                if cal else ev.calificacion_riesgo
            )

            ev.observaciones = d.get(
                'observaciones',
                ev.observaciones
            ).strip()

            if ev.estado == 'completada' and not ev.completada:
                ev.completar()
            else:
                ev.save()

            messages.success(
                request,
                '✅ Evaluación actualizada correctamente.'
            )

            return redirect('evaluaciones:detalle', pk=ev.pk)

        except Exception as e:

            messages.error(
                request,
                f'❌ Error: {str(e)}'
            )

            return redirect('evaluaciones:editar', pk=pk)


class EvaluacionDeleteWebView(LoginRequiredMixin, View):

    def post(self, request, pk):

        ev = get_object_or_404(
            Evaluacion,
            pk=pk,
            activo=True
        )

        titulo = ev.titulo

        ev.activo = False
        ev.save()

        messages.success(
            request,
            f'✅ Evaluación "{titulo}" eliminada.'
        )

        return redirect('evaluaciones:lista')


# ── DRF API ────────────────────────────────────────────────────────────────────

class EvaluacionListCreateView(generics.ListCreateAPIView):

    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = [
        'estado',
        'completada',
        'nivel_riesgo',
        'activo'
    ]

    search_fields = [
        'titulo',
        'interno__nombre',
        'interno__cedula'
    ]

    ordering_fields = [
        'fecha_creacion',
        'estado'
    ]

    ordering = ['-fecha_creacion']

    def get_queryset(self):

        return Evaluacion.objects.filter(
            activo=True
        ).select_related(
            'interno',
            'psicoplogo'
        )


class EvaluacionRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Evaluacion.objects.all()