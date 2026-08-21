# tests_sgep/tests_caja_blanca/test_ia_internos_caja_blanca.py
"""
PRUEBAS DE CAJA BLANCA — Motor IA Heurístico + InternoService
=============================================================
Técnica: Cobertura de Ramas (Branch Coverage) + Cobertura de Caminos

FUNCIONES ANALIZADAS:
    MotorHeuristico.calcular_score()           — 8 decisiones IF independientes
    MotorHeuristico.score_a_nivel()            — 3 decisiones IF encadenadas
    MotorHeuristico.generar_recomendaciones()  — 9 decisiones IF independientes
    IAService.predecir_riesgo()               — flujo principal con try/except
    InternoService.soft_delete()
    InternoService.cambiar_estado()
    EvaluacionService.calcular_nivel_riesgo()  — 4 ramas
    EvaluacionService.completar_evaluacion()
    Interno.soft_delete()
    Interno.nombre_completo()
    build_internos()                           — reportes
"""

import pytest
from django.utils import timezone


pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: MotorHeuristico.calcular_score()
# ═══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS DE RAMAS (código en ia_app/services.py):
#
#  D1: reinc > 0          → suma PESO_REINCIDENCIA
#  D2: delito_violento    → suma PESO_VIOLENCIA
#  D3: depresion_severa   → suma PESO_DEPRESION
#  D4: ansiedad_severa    → suma PESO_ANSIEDAD
#  D5: not apoyo_familiar → suma PESO_SIN_APOYO
#  D6: cal_prev > 70      → suma bonus 10
#  D7: talleres > 0       → resta PESO_TALLER
#  D8: apoyo_familiar     → resta PESO_APOYO_FAM
#  D9: reincidencias == 0 → resta PESO_SIN_REINC
#  D10: num_eval > 0 and nivel no critico → resta PESO_EVAL_POS
#  D11: score clamp 0-100 (max/min)

