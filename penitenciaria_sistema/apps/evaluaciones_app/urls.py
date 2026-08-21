from django.urls import path
from . import views

app_name = 'evaluaciones'

urlpatterns = [
    path('', views.EvaluacionListWebView.as_view(), name='lista'),
    path('nueva/', views.EvaluacionCreateWebView.as_view(), name='crear'),
    path('<uuid:pk>/', views.EvaluacionDetailWebView.as_view(), name='detalle'),
    path('<uuid:pk>/editar/', views.EvaluacionEditWebView.as_view(), name='editar'),
    path('<uuid:pk>/eliminar/', views.EvaluacionDeleteWebView.as_view(), name='eliminar'),
    # API DRF
    path('api/', views.EvaluacionListCreateView.as_view(), name='evaluacion-list'),
    path('api/<uuid:pk>/', views.EvaluacionRetrieveUpdateDestroyView.as_view(), name='evaluacion-detail'),
]
