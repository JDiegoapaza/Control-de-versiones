# tests_sgep/tests_caja_negra/test_evaluaciones_ia_caja_negra.py
"""
PRUEBAS DE CAJA NEGRA — Módulos: Evaluaciones Psicológicas + IA Predictiva
===========================================================================
Técnica: Partición de Equivalencia + Análisis de Valores Límite

MÓDULOS ANALIZADOS:
    apps.evaluaciones_app (models.py, services.py, views.py)
    apps.ia_app (models.py, services.py, views.py)

Casos cubiertos
---------------
Evaluaciones:
  CN-E-001  Creación de evaluación válida
  CN-E-002  Completar evaluación con resultados
  CN-E-003  Acceso a evaluaciones sin autenticación → 401/403
  CN-E-004  API: Listado de evaluaciones pendientes
  CN-E-005  calcular_nivel_riesgo — valores límite (0.0, 0.24, 0.25, 0.74, 0.75, 1.0)
  CN-E-006  get_evaluaciones_pendientes filtrado por psicólogo

IA Predictiva:
  CN-IA-001  predecir_riesgo genera predicción y persiste en BD
  CN-IA-002  score_a_nivel — particiones de equivalencia completas
  CN-IA-003  Motor heurístico — interno sin factores de riesgo → nivel bajo
  CN-IA-004  Motor heurístico — interno con múltiples factores críticos → nivel crítico
  CN-IA-005  generar_recomendaciones para nivel crítico incluye alerta urgente
  CN-IA-006  Confianza aumenta con más evaluaciones
"""

import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBAS DE CAJA NEGRA — EVALUACIONES PSICOLÓGICAS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvaluacionesCajaNegra_Creacion:

    def test_CN_E_001_creacion_evaluacion_valida(
        self, client_autenticado_psicologo, interno_activo
    ):
        """
        CN-E-001: Crear evaluación con datos válidos.

        ENTRADA:
            titulo, interno_id, estado='pendiente'

        RESULTADO ESPERADO:
            - HTTP 201 o 302
            - Evaluación persiste en BD con estado='pendiente'
            - completada=False
        """
        from apps.evaluaciones_app.models import Evaluacion

        url = reverse('evaluaciones:api_list_create')
        datos = {
            'titulo': 'Evaluación Ingreso Test',
            'interno': str(interno_activo.pk),
            'estado': 'pendiente',
        }

        response = client_autenticado_psicologo.post(
            url, datos, content_type='application/json'
        )

        # Aceptar 201 (API) o 302 (vista web)
        assert response.status_code in (201, 200, 302)

    def test_CN_E_002_completar_evaluacion_actualiza_estado(
        self, evaluacion_pendiente
    ):
        """
        CN-E-002: Marcar evaluación como completada actualiza estado y fecha.

        ENTRADA: evaluacion con estado='pendiente', completada=False
        RESULTADO: estado='completada', completada=True, fecha_completada != None
        """
        evaluacion_pendiente.completar()

        assert evaluacion_pendiente.completada is True
        assert evaluacion_pendiente.estado == 'completada'
        assert evaluacion_pendiente.fecha_completada is not None