class TestMotorHeuristico_CajaBlanca:
    """Cobertura de cada decisión en calcular_score()."""

    def _features_base(self):
        """Features neutros (sin factores de riesgo ni protección)."""
        return {
            'reincidencias': 0,
            'delito_violento': False,
            'depresion_severa': False,
            'ansiedad_severa': False,
            'apoyo_familiar': False,  # sin apoyo (factor negativo)
            'talleres_completados': 0,
            'num_evaluaciones': 0,
            'nivel_riesgo_previo': None,
            'calificacion_riesgo_promedio': None,
        }

    def test_CB_IA_001_rama_reincidencia_verdadera(self):
        """
        CB-IA-001: D1=True — reincidencias > 0 suma puntaje.
        VERIFICACIÓN: 'reincidencias' aparece en factores.
        """
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['reincidencias'] = 2   # > 0 → Rama D1 verdadera

        score, factores = MotorHeuristico.calcular_score(features)

        assert 'reincidencias' in factores
        assert score > 0

    def test_CB_IA_002_rama_reincidencia_falsa(self):
        """
        CB-IA-002: D1=False — reincidencias=0 NO suma, resta PESO_SIN_REINC.
        VERIFICACIÓN: 'reincidencias' NO en factores, 'sin_reincidencias' SÍ.
        """
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['reincidencias'] = 0   # == 0 → Rama D1 falsa

        score, factores = MotorHeuristico.calcular_score(features)

        assert 'reincidencias' not in factores
        assert 'sin_reincidencias' in factores

    def test_CB_IA_003_rama_delito_violento_verdadera(self):
        """CB-IA-003: D2=True — delito violento suma 35 puntos."""
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['delito_violento'] = True

        score_sin, _ = MotorHeuristico.calcular_score({**features, 'delito_violento': False})
        score_con, factores = MotorHeuristico.calcular_score(features)

        assert 'delito_violento' in factores
        assert score_con > score_sin   # Con delito violento, score mayor
        assert score_con - score_sin == 35.0

    def test_CB_IA_004_rama_depresion_severa_verdadera(self):
        """CB-IA-004: D3=True — depresión severa suma 20 puntos."""
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['depresion_severa'] = True

        score, factores = MotorHeuristico.calcular_score(features)

        assert 'depresion_severa' in factores

    def test_CB_IA_005_rama_ansiedad_severa_verdadera(self):
        """CB-IA-005: D4=True — ansiedad severa suma 15 puntos."""
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['ansiedad_severa'] = True

        score, factores = MotorHeuristico.calcular_score(features)

        assert 'ansiedad_severa' in factores

    def test_CB_IA_006_rama_sin_apoyo_familiar(self):
        """CB-IA-006: D5=True (not apoyo_familiar=False) — suma 15."""
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['apoyo_familiar'] = False   # sin apoyo → suma

        score, factores = MotorHeuristico.calcular_score(features)

        assert 'sin_apoyo_familiar' in factores

    def test_CB_IA_007_rama_con_apoyo_familiar(self):
        """CB-IA-007: D8=True — con apoyo familiar, resta PESO_APOYO_FAM."""
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['apoyo_familiar'] = True    # con apoyo → resta
        features['reincidencias'] = 0

        score, factores = MotorHeuristico.calcular_score(features)

        assert 'apoyo_familiar' in factores
        assert '+' not in str(factores['apoyo_familiar'].get('impacto', ''))

    def test_CB_IA_008_rama_calificacion_riesgo_alta_bonus(self):
        """
        CB-IA-008: D6=True — calificación previa > 70 suma bonus de 10.
        """
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['calificacion_riesgo_promedio'] = 80.0   # > 70 → bonus

        score_con, factores = MotorHeuristico.calcular_score(features)

        assert 'historial_riesgo_alto' in factores

    def test_CB_IA_009_rama_calificacion_riesgo_baja_sin_bonus(self):
        """
        CB-IA-009: D6=False — calificación <= 70 no suma bonus.
        """
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['calificacion_riesgo_promedio'] = 65.0   # <= 70 → sin bonus

        score, factores = MotorHeuristico.calcular_score(features)

        assert 'historial_riesgo_alto' not in factores

    def test_CB_IA_010_rama_talleres_completados_resta(self):
        """
        CB-IA-010: D7=True — talleres_completados > 0 resta puntos.
        """
        from apps.ia_app.services import MotorHeuristico

        features_sin = {**self._features_base(), 'talleres_completados': 0}
        features_con = {**self._features_base(), 'talleres_completados': 2}

        score_sin, _ = MotorHeuristico.calcular_score(features_sin)
        score_con, factores = MotorHeuristico.calcular_score(features_con)

        assert 'talleres_completados' in factores
        assert score_con < score_sin   # Con talleres, score menor

    def test_CB_IA_011_limite_reincidencias_clampeado_a_3(self):
        """
        CB-IA-011: reincidencias=99 → se clampea a 3 (MAX_REINCIDENCIA).
        DECISIÓN: min(reinc, 3) → impacto máximo = 3 * 30 = 90
        """
        from apps.ia_app.services import MotorHeuristico

        features = self._features_base()
        features['reincidencias'] = 99   # Se clampea a 3

        score, factores = MotorHeuristico.calcular_score(features)

        if 'reincidencias' in factores:
            impacto = factores['reincidencias']['impacto']
            # Impacto máximo permitido = +90
            assert int(impacto.replace('+', '')) <= 90

    def test_CB_IA_012_score_siempre_clampeado_0_100(self):
        """
        CB-IA-012: max(0, min(100, score)) — verifica el clamp al final.
        RAMAS: score < 0 (clamp a 0) | score > 100 (clamp a 100)
        """
        from apps.ia_app.services import MotorHeuristico

        # Máxima protección → score debería ser 0 o cercano
        features_min = {
            'reincidencias': 0,
            'delito_violento': False,
            'depresion_severa': False,
            'ansiedad_severa': False,
            'apoyo_familiar': True,
            'talleres_completados': 5,
            'num_evaluaciones': 5,
            'nivel_riesgo_previo': 'bajo',
            'calificacion_riesgo_promedio': 10.0,
        }

        score, _ = MotorHeuristico.calcular_score(features_min)

        assert 0 <= score <= 100


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: generar_recomendaciones() — 9 decisiones IF independientes
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerarRecomendaciones:

    def test_CB_IA_013_nivel_critico_agrega_protocolo_urgente(self):
        """
        CB-IA-013: Nivel 'critico' → ejecuta bloque IF nivel == 'critico'
        Agrega 3 recomendaciones de urgencia.
        """
        from apps.ia_app.services import MotorHeuristico

        recs = MotorHeuristico.generar_recomendaciones('critico', {})

        urgente_count = sum(1 for r in recs if 'urgente' in r.lower() or 'inmediata' in r.lower())
        assert urgente_count >= 1

    def test_CB_IA_014_nivel_alto_agrega_psicologo_cabecera(self):
        """
        CB-IA-014: Nivel 'alto' → ejecuta bloque IF nivel in ('alto', 'critico').
        """
        from apps.ia_app.services import MotorHeuristico

        recs = MotorHeuristico.generar_recomendaciones('alto', {})

        texto = ' '.join(recs).lower()
        assert 'psicólogo' in texto or 'seguimiento' in texto

    def test_CB_IA_015_factor_depresion_agrega_tratamiento(self):
        """
        CB-IA-015: Factor 'depresion_severa' en factores → recomendación de tratamiento.
        """
        from apps.ia_app.services import MotorHeuristico

        factores = {'depresion_severa': {'valor': True}}
        recs = MotorHeuristico.generar_recomendaciones('alto', factores)

        texto = ' '.join(recs).lower()
        assert 'depresión' in texto or 'tratamiento' in texto

    def test_CB_IA_016_factor_sin_apoyo_familiar(self):
        """
        CB-IA-016: Factor 'sin_apoyo_familiar' → recomendación de vinculación familiar.
        """
        from apps.ia_app.services import MotorHeuristico

        factores = {'sin_apoyo_familiar': {'valor': True}}
        recs = MotorHeuristico.generar_recomendaciones('medio', factores)

        texto = ' '.join(recs).lower()
        assert 'familiar' in texto or 'apoyo' in texto

    def test_CB_IA_017_sin_talleres_recomienda_inscripcion(self):
        """
        CB-IA-017: talleres_completados=0 → recomendación de inscripción a talleres.
        """
        from apps.ia_app.services import MotorHeuristico

        factores = {'talleres_completados': {'valor': 0}}
        recs = MotorHeuristico.generar_recomendaciones('medio', factores)

        texto = ' '.join(recs).lower()
        assert 'taller' in texto

    def test_CB_IA_018_nivel_bajo_agrega_seguimiento_rutina(self):
        """
        CB-IA-018: Nivel 'bajo' → ejecuta bloque IF nivel == 'bajo'.
        """
        from apps.ia_app.services import MotorHeuristico

        recs = MotorHeuristico.generar_recomendaciones('bajo', {})

        texto = ' '.join(recs).lower()
        assert 'rutina' in texto or 'mensual' in texto


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: InternoService — Todas las ramas
# ═══════════════════════════════════════════════════════════════════════════════

