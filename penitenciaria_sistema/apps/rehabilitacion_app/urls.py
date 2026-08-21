from django.urls import path
from . import views

app_name = 'rehabilitacion'

urlpatterns = [
    # Web
    path('', views.RehabilitacionListWebView.as_view(), name='lista'),
    path('nueva/', views.RehabilitacionCreateWebView.as_view(), name='crear'),
    path('<uuid:pk>/', views.RehabilitacionDetailWebView.as_view(), name='detalle'),
    path('<uuid:pk>/editar/', views.RehabilitacionEditWebView.as_view(), name='editar'),
    path('<uuid:pk>/eliminar/', views.RehabilitacionDeleteWebView.as_view(), name='eliminar'),
    path('programas/', views.ProgramaListWebView.as_view(), name='programas'),
    path('programas/nuevo/', views.ProgramaCreateWebView.as_view(), name='programa_crear'),
    # API DRF
    path('api/programas/', views.ProgramaListCreateView.as_view(), name='programa-list'),
    path('api/programas/<uuid:pk>/', views.ProgramaRetrieveUpdateDestroyView.as_view(), name='programa-detail'),
    path('api/', views.RehabilitacionListCreateView.as_view(), name='rehabilitacion-list'),
    path('api/<uuid:pk>/', views.RehabilitacionRetrieveUpdateDestroyView.as_view(), name='rehabilitacion-detail'),
]
