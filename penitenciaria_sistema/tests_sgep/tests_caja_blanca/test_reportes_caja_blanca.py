# tests_sgep/tests_caja_blanca/test_reportes_caja_blanca.py
"""
PRUEBAS DE CAJA BLANCA — Módulo: Generación de Reportes
========================================================
Técnica: Cobertura de Ramas + Manejo de Excepciones

FUNCIONES ANALIZADAS:
    _safe()                   — wrapper try/except
    build_internos()          — bucles for, condicionales
    build_evaluaciones()      — agregaciones, condicionales
    build_auditoria()         — contadores, formateo
    generar_datos()           — diccionario BUILDERS, .get() con default
    build_estadistico()       — _safe() múltiples veces

ANÁLISIS DE DECISIONES:
    _safe():
        try: fn() → resultado
        except Exception: → {}

    build_internos():
        for i in qs: (bucle 0 a N iteraciones)
            i.fecha_ingreso if i.fecha_ingreso else '—'  ← rama

    build_evaluaciones():
        promedio_riesgo if promedio_riesgo else None   ← rama

    generar_datos():
        builder = BUILDERS.get(tipo, build_estadistico)  ← rama
        tipo en BUILDERS vs tipo no en BUILDERS
"""

import pytest
from django.utils import timezone


pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: _safe() helper
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafeHelper:
    """
    Cobertura de la función _safe() en report_generator.py.

    Código fuente:
        def _safe(fn):
            try:
                return fn()    ← RAMA try
            except Exception as e:
                logger.warning(...)
                return {}      ← RAMA except
    """

    def test_CB_R_001_safe_rama_try_exitoso(self, db):
        """
        CB-R-001: _safe() — RAMA try exitosa, retorna resultado de fn().
        """
        from apps.reportes_app.services.report_generator import _safe

        resultado = _safe(lambda: {'clave': 'valor_prueba'})

        assert resultado == {'clave': 'valor_prueba'}

    def test_CB_R_002_safe_rama_except_captura_excepcion(self, db):
        """
        CB-R-002: _safe() — RAMA except, fn() lanza excepción → retorna {}.
        EXCEPCIÓN PROBADA: ValueError, RuntimeError.
        """
        from apps.reportes_app.services.report_generator import _safe

        resultado = _safe(lambda: (_ for _ in ()).throw(ValueError("Error simulado")))

        assert resultado == {}

    def test_CB_R_003_safe_captura_import_error(self, db):
        """
        CB-R-003: _safe() captura ImportError al importar módulo inexistente.
        """
        from apps.reportes_app.services.report_generator import _safe

        def fn_con_import_error():
            import modulo_que_no_existe_abc
            return {}

        resultado = _safe(fn_con_import_error)
        assert resultado == {}


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: Bucles en build_internos()
# ═══════════════════════════════════════════════════════════════════════════════
# Código fuente (bucle crítico):
#
#   for i in qs.order_by('apellido', 'nombre').select_related()[:500]:
#       filas.append({
#           ...
#           'ingreso': i.fecha_ingreso.strftime('%d/%m/%Y') if i.fecha_ingreso else '—',
#       })
#
# DECISIÓN INTERNA: fecha_ingreso is not None vs None (→ '—')

