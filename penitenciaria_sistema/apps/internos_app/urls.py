# apps/internos_app/urls.py
from django.urls import path
from . import views

app_name = 'internos'

urlpatterns = [
    # ── WEB ──
    path('', views.InternoListWebView.as_view(), name='lista'),
    path('nuevo/', views.InternoCreateWebView.as_view(), name='crear'),
    path('<uuid:pk>/', views.InternoDetailWebView.as_view(), name='detalle'),
    path('<uuid:pk>/editar/', views.InternoEditWebView.as_view(), name='editar'),
    path('<uuid:pk>/eliminar/', views.InternoDeleteWebView.as_view(), name='eliminar'),

    # ── API DRF ──
    path('api/', views.InternoListCreateView.as_view(), name='interno-list'),
    path('api/<uuid:pk>/', views.InternoRetrieveUpdateDestroyView.as_view(), name='interno-detail'),
]
