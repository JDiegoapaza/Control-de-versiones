# apps/reportes_app/services/csv_exporter.py
"""Exportador CSV usando solo stdlib."""

import csv
import io


def export_csv(datos: dict) -> bytes:
    """
    Genera un archivo .csv a partir del dict de datos.
    Devuelve bytes UTF-8 con BOM para compatibilidad con Excel.
    """
    buf = io.StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_ALL)

    # Encabezado del reporte
    writer.writerow([datos.get('titulo', 'Reporte SGEP')])
    writer.writerow([f'Generado: {datos.get("generado", "")}'])
    writer.writerow([])

    # Resumen
    resumen = _build_resumen(datos)
    if resumen:
        writer.writerow(['RESUMEN'])
        for k, v in resumen.items():
            writer.writerow([k, str(v)])
        writer.writerow([])

    # Tabla principal
    filas = datos.get('filas', [])
    if filas:
        # Header
        header_labels = {
            'nombre_completo': 'Nombre Completo', 'cedula': 'Cédula',
            'sexo': 'Sexo', 'estado': 'Estado', 'delito': 'Delito',
            'centro': 'Centro', 'celda': 'Celda', 'ingreso': 'Ingreso',
            'titulo': 'Evaluación', 'interno': 'Interno', 'psicologo': 'Psicólogo',
            'nivel_riesgo': 'Nivel Riesgo', 'calificacion': 'Calificación',
            'fecha': 'Fecha', 'programa': 'Programa', 'tipo': 'Tipo',
            'progreso': 'Progreso', 'inicio': 'Inicio', 'fin_previsto': 'Fin Previsto',
            'evento': 'Evento', 'usuario': 'Usuario', 'ip': 'IP',
            'descripcion': 'Descripción', 'score': 'Score', 'confianza': 'Confianza',
            'modelo': 'Modelo',
        }
        headers = list(filas[0].keys())
        writer.writerow([header_labels.get(h, h.replace('_', ' ').title()) for h in headers])
        for fila in filas:
            writer.writerow([fila.get(h, '') for h in headers])

    # BOM para Excel
    return b'\xef\xbb\xbf' + buf.getvalue().encode('utf-8')


def _build_resumen(datos: dict) -> dict:
    tipo = datos.get('tipo', '')
    r = {}
    if tipo == 'internos':
        r['Total internos activos'] = datos.get('total', 0)
    elif tipo == 'evaluaciones':
        r['Total evaluaciones'] = datos.get('total', 0)
        r['Completadas'] = datos.get('completadas', 0)
        r['Pendientes'] = datos.get('pendientes', 0)
        if datos.get('promedio_riesgo'):
            r['Promedio riesgo (%)'] = datos['promedio_riesgo']
    elif tipo == 'rehabilitacion':
        r['Total asignaciones'] = datos.get('total', 0)
        r['Completados'] = datos.get('completados', 0)
        r['En proceso'] = datos.get('en_proceso', 0)
    elif tipo == 'auditoria':
        r['Total eventos'] = datos.get('total', 0)
        r['Exitosos'] = datos.get('exitosos', 0)
        r['Fallidos'] = datos.get('fallidos', 0)
    elif tipo == 'estadistico':
        r['Internos activos'] = datos.get('internos', 0)
        r['Evaluaciones'] = datos.get('evaluaciones', 0)
        r['Rehabilitaciones'] = datos.get('rehabilitaciones', 0)
        r['Predicciones IA'] = datos.get('predicciones_ia', 0)
    elif tipo == 'ia_predictiva':
        r['Total predicciones'] = datos.get('total', 0)
        r['Score promedio'] = f"{datos.get('avg_score', 0)}%"
        r['Confianza promedio'] = f"{datos.get('avg_confianza', 0)}%"
    return r
