# apps/auth_app/urls.py
"""
URLs de Autenticación
Login, Logout, Recuperación de contraseña
+ V3.1: Gestión administrativa de usuarios (integrada en auth_app)
"""

from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    # ===== VISTAS BASADAS EN FUNCIONES =====

    # Login
    path('login/', views.login_view, name='login'),

    # Logout
    path('logout/', views.logout_view, name='logout'),

    # Recuperación de contraseña
    path('recuperar-password/', views.recuperar_password_view, name='recuperar_password'),

    # Perfil de usuario (próximamente)
    # path('perfil/', views.perfil_view, name='perfil'),

    # Cambiar contraseña (próximamente)
    # path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),

    # ===== API REST ENDPOINTS =====

    # Login API
    path('api/login/', views.api_login, name='api_login'),

    # Refresh token API
    path('api/refresh/', views.api_refresh_token, name='api_refresh_token'),

    # ===== V3.1: GESTIÓN ADMINISTRATIVA DE USUARIOS =====
    # Solo accesible para superusuarios (decorador @solo_superusuario en cada vista)
    path('usuarios/',                       views.usuarios_lista,            name='usuarios_lista'),
    path('usuarios/crear/',                 views.usuario_crear,             name='usuario_crear'),
    path('usuarios/<uuid:uid>/detalle/',    views.usuario_detalle,           name='usuario_detalle'),
    path('usuarios/<uuid:uid>/editar/',     views.usuario_editar,            name='usuario_editar'),
    path('usuarios/<uuid:uid>/toggle/',     views.usuario_activar_desactivar,name='usuario_toggle'),
    path('usuarios/<uuid:uid>/reset-pwd/',  views.usuario_reset_password,    name='usuario_reset_password'),
]
