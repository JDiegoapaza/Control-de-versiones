# apps/auth_app/urls_logout.py
"""
Mini-urlconf para el atajo /logout/ → ejecuta logout_view.
"""

from django.urls import path
from . import views

# SIN app_name para evitar colisión de namespace con 'auth'
urlpatterns = [
    path('', views.logout_view, name='logout_direct'),
]