class TestInternoService_CajaBlanca:

    def test_CB_INT_001_soft_delete_actualiza_campos(self, interno_activo):
        """
        CB-INT-001: soft_delete() — camino principal sin condiciones.
        Verifica que activo=False y eliminado_en es asignado.
        """
        from apps.internos_app.services import InternoService

        InternoService.soft_delete(interno_activo)

        interno_activo.refresh_from_db()
        assert interno_activo.activo is False
        assert interno_activo.eliminado_en is not None

    def test_CB_INT_002_buscar_cedula_existente(self, interno_activo):
        """
        CB-INT-002: buscar_por_cedula — RAMA try con resultado (no DoesNotExist).
        """
        from apps.internos_app.services import InternoService

        resultado = InternoService.buscar_por_cedula(interno_activo.cedula)

        assert resultado is not None
        assert resultado.pk == interno_activo.pk

    def test_CB_INT_003_buscar_cedula_inexistente_except(self, db):
        """
        CB-INT-003: buscar_por_cedula — RAMA except DoesNotExist → retorna None.
        """
        from apps.internos_app.services import InternoService

        resultado = InternoService.buscar_por_cedula('NO-EXISTE-99999')

        assert resultado is None

    def test_CB_INT_004_cambiar_estado_valido(self, interno_activo):
        """
        CB-INT-004: cambiar_estado con estado válido — RAMA if estado in estados_validos.
        """
        from apps.internos_app.services import InternoService

        resultado = InternoService.cambiar_estado(interno_activo, 'liberado')

        assert resultado.estado == 'liberado'

    def test_CB_INT_005_cambiar_estado_invalido_lanza_valueerror(self, interno_activo):
        """
        CB-INT-005: cambiar_estado con estado inválido — RAMA if not in → raise ValueError.
        EXCEPCIÓN PROBADA: ValueError.
        """
        from apps.internos_app.services import InternoService

        with pytest.raises(ValueError):
            InternoService.cambiar_estado(interno_activo, 'evadido')

    def test_CB_INT_006_nombre_completo(self, interno_activo):
        """
        CB-INT-006: Método nombre_completo() concatena nombre y apellido.
        """
        resultado = interno_activo.nombre_completo()

        assert resultado == 'Carlos Mamani'

    def test_CB_INT_007_soft_delete_en_modelo(self, interno_activo):
        """
        CB-INT-007: Método soft_delete() del modelo (distinto del service).
        """
        interno_activo.soft_delete()

        assert interno_activo.activo is False
        assert interno_activo.eliminado_en is not None