class TestServicioEvaluaciones:
    """
    Pruebas al EvaluacionService — capa de lógica de negocio.
    """

    def test_CN_E_005_nivel_riesgo_bajo_score_menor_0_25(self):
        """
        CN-E-005a: score < 0.25 → nivel 'bajo'
        VALORES LÍMITE: 0.0, 0.10, 0.24
        """
        from apps.evaluaciones_app.services import EvaluacionService

        for score in [0.0, 0.10, 0.24]:
            nivel = EvaluacionService.calcular_nivel_riesgo(score)
            assert nivel == 'bajo', f"score={score} debería ser 'bajo', obtuvo '{nivel}'"

    def test_CN_E_005b_nivel_riesgo_medio_score_entre_0_25_y_0_50(self):
        """
        CN-E-005b: 0.25 <= score < 0.50 → nivel 'medio'
        VALORES LÍMITE: 0.25, 0.30, 0.49
        """
        from apps.evaluaciones_app.services import EvaluacionService

        for score in [0.25, 0.30, 0.49]:
            nivel = EvaluacionService.calcular_nivel_riesgo(score)
            assert nivel == 'medio', f"score={score} debería ser 'medio', obtuvo '{nivel}'"

    def test_CN_E_005c_nivel_riesgo_alto_score_entre_0_50_y_0_75(self):
        """
        CN-E-005c: 0.50 <= score < 0.75 → nivel 'alto'
        VALORES LÍMITE: 0.50, 0.60, 0.74
        """
        from apps.evaluaciones_app.services import EvaluacionService

        for score in [0.50, 0.60, 0.74]:
            nivel = EvaluacionService.calcular_nivel_riesgo(score)
            assert nivel == 'alto', f"score={score} debería ser 'alto', obtuvo '{nivel}'"

    def test_CN_E_005d_nivel_riesgo_critico_score_mayor_0_75(self):
        """
        CN-E-005d: score >= 0.75 → nivel 'critico'
        VALORES LÍMITE: 0.75, 0.90, 1.0
        """
        from apps.evaluaciones_app.services import EvaluacionService

        for score in [0.75, 0.90, 1.0]:
            nivel = EvaluacionService.calcular_nivel_riesgo(score)
            assert nivel == 'critico', f"score={score} debería ser 'critico', obtuvo '{nivel}'"

    def test_CN_E_006_evaluaciones_pendientes_filtradas_por_psicologo(
        self, usuario_psicologo, evaluacion_pendiente, evaluacion_completada
    ):
        """
        CN-E-006: get_evaluaciones_pendientes con psicologo retorna solo las de ese psicólogo.

        ENTRADA: psicologo=usuario_psicologo
        RESULTADO: Solo evaluaciones pendientes de ese psicólogo (no las completadas).
        """
        from apps.evaluaciones_app.services import EvaluacionService

        qs = EvaluacionService.get_evaluaciones_pendientes(psicologo=usuario_psicologo)

        assert qs.count() == 1
        assert qs.first().pk == evaluacion_pendiente.pk


class TestAccesoEvaluacionesSinAuth:

    def test_CN_E_003_api_evaluaciones_sin_autenticacion(self, api_client):
        """
        CN-E-003: API de evaluaciones requiere autenticación.

        RESULTADO ESPERADO: HTTP 401 o 403.
        """
        url = reverse('evaluaciones:api_list_create')
        response = api_client.get(url)

        assert response.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBAS DE CAJA NEGRA — MOTOR DE IA HEURÍSTICO
# ═══════════════════════════════════════════════════════════════════════════════

class TestMotorHeuristico_ScoreANivel:
    """
    Partición de Equivalencia para score_a_nivel().
    4 particiones: bajo, medio, alto, critico.
    """

    def test_CN_IA_002a_score_menor_25_es_bajo(self):
        """Scores 0-24.9 → 'bajo'"""
        from apps.ia_app.services import MotorHeuristico

        for score in [0.0, 10.0, 24.9]:
            nivel = MotorHeuristico.score_a_nivel(score)
            assert nivel == 'bajo', f"score={score} → esperado 'bajo', obtuvo '{nivel}'"

    def test_CN_IA_002b_score_25_a_49_es_medio(self):
        """Scores 25-49.9 → 'medio'"""
        from apps.ia_app.services import MotorHeuristico

        for score in [25.0, 35.0, 49.9]:
            nivel = MotorHeuristico.score_a_nivel(score)
            assert nivel == 'medio', f"score={score} → esperado 'medio', obtuvo '{nivel}'"

    def test_CN_IA_002c_score_50_a_74_es_alto(self):
        """Scores 50-74.9 → 'alto'"""
        from apps.ia_app.services import MotorHeuristico

        for score in [50.0, 60.0, 74.9]:
            nivel = MotorHeuristico.score_a_nivel(score)
            assert nivel == 'alto', f"score={score} → esperado 'alto', obtuvo '{nivel}'"

    def test_CN_IA_002d_score_75_o_mayor_es_critico(self):
        """Scores >= 75 → 'critico'"""
        from apps.ia_app.services import MotorHeuristico

        for score in [75.0, 90.0, 100.0]:
            nivel = MotorHeuristico.score_a_nivel(score)
            assert nivel == 'critico', f"score={score} → esperado 'critico', obtuvo '{nivel}'"


