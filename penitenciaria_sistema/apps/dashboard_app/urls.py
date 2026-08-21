# apps/dashboard_app/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('estadisticas/', views.estadisticas_ajax, name='estadisticas'),
]
