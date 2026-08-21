from django.urls import path
from . import views

app_name = 'ia'

urlpatterns = [
    # Web
    path('', views.IAListWebView.as_view(), name='lista'),
    path('analizar/', views.IAAnalizarView.as_view(), name='analizar'),
    path('prediccion/<uuid:pk>/', views.IADetalleWebView.as_view(), name='detalle'),
    # API DRF
    path('api/', views.PrediccionRiesgoListCreateView.as_view(), name='prediccion-list'),
    path('api/predicciones/<uuid:pk>/', views.PrediccionRiesgoRetrieveView.as_view(), name='prediccion-detail'),
    path('api/predecir/<uuid:interno_pk>/', views.api_predecir, name='api-predecir'),
]
