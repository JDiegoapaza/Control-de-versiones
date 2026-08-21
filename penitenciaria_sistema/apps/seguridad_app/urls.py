from django.urls import path
from . import views

app_name = 'seguridad'

urlpatterns = [
    path('', views.LogAuditoriaWebView.as_view(), name='log-list'),
    path('logs/', views.LogAuditoriaListView.as_view(), name='log-api-list'),
    path('configuracion/', views.ConfiguracionSeguridadListView.as_view(), name='config-list'),
]