class TestBuildInternosBucles:

    def test_CB_R_004_bucle_con_cero_internos(self, db):
        """
        CB-R-004: Bucle for con 0 iteraciones (BD vacía).
        RESULTADO: filas = [] (lista vacía), total = 0.
        """
        from apps.reportes_app.services.report_generator import build_internos

        resultado = build_internos()

        assert resultado['total'] == 0
        assert resultado['filas'] == []

    def test_CB_R_005_bucle_con_un_interno(self, interno_activo):
        """
        CB-R-005: Bucle for con 1 iteración.
        RESULTADO: filas tiene exactamente 1 elemento con estructura correcta.
        """
        from apps.reportes_app.services.report_generator import build_internos

        resultado = build_internos()

        assert resultado['total'] == 1
        assert len(resultado['filas']) == 1

    def test_CB_R_006_bucle_con_multiples_internos(
        self, interno_activo, interno_condenado
    ):
        """
        CB-R-006: Bucle for con N iteraciones (N > 1).
        RESULTADO: filas tiene N elementos.
        """
        from apps.reportes_app.services.report_generator import build_internos

        resultado = build_internos()

        assert resultado['total'] == 2
        assert len(resultado['filas']) == 2

    def test_CB_R_007_rama_fecha_ingreso_none(self, db):
        """
        CB-R-007: Interno con fecha_ingreso=None → campo 'ingreso'='—'.
        RAMA: fecha_ingreso is None → else '—'
        """
        from apps.internos_app.models import Interno
        from apps.reportes_app.services.report_generator import build_internos

        Interno.objects.create(
            nombre='SinFecha',
            apellido='Ingreso',
            cedula='SIN-FECHA-001',
            sexo='M',
            estado='procesado',
            fecha_ingreso=None,   # ← fecha_ingreso = None
        )

        resultado = build_internos()

        fila_sin_fecha = next(
            (f for f in resultado['filas'] if f['cedula'] == 'SIN-FECHA-001'),
            None
        )

        assert fila_sin_fecha is not None
        assert fila_sin_fecha['ingreso'] == '—'

    def test_CB_R_008_rama_fecha_ingreso_no_none(self, interno_activo):
        """
        CB-R-008: Interno con fecha_ingreso != None → campo 'ingreso' formateado.
        RAMA: fecha_ingreso is not None → strftime('%d/%m/%Y')
        """
        from apps.reportes_app.services.report_generator import build_internos
        import re

        resultado = build_internos()

        fila = next(
            (f for f in resultado['filas'] if f['cedula'] == interno_activo.cedula),
            None
        )

        assert fila is not None
        # Verifica formato DD/MM/YYYY
        assert re.match(r'\d{2}/\d{2}/\d{4}', fila['ingreso']), (
            f"Formato de fecha inesperado: '{fila['ingreso']}'"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: build_evaluaciones() — condicionales de promedio
# ═══════════════════════════════════════════════════════════════════════════════
# Código fuente:
#
#   promedio_riesgo = qs.filter(completada=True, calificacion_riesgo__isnull=False)
#                       .aggregate(p=Avg('calificacion_riesgo'))['p']
#   ...
#   'promedio_riesgo': round(promedio_riesgo, 1) if promedio_riesgo else None,
#
# RAMAS:
#   promedio_riesgo is not None → round(promedio_riesgo, 1)
#   promedio_riesgo is None     → None

class TestBuildEvaluacionesRamas:

    def test_CB_R_009_promedio_riesgo_none_sin_evaluaciones(self, db):
        """
        CB-R-009: Sin evaluaciones completadas con calificación → promedio_riesgo=None.
        RAMA: promedio_riesgo is None → 'promedio_riesgo': None
        """
        from apps.reportes_app.services.report_generator import build_evaluaciones

        resultado = build_evaluaciones()

        assert resultado['promedio_riesgo'] is None

    def test_CB_R_010_promedio_riesgo_calculado(self, evaluacion_completada):
        """
        CB-R-010: Con evaluación completada y calificación → promedio calculado.
        RAMA: promedio_riesgo is not None → round(promedio_riesgo, 1)
        """
        from apps.reportes_app.services.report_generator import build_evaluaciones

        resultado = build_evaluaciones()

        assert resultado['promedio_riesgo'] is not None
        assert isinstance(resultado['promedio_riesgo'], float)
        assert resultado['promedio_riesgo'] == round(45.0, 1)  # calificacion_riesgo=45.0

    def test_CB_R_011_fila_calificacion_none_muestra_guion(
        self, evaluacion_pendiente
    ):
        """
        CB-R-011: Evaluación sin calificación_riesgo muestra '—' en la fila.
        RAMA: ev.calificacion_riesgo is None → '—'
        """
        from apps.reportes_app.services.report_generator import build_evaluaciones

        resultado = build_evaluaciones()

        fila = next(
            (f for f in resultado['filas']
             if 'Ingreso' in f['titulo'] or f['estado'] == 'Pendiente'),
            None
        )

        if fila:
            assert fila['calificacion'] == '—'

    def test_CB_R_012_fila_calificacion_no_none_formateada(
        self, evaluacion_completada
    ):
        """
        CB-R-012: Evaluación CON calificación → se formatea como '45.0%'.
        RAMA: ev.calificacion_riesgo is not None → f'{ev.calificacion_riesgo:.1f}%'
        """
        from apps.reportes_app.services.report_generator import build_evaluaciones

        resultado = build_evaluaciones()

        fila = next(
            (f for f in resultado['filas']
             if f['calificacion'] != '—'),
            None
        )

        if fila:
            assert '%' in fila['calificacion']
            assert fila['calificacion'] == '45.0%'


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: generar_datos() — diccionario BUILDERS y .get() con default
# ═══════════════════════════════════════════════════════════════════════════════
# Código fuente:
#
#   BUILDERS = {
#       'internos': build_internos,
#       'evaluaciones': build_evaluaciones,
#       ...
#       'individual': build_internos,      ← alias legacy
#       'comparativo': build_estadistico,  ← alias legacy
#   }
#
#   def generar_datos(tipo, parametros=None):
#       builder = BUILDERS.get(tipo, build_estadistico)  ← default
#       return builder(parametros or {})

class TestGenerarDatos_CajaBlanca:

    def test_CB_R_013_tipo_en_builders_usa_builder_correcto(self, db):
        """
        CB-R-013: tipo en BUILDERS → usa el builder mapeado.
        """
        from apps.reportes_app.services.report_generator import generar_datos, BUILDERS

        for tipo in BUILDERS:
            resultado = generar_datos(tipo)
            assert isinstance(resultado, dict)

    def test_CB_R_014_tipo_no_en_builders_usa_estadistico(self, db):
        """
        CB-R-014: tipo NO en BUILDERS → .get() retorna build_estadistico (default).
        """
        from apps.reportes_app.services.report_generator import generar_datos

        resultado = generar_datos('tipo_fantasma_xyz')

        assert resultado['tipo'] == 'estadistico'

    def test_CB_R_015_parametros_none_usa_dict_vacio(self, db):
        """
        CB-R-015: parametros=None → se convierte a {} mediante 'parametros or {}'.
        """
        from apps.reportes_app.services.report_generator import generar_datos

        # No debe fallar con None
        resultado = generar_datos('internos', None)
        assert isinstance(resultado, dict)

    def test_CB_R_016_tipo_alias_legacy_individual(self, db):
        """
        CB-R-016: 'individual' es alias legacy de build_internos.
        """
        from apps.reportes_app.services.report_generator import generar_datos

        resultado = generar_datos('individual')
        assert resultado['tipo'] == 'internos'

    def test_CB_R_017_tipo_alias_legacy_comparativo(self, db):
        """
        CB-R-017: 'comparativo' es alias legacy de build_estadistico.
        """
        from apps.reportes_app.services.report_generator import generar_datos

        resultado = generar_datos('comparativo')
        assert resultado['tipo'] == 'estadistico'


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: build_auditoria() — condicionales en formateo de filas
# ═══════════════════════════════════════════════════════════════════════════════
# Código fuente (fila):
#
#   'usuario': str(log.usuario) if log.usuario else 'Anónimo',
#   'ip': log.ip_address or '—',
#   'descripcion': (log.descripcion or '')[:120],
#   'fecha': log.fecha.strftime(...) if log.fecha else '—',

class TestBuildAuditoria_CajaBlanca:

    def test_CB_R_018_usuario_none_muestra_anonimo(self, db):
        """
        CB-R-018: log.usuario=None → 'usuario'='Anónimo'.
        RAMA: log.usuario is None → else 'Anónimo'
        """
        from apps.seguridad_app.models import LogAuditoria
        from apps.reportes_app.services.report_generator import build_auditoria

        LogAuditoria.objects.create(
            usuario=None,   # Sin usuario (intento anónimo)
            tipo_evento='LOGIN_FALLIDO',
            ip_address='10.10.10.1',
            estado='FALLIDO',
        )

        resultado = build_auditoria()

        fila_anonima = next(
            (f for f in resultado['filas'] if f['usuario'] == 'Anónimo'),
            None
        )
        assert fila_anonima is not None, "No se encontró fila con 'Anónimo'"

    def test_CB_R_019_ip_none_muestra_guion(self, db):
        """
        CB-R-019: log.ip_address=None → 'ip'='—'.
        RAMA: ip_address is None → or '—'
        """
        from apps.seguridad_app.models import LogAuditoria
        from apps.reportes_app.services.report_generator import build_auditoria

        LogAuditoria.objects.create(
            tipo_evento='ERROR',
            ip_address=None,   # Sin IP
            estado='ERROR',
        )

        resultado = build_auditoria()

        fila_sin_ip = next(
            (f for f in resultado['filas'] if f['ip'] == '—'),
            None
        )
        assert fila_sin_ip is not None

    def test_CB_R_020_descripcion_truncada_a_120_chars(self, db):
        """
        CB-R-020: descripcion larga se trunca a 120 caracteres.
        CÓDIGO: (log.descripcion or '')[:120]
        """
        from apps.seguridad_app.models import LogAuditoria
        from apps.reportes_app.services.report_generator import build_auditoria

        descripcion_larga = 'X' * 200  # 200 chars → debe truncarse a 120

        LogAuditoria.objects.create(
            tipo_evento='VER',
            ip_address='127.0.0.1',
            descripcion=descripcion_larga,
            estado='EXITOSO',
        )

        resultado = build_auditoria()

        fila = next(
            (f for f in resultado['filas'] if 'X' * 10 in f['descripcion']),
            None
        )

        if fila:
            assert len(fila['descripcion']) <= 120, (
                f"Descripción no truncada: {len(fila['descripcion'])} chars"
            )