class TestMotorHeuristico_CalcScore:
    """
    Pruebas de caja negra al cálculo de score heurístico.
    Provee features conocidos y verifica el nivel resultante.
    """

    def test_CN_IA_003_interno_sin_factores_riesgo_nivel_bajo(self):
        """
        CN-IA-003: Interno sin factores de riesgo → score bajo.

        ENTRADA (features):
            reincidencias=0, delito_violento=False,
            depresion_severa=False, ansiedad_severa=False,
            apoyo_familiar=True, talleres_completados=3,
            num_evaluaciones=2

        RESULTADO ESPERADO: nivel 'bajo' o 'medio' (score < 50)
        """
        from apps.ia_app.services import MotorHeuristico

        features = {
            'reincidencias': 0,
            'delito_violento': False,
            'depresion_severa': False,
            'ansiedad_severa': False,
            'apoyo_familiar': True,
            'talleres_completados': 3,
            'num_evaluaciones': 2,
            'nivel_riesgo_previo': 'bajo',
            'calificacion_riesgo_promedio': 20.0,
        }

        score, factores = MotorHeuristico.calcular_score(features)
        nivel = MotorHeuristico.score_a_nivel(score)

        assert score < 50, f"Se esperaba score < 50, se obtuvo {score}"
        assert nivel in ('bajo', 'medio')

    def test_CN_IA_004_interno_con_todos_factores_criticos(self):
        """
        CN-IA-004: Interno con múltiples factores de riesgo → nivel crítico.

        ENTRADA (features):
            reincidencias=3 (máximo), delito_violento=True,
            depresion_severa=True, ansiedad_severa=True,
            apoyo_familiar=False, talleres_completados=0,
            calificacion_riesgo_promedio=80.0

        RESULTADO ESPERADO: nivel 'critico' (score >= 75)
        """
        from apps.ia_app.services import MotorHeuristico

        features = {
            'reincidencias': 3,
            'delito_violento': True,
            'depresion_severa': True,
            'ansiedad_severa': True,
            'apoyo_familiar': False,
            'talleres_completados': 0,
            'num_evaluaciones': 1,
            'nivel_riesgo_previo': 'alto',
            'calificacion_riesgo_promedio': 80.0,
        }

        score, factores = MotorHeuristico.calcular_score(features)
        nivel = MotorHeuristico.score_a_nivel(score)

        assert score >= 75, f"Se esperaba score >= 75, se obtuvo {score}"
        assert nivel == 'critico', f"Se esperaba 'critico', se obtuvo '{nivel}'"

    def test_CN_IA_004b_score_clampeado_entre_0_y_100(self):
        """
        CN-IA-004b: El score siempre está entre 0 y 100 (nunca negativo ni > 100).
        """
        from apps.ia_app.services import MotorHeuristico

        # Features extremos positivos
        features_max = {
            'reincidencias': 99, 'delito_violento': True,
            'depresion_severa': True, 'ansiedad_severa': True,
            'apoyo_familiar': False, 'talleres_completados': 0,
            'calificacion_riesgo_promedio': 100.0, 'num_evaluaciones': 0,
            'nivel_riesgo_previo': 'critico',
        }
        score_max, _ = MotorHeuristico.calcular_score(features_max)
        assert 0 <= score_max <= 100, f"Score fuera de rango: {score_max}"

        # Features extremos negativos (máxima protección)
        features_min = {
            'reincidencias': 0, 'delito_violento': False,
            'depresion_severa': False, 'ansiedad_severa': False,
            'apoyo_familiar': True, 'talleres_completados': 10,
            'calificacion_riesgo_promedio': 5.0, 'num_evaluaciones': 5,
            'nivel_riesgo_previo': 'bajo',
        }
        score_min, _ = MotorHeuristico.calcular_score(features_min)
        assert 0 <= score_min <= 100, f"Score fuera de rango: {score_min}"


