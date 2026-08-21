# apps/reportes_app/urls.py
from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # ── Web ──────────────────────────────────────────────────────────────────
    path('',                    views.ReporteListWebView.as_view(),      name='lista'),
    path('nuevo/',              views.ReporteCreateWebView.as_view(),    name='crear'),
    path('<uuid:pk>/',          views.ReporteDetailWebView.as_view(),    name='detalle'),
    path('<uuid:pk>/eliminar/', views.ReporteDeleteView.as_view(),       name='eliminar'),

    # ── Exportaciones ─────────────────────────────────────────────────────────
    path('<uuid:pk>/pdf/',      views.ReporteDownloadPDFView.as_view(),  name='pdf'),
    path('<uuid:pk>/excel/',    views.ReporteDownloadExcelView.as_view(),name='excel'),
    path('<uuid:pk>/csv/',      views.ReporteDownloadCSVView.as_view(),  name='csv'),
    path('<uuid:pk>/json/',     views.ReporteDownloadJSONView.as_view(), name='json'),

    # ── API DRF ───────────────────────────────────────────────────────────────
    path('api/',                views.ReporteListCreateView.as_view(),   name='reporte-list'),
    path('api/<uuid:pk>/',      views.ReporteRetrieveView.as_view(),     name='reporte-detail'),
]
