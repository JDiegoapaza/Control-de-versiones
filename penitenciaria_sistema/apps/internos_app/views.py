# apps/internos_app/views.py
"""
Vistas para gestión de internos.
Separación: /internos/ → web | /internos/api/ → DRF
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Interno
from .serializers import InternoSerializer
from .services import InternoService


# ── WEB VIEWS ─────────────────────────────────────────────────────────────────

class InternoListWebView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Interno.objects.filter(activo=True)
        q = request.GET.get('q', '')
        estado = request.GET.get('estado', '')
        if q:
            from django.db.models import Q
            qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(cedula__icontains=q))
        if estado:
            qs = qs.filter(estado=estado)
        qs = qs.order_by('apellido', 'nombre')
        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page'))
        return render(request, 'internos/lista.html', {
            'titulo': 'Gestión de Internos',
            'internos': page,
            'q': q,
            'estado_filter': estado,
            'estado_choices': Interno.ESTADO_CHOICES,
            'total': Interno.objects.filter(activo=True).count(),
        })


class InternoCreateWebView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'internos/form.html', {
            'titulo': 'Registrar Nuevo Interno',
            'accion': 'Registrar',
            'estado_choices': Interno.ESTADO_CHOICES,
            'sexo_choices': Interno.SEXO_CHOICES,
        })

    def post(self, request):
        d = request.POST
        try:
            interno = Interno.objects.create(
                nombre=d.get('nombre', '').strip(),
                apellido=d.get('apellido', '').strip(),
                cedula=d.get('cedula', '').strip(),
                fecha_nacimiento=d.get('fecha_nacimiento') or None,
                sexo=d.get('sexo', 'M'),
                estado=d.get('estado', 'procesado'),
                delito=d.get('delito', '').strip(),
                centro_penitenciario=d.get('centro_penitenciario', '').strip(),
                celda=d.get('celda', '').strip(),
                observaciones=d.get('observaciones', '').strip(),
                fecha_liberacion_prevista=d.get('fecha_liberacion_prevista') or None,
            )
            messages.success(request, f'✅ Interno "{interno.nombre_completo()}" registrado correctamente.')
            return redirect('internos:lista')
        except Exception as e:
            messages.error(request, f'❌ Error al registrar: {str(e)}')
            return render(request, 'internos/form.html', {
                'titulo': 'Registrar Nuevo Interno',
                'accion': 'Registrar',
                'estado_choices': Interno.ESTADO_CHOICES,
                'sexo_choices': Interno.SEXO_CHOICES,
                'form_data': d,
            })


class InternoDetailWebView(LoginRequiredMixin, View):
    def get(self, request, pk):
        interno = get_object_or_404(Interno, pk=pk, activo=True)
        return render(request, 'internos/detalle.html', {
            'titulo': f'Interno: {interno.nombre_completo()}',
            'interno': interno,
            'evaluaciones': interno.evaluaciones.filter(activo=True).order_by('-fecha_creacion')[:5],
            'rehabilitaciones': interno.rehabilitaciones.all().order_by('-creado_en')[:5],
            'predicciones': interno.predicciones_ia.all().order_by('-fecha_prediccion')[:3],
        })


class InternoEditWebView(LoginRequiredMixin, View):
    def get(self, request, pk):
        interno = get_object_or_404(Interno, pk=pk, activo=True)
        return render(request, 'internos/form.html', {
            'titulo': f'Editar: {interno.nombre_completo()}',
            'accion': 'Guardar cambios',
            'interno': interno,
            'estado_choices': Interno.ESTADO_CHOICES,
            'sexo_choices': Interno.SEXO_CHOICES,
        })

    def post(self, request, pk):
        interno = get_object_or_404(Interno, pk=pk, activo=True)
        d = request.POST
        try:
            interno.nombre = d.get('nombre', interno.nombre).strip()
            interno.apellido = d.get('apellido', interno.apellido).strip()
            interno.cedula = d.get('cedula', interno.cedula).strip()
            interno.fecha_nacimiento = d.get('fecha_nacimiento') or interno.fecha_nacimiento
            interno.sexo = d.get('sexo', interno.sexo)
            interno.estado = d.get('estado', interno.estado)
            interno.delito = d.get('delito', interno.delito).strip()
            interno.centro_penitenciario = d.get('centro_penitenciario', interno.centro_penitenciario).strip()
            interno.celda = d.get('celda', interno.celda).strip()
            interno.observaciones = d.get('observaciones', interno.observaciones).strip()
            interno.fecha_liberacion_prevista = d.get('fecha_liberacion_prevista') or interno.fecha_liberacion_prevista
            interno.save()
            messages.success(request, f'✅ Datos actualizados correctamente.')
            return redirect('internos:detalle', pk=interno.pk)
        except Exception as e:
            messages.error(request, f'❌ Error al actualizar: {str(e)}')
            return render(request, 'internos/form.html', {
                'titulo': f'Editar: {interno.nombre_completo()}',
                'accion': 'Guardar cambios',
                'interno': interno,
                'estado_choices': Interno.ESTADO_CHOICES,
                'sexo_choices': Interno.SEXO_CHOICES,
            })


class InternoDeleteWebView(LoginRequiredMixin, View):
    def post(self, request, pk):
        interno = get_object_or_404(Interno, pk=pk, activo=True)
        nombre = interno.nombre_completo()
        InternoService.soft_delete(interno)
        messages.success(request, f'✅ Interno "{nombre}" eliminado correctamente.')
        return redirect('internos:lista')


# ── DRF API VIEWS ──────────────────────────────────────────────────────────────

class InternoListCreateView(generics.ListCreateAPIView):
    serializer_class = InternoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'sexo', 'activo', 'centro_penitenciario']
    search_fields = ['nombre', 'apellido', 'cedula', 'delito']
    ordering_fields = ['apellido', 'creado_en', 'estado']
    ordering = ['apellido']

    def get_queryset(self):
        return Interno.objects.filter(activo=True)


class InternoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InternoSerializer
    permission_classes = [IsAuthenticated]
    queryset = Interno.objects.all()

    def perform_destroy(self, instance):
        InternoService.soft_delete(instance)