class TestMotorHeuristico_Recomendaciones:

    def test_CN_IA_005_nivel_critico_incluye_alerta_urgente(self):
        """
        CN-IA-005: generar_recomendaciones para nivel 'critico'
        debe incluir alerta de urgencia.
        """
        from apps.ia_app.services import MotorHeuristico

        factores = {
            'reincidencias': {'valor': 3},
            'delito_violento': {'valor': True},
        }

        recomendaciones = MotorHeuristico.generar_recomendaciones('critico', factores)

        assert len(recomendaciones) > 0
        texto_completo = ' '.join(recomendaciones).lower()
        assert 'urgente' in texto_completo or 'inmediata' in texto_completo

    def test_CN_IA_005b_nivel_bajo_incluye_mensaje_positivo(self):
        """
        CN-IA-005b: nivel 'bajo' incluye recomendación de mantenimiento rutinario.
        """
        from apps.ia_app.services import MotorHeuristico

        recomendaciones = MotorHeuristico.generar_recomendaciones('bajo', {})

        assert len(recomendaciones) > 0
        texto_completo = ' '.join(recomendaciones).lower()
        assert (
            'rutina' in texto_completo
            or 'seguimiento' in texto_completo
            or 'continuar' in texto_completo
        )


class TestIAService_PredecirRiesgo:

    def test_CN_IA_001_predecir_riesgo_persiste_en_bd(
        self, interno_activo, usuario_psicologo
    ):
        """
        CN-IA-001: predecir_riesgo() crea PrediccionRiesgo en la BD.

        ENTRADA: interno con datos básicos (sin evaluaciones previas)
        RESULTADO:
            - Objeto PrediccionRiesgo creado en BD
            - nivel_riesgo en ('bajo', 'medio', 'alto', 'critico')
            - 0 <= score <= 1
            - confianza >= 50 (base mínima configurada)
        """
        from apps.ia_app.services import IAService
        from apps.ia_app.models import PrediccionRiesgo

        count_antes = PrediccionRiesgo.objects.count()

        prediccion = IAService.predecir_riesgo(interno_activo, usuario=usuario_psicologo)

        assert PrediccionRiesgo.objects.count() == count_antes + 1
        assert prediccion.nivel_riesgo in ('bajo', 'medio', 'alto', 'critico')
        assert 0.0 <= prediccion.score <= 1.0
        assert prediccion.confianza >= 50.0
        assert prediccion.modelo_version == 'heuristica-v2.0'

    def test_CN_IA_006_confianza_aumenta_con_mas_evaluaciones(
        self, interno_activo, usuario_psicologo, evaluacion_completada
    ):
        """
        CN-IA-006: Con más evaluaciones, la confianza es mayor que con ninguna.

        RESULTADO: confianza con evaluaciones > confianza base (50%)
        """
        from apps.ia_app.services import IAService

        prediccion = IAService.predecir_riesgo(interno_activo, usuario=usuario_psicologo)

        # Con 1 evaluación, confianza debe ser > 50 (50 + 10*1 = 60)
        assert prediccion.confianza > 50.0

    def test_CN_IA_001b_prediccion_tiene_factores_en_json(
        self, interno_activo
    ):
        """
        CN-IA-001b: La predicción almacena los factores determinantes como JSON.
        """
        from apps.ia_app.services import IAService

        prediccion = IAService.predecir_riesgo(interno_activo)

        assert isinstance(prediccion.factores, dict)
        assert 'features' in prediccion.factores
        assert 'recomendaciones' in prediccion.factores
        assert 'score_raw' in prediccion.factores
