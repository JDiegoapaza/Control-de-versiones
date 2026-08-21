# apps/auth_app/urls_login.py
"""
Mini-urlconf para el atajo /login/ → redirige a auth:login.
Esto permite que LOGIN_URL = '/login/' funcione correctamente
sin colisionar con el namespace 'auth' de /auth/login/.
"""

from django.urls import path
from . import views

# SIN app_name para evitar colisión de namespace con 'auth'
urlpatterns = [
    path('', views.login_view, name='login_direct'),
]