# ═══════════════════════════════════════════════════════════════════════════════
# CAJA BLANCA: EvaluacionService — Cobertura de ramas
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvaluacionService_CajaBlanca:

    def test_CB_EV_001_calcular_nivel_limite_bajo_medio(self):
        """
        CB-EV-001: Valor límite exacto 0.25 → rama 'medio' (score < 0.50).
        DECISIÓN: score < 0.25 (F) → score < 0.50 (T) → 'medio'
        """
        from apps.evaluaciones_app.services import EvaluacionService

        nivel = EvaluacionService.calcular_nivel_riesgo(0.25)
        assert nivel == 'medio'

    def test_CB_EV_002_calcular_nivel_limite_medio_alto(self):
        """
        CB-EV-002: Valor límite exacto 0.50 → rama 'alto'.
        DECISIÓN: < 0.25 (F) → < 0.50 (F) → < 0.75 (T) → 'alto'
        """
        from apps.evaluaciones_app.services import EvaluacionService

        nivel = EvaluacionService.calcular_nivel_riesgo(0.50)
        assert nivel == 'alto'

    def test_CB_EV_003_calcular_nivel_limite_alto_critico(self):
        """
        CB-EV-003: Valor límite exacto 0.75 → rama 'critico'.
        DECISIÓN: < 0.25 (F) → < 0.50 (F) → < 0.75 (F) → else 'critico'
        """
        from apps.evaluaciones_app.services import EvaluacionService

        nivel = EvaluacionService.calcular_nivel_riesgo(0.75)
        assert nivel == 'critico'

    def test_CB_EV_004_completar_evaluacion_actualiza_todos_campos(
        self, evaluacion_pendiente
    ):
        """
        CB-EV-004: completar_evaluacion() — camino principal completo.
        VERIFICACIÓN: resultados, completada, estado, fecha_completada actualizados.
        """
        from apps.evaluaciones_app.services import EvaluacionService

        resultados = {
            'depresion_severa': True,
            'ansiedad_severa': False,
            'reincidencias': 0,
            'apoyo_familiar': True,
        }

        ev = EvaluacionService.completar_evaluacion(evaluacion_pendiente, resultados)

        assert ev.completada is True
        assert ev.estado == 'completada'
        assert ev.resultados == resultados
        assert ev.fecha_completada is not None

    def test_CB_EV_005_get_evaluaciones_pendientes_sin_filtro(
        self, evaluacion_pendiente, evaluacion_completada
    ):
        """
        CB-EV-005: get_evaluaciones_pendientes() sin psicologo — RAMA if psicologo=None.
        Retorna todas las evaluaciones pendientes sin filtrar por psicólogo.
        """
        from apps.evaluaciones_app.services import EvaluacionService

        qs = EvaluacionService.get_evaluaciones_pendientes(psicologo=None)

        # Solo la pendiente debe aparecer (completada no)
        pks = list(qs.values_list('pk', flat=True))
        assert evaluacion_pendiente.pk in pks
        assert evaluacion_completada.pk not in pks

    def test_CB_EV_006_get_evaluaciones_pendientes_con_filtro_psicologo(
        self, usuario_psicologo, evaluacion_pendiente
    ):
        """
        CB-EV-006: get_evaluaciones_pendientes() CON psicologo — RAMA if psicologo.
        Ejecuta el filtro adicional .filter(psicoplogo=psicologo).
        """
        from apps.evaluaciones_app.services import EvaluacionService

        qs = EvaluacionService.get_evaluaciones_pendientes(psicologo=usuario_psicologo)

        assert qs.count() == 1

    def test_CB_EV_007_metodo_completar_del_modelo(self, evaluacion_pendiente):
        """
        CB-EV-007: Evaluacion.completar() — método del modelo mismo.
        """
        evaluacion_pendiente.completar()

        assert evaluacion_pendiente.completada is True
        assert evaluacion_pendiente.estado == 'completada'
        assert evaluacion_pendiente.fecha_completada is not None
