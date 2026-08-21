# config/urls.py
"""
Configuración de URLs principales del proyecto.
Centraliza el enrutamiento de todas las aplicaciones.

Rutas principales:
  /            → Home institucional
  /login/      → Login HTML (alias de /auth/login/)
  /logout/     → Logout (alias de /auth/logout/)
  /dashboard/  → Dashboard principal
  /admin/      → Admin Django
  /auth/       → Módulo de autenticación completo
  /api/        → Endpoints REST (JWT)
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView


# ===== NAMESPACES registrados =====
# 'auth'          → apps.auth_app
# 'dashboard'     → apps.dashboard_app
# 'internos'      → apps.internos_app
# 'evaluaciones'  → apps.evaluaciones_app
# 'rehabilitacion'→ apps.rehabilitacion_app
# 'ia'            → apps.ia_app
# 'reportes'      → apps.reportes_app
# 'seguridad'     → apps.seguridad_app


urlpatterns = [

    # ===== RAÍZ — Home institucional =====
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # ===== ADMIN DJANGO =====
    path('admin/', admin.site.urls),

    # ===== ATAJOS DIRECTOS DE AUTENTICACIÓN =====
    # Evitan el error /accounts/login/ 404 y son los que usa LOGIN_URL
    path('login/', include('apps.auth_app.urls_login')),
    path('logout/', include('apps.auth_app.urls_logout')),

    # ===== MÓDULO DE AUTENTICACIÓN COMPLETO =====
    path('auth/', include(('apps.auth_app.urls', 'auth'), namespace='auth')),

    # ===== DASHBOARD =====
    path('dashboard/', include(('apps.dashboard_app.urls', 'dashboard'), namespace='dashboard')),

    # ===== GESTIÓN DE INTERNOS =====
    path('internos/', include(('apps.internos_app.urls', 'internos'), namespace='internos')),

    # ===== EVALUACIONES =====
    path('evaluaciones/', include(('apps.evaluaciones_app.urls', 'evaluaciones'), namespace='evaluaciones')),

    # ===== REHABILITACIÓN =====
    path('rehabilitacion/', include(('apps.rehabilitacion_app.urls', 'rehabilitacion'), namespace='rehabilitacion')),

    # ===== IA =====
    path('ia/', include(('apps.ia_app.urls', 'ia'), namespace='ia')),

    # ===== REPORTES =====
    path('reportes/', include(('apps.reportes_app.urls', 'reportes'), namespace='reportes')),

    # ===== SEGURIDAD =====
    path('seguridad/', include(('apps.seguridad_app.urls', 'seguridad'), namespace='seguridad')),

    # ===== API JWT =====
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# ===== ARCHIVOS ESTÁTICOS Y MEDIA EN DESARROLLO =====
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug Toolbar (solo si está instalado)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns


# ===== MANEJADORES DE ERROR PERSONALIZADOS =====
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
handler403 = 'django.views.defaults.permission_denied'
handler400 = 'django.views.defaults.bad_request'