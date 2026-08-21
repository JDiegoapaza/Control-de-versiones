# apps/ia_app/services.py
"""
Motor de IA Heurístico Funcional para predicción de riesgo penitenciario.

ARQUITECTURA ML-READY:
  - Actualmente: motor heurístico con puntajes ponderados
  - Preparado para: scikit-learn, pandas, joblib en el futuro
  - Los features se guardan estructurados para dataset de entrenamiento futuro

PESOS HEURÍSTICOS:
  Factores de RIESGO (suman):
    + reincidencias:   +30 por reincidencia (max +90)
    + violencia:       +35
    + depresión severa:+20
    + ansiedad severa: +15
    + sin apoyo fam.:  +15

  Factores PROTECTORES (restan):
    - talleres complet.:-12 por taller (max -36)
    - apoyo familiar:  -15
    - evaluac. positiv.:-10
    - sin reincidencias:-10

Escala 0–100 → nivel: bajo(<25) | medio(<50) | alto(<75) | crítico(>=75)
"""

import logging
from .models import PrediccionRiesgo

logger = logging.getLogger(__name__)


class MotorHeuristico:
    """
    Motor heurístico documentado y reproducible.
    FUTURE: reemplazar _calcular_score() con modelo scikit-learn entrenado.
    """

    VERSION = 'heuristica-v2.0'

    # ── Constantes de peso ─────────────────────────────────────────────────────
    PESO_REINCIDENCIA = 30       # por reincidencia
    MAX_REINCIDENCIA  = 90
    PESO_VIOLENCIA    = 35
    PESO_DEPRESION    = 20
    PESO_ANSIEDAD     = 15
    PESO_SIN_APOYO    = 15
    PESO_TALLER       = -12      # por taller completado
    MAX_TALLERES      = -36
    PESO_APOYO_FAM    = -15
    PESO_EVAL_POS     = -10
    PESO_SIN_REINC    = -10

    @classmethod
    def extraer_features(cls, interno) -> dict:
        """
        Extrae features estructurados del interno.
        Formato compatible con pandas DataFrame para futura fase ML.

        Returns:
            dict con todos los features relevantes
        """
        features = {
            # Datos demográficos
            'edad': None,
            'sexo': interno.sexo,
            'estado': interno.estado,

            # Historial
            'reincidencias': 0,
            'delito_violento': False,

            # Evaluaciones psicológicas
            'depresion_severa': False,
            'ansiedad_severa': False,
            'nivel_riesgo_previo': None,
            'num_evaluaciones': 0,
            'calificacion_riesgo_promedio': None,

            # Rehabilitación
            'talleres_completados': 0,
            'en_rehabilitacion': False,
            'progreso_rehabilitacion': 0.0,

            # Red de apoyo
            'apoyo_familiar': False,
        }

        # Calcular edad
        if interno.fecha_nacimiento:
            from datetime import date
            hoy = date.today()
            features['edad'] = hoy.year - interno.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (interno.fecha_nacimiento.month, interno.fecha_nacimiento.day)
            )

        # Analizar delito
        delito_lower = (interno.delito or '').lower()
        violentos = ['homicidio', 'asesinato', 'robo agravado', 'violación', 'secuestro',
                     'lesiones graves', 'feminicidio', 'tentativa', 'violencia']
        features['delito_violento'] = any(p in delito_lower for p in violentos)

        # Analizar evaluaciones psicológicas
        try:
            evaluaciones = interno.evaluaciones.filter(activo=True, completada=True)
            features['num_evaluaciones'] = evaluaciones.count()

            if evaluaciones.exists():
                from django.db.models import Avg
                avg = evaluaciones.aggregate(p=Avg('calificacion_riesgo'))['p']
                features['calificacion_riesgo_promedio'] = avg

                # Último nivel de riesgo registrado
                ultima = evaluaciones.order_by('-fecha_creacion').first()
                if ultima:
                    features['nivel_riesgo_previo'] = ultima.nivel_riesgo
                    # Analizar resultados JSON para indicadores psicológicos
                    resultados = ultima.resultados or {}
                    if isinstance(resultados, dict):
                        features['depresion_severa'] = resultados.get('depresion_severa', False)
                        features['ansiedad_severa'] = resultados.get('ansiedad_severa', False)
                        features['reincidencias'] = int(resultados.get('reincidencias', 0))
                        features['apoyo_familiar'] = resultados.get('apoyo_familiar', False)
        except Exception as e:
            logger.warning(f'Error analizando evaluaciones de {interno}: {e}')

        # Analizar rehabilitación
        try:
            rehabilitaciones = interno.rehabilitaciones.all()
            completadas = rehabilitaciones.filter(estado='completado').count()
            en_proceso = rehabilitaciones.filter(estado='en_proceso').first()
            features['talleres_completados'] = completadas
            features['en_rehabilitacion'] = en_proceso is not None
            if en_proceso:
                features['progreso_rehabilitacion'] = en_proceso.progreso or 0.0
        except Exception as e:
            logger.warning(f'Error analizando rehabilitación de {interno}: {e}')

        return features

    @classmethod
    def calcular_score(cls, features: dict) -> tuple:
        """
        Calcula score heurístico (0–100) y factores determinantes.

        Returns:
            (score: float, factores: dict)

        FUTURE ML: esta función se reemplaza con:
            modelo = joblib.load('ml/models/riesgo_v3.pkl')
            X = pd.DataFrame([features])
            score = modelo.predict_proba(X)[0][1] * 100
        """
        score = 0.0
        factores = {}

        # ── FACTORES DE RIESGO ─────────────────────────────────────────────────
        reinc = min(features.get('reincidencias', 0), 3)
        if reinc > 0:
            pts = min(reinc * cls.PESO_REINCIDENCIA, cls.MAX_REINCIDENCIA)
            score += pts
            factores['reincidencias'] = {
                'valor': reinc,
                'impacto': f'+{pts:.0f}',
                'descripcion': f'{reinc} reincidencia(s) documentada(s)'
            }

        if features.get('delito_violento'):
            score += cls.PESO_VIOLENCIA
            factores['delito_violento'] = {
                'valor': True,
                'impacto': f'+{cls.PESO_VIOLENCIA}',
                'descripcion': 'Delito con componente de violencia'
            }

        if features.get('depresion_severa'):
            score += cls.PESO_DEPRESION
            factores['depresion_severa'] = {
                'valor': True,
                'impacto': f'+{cls.PESO_DEPRESION}',
                'descripcion': 'Depresión severa documentada'
            }

        if features.get('ansiedad_severa'):
            score += cls.PESO_ANSIEDAD
            factores['ansiedad_severa'] = {
                'valor': True,
                'impacto': f'+{cls.PESO_ANSIEDAD}',
                'descripcion': 'Ansiedad severa documentada'
            }

        if not features.get('apoyo_familiar'):
            score += cls.PESO_SIN_APOYO
            factores['sin_apoyo_familiar'] = {
                'valor': True,
                'impacto': f'+{cls.PESO_SIN_APOYO}',
                'descripcion': 'Sin red de apoyo familiar'
            }

        # Bonus si calificación previa es alta
        cal_prev = features.get('calificacion_riesgo_promedio')
        if cal_prev and cal_prev > 70:
            bonus = 10
            score += bonus
            factores['historial_riesgo_alto'] = {
                'valor': f'{cal_prev:.1f}%',
                'impacto': f'+{bonus}',
                'descripcion': 'Historial de calificación de riesgo elevada'
            }

        # ── FACTORES PROTECTORES ──────────────────────────────────────────────
        talleres = features.get('talleres_completados', 0)
        if talleres > 0:
            pts = max(talleres * cls.PESO_TALLER, cls.MAX_TALLERES)
            score += pts
            factores['talleres_completados'] = {
                'valor': talleres,
                'impacto': f'{pts:.0f}',
                'descripcion': f'{talleres} taller(es) de rehabilitación completado(s)'
            }

        if features.get('apoyo_familiar'):
            score += cls.PESO_APOYO_FAM
            factores['apoyo_familiar'] = {
                'valor': True,
                'impacto': f'{cls.PESO_APOYO_FAM}',
                'descripcion': 'Cuenta con red de apoyo familiar'
            }

        if features.get('reincidencias', 0) == 0:
            score += cls.PESO_SIN_REINC
            factores['sin_reincidencias'] = {
                'valor': True,
                'impacto': f'{cls.PESO_SIN_REINC}',
                'descripcion': 'Sin antecedentes de reincidencia'
            }

        if features.get('num_evaluaciones', 0) > 0 and not features.get('nivel_riesgo_previo') in ('alto', 'critico'):
            score += cls.PESO_EVAL_POS
            factores['evaluaciones_favorables'] = {
                'valor': True,
                'impacto': f'{cls.PESO_EVAL_POS}',
                'descripcion': 'Evaluaciones psicológicas sin riesgo crítico'
            }

        # Clamp 0–100
        score = max(0.0, min(100.0, score))
        return score, factores

    @classmethod
    def score_a_nivel(cls, score: float) -> str:
        if score < 25:
            return 'bajo'
        elif score < 50:
            return 'medio'
        elif score < 75:
            return 'alto'
        return 'critico'

    @classmethod
    def generar_recomendaciones(cls, nivel: str, factores: dict) -> list:
        """Genera recomendaciones automáticas según nivel y factores."""
        recomendaciones = []

        if nivel == 'critico':
            recomendaciones.append('⚠️ URGENTE: Evaluación psicológica inmediata requerida.')
            recomendaciones.append('Implementar protocolo de vigilancia intensiva.')
            recomendaciones.append('Notificar al equipo directivo y de seguridad.')

        if nivel in ('alto', 'critico'):
            recomendaciones.append('Asignar psicólogo de cabecera con seguimiento semanal.')
            recomendaciones.append('Inscribir en programa de gestión de ira y conducta.')

        if 'depresion_severa' in factores:
            recomendaciones.append('Iniciar tratamiento psicológico para depresión severa.')

        if 'ansiedad_severa' in factores:
            recomendaciones.append('Incluir en terapia de manejo de ansiedad.')

        if 'sin_apoyo_familiar' in factores:
            recomendaciones.append('Promover el contacto y vinculación familiar.')
            recomendaciones.append('Evaluar trabajo social para red de apoyo.')

        if factores.get('talleres_completados', {}).get('valor', 0) == 0:
            recomendaciones.append('Inscribir en talleres de rehabilitación disponibles.')

        if 'reincidencias' in factores:
            recomendaciones.append('Implementar programa especializado de reinserción social.')

        if nivel == 'bajo':
            recomendaciones.append('✅ Mantener seguimiento de rutina mensual.')
            recomendaciones.append('Continuar con programas de rehabilitación actuales.')

        return recomendaciones


class IAService:
    """
    Servicio principal de IA.
    Orquesta extracción de features, cálculo heurístico y persistencia.
    """

    MODEL_VERSION = MotorHeuristico.VERSION

    @staticmethod
    def predecir_riesgo(interno, usuario=None) -> PrediccionRiesgo:
        """
        Genera predicción de riesgo para un interno usando motor heurístico.

        FUTURE ML:
            # from ml.predict import predict_risk
            # resultado = predict_risk(interno_id=str(interno.pk))
        """
        motor = MotorHeuristico

        # 1. Extraer features estructurados
        features = motor.extraer_features(interno)

        # 2. Calcular score heurístico
        score_raw, factores = motor.calcular_score(features)
        score_normalizado = score_raw / 100.0  # normalizar a 0-1

        # 3. Determinar nivel
        nivel = motor.score_a_nivel(score_raw)

        # 4. Generar recomendaciones
        recomendaciones = motor.generar_recomendaciones(nivel, factores)

        # 5. Confianza: más evaluaciones = mayor confianza
        num_eval = features.get('num_evaluaciones', 0)
        confianza = min(0.5 + (num_eval * 0.1), 0.95) * 100  # 50% base, +10% por evaluación

        # 6. Persistir (incluyendo features para dataset futuro ML)
        prediccion = PrediccionRiesgo.objects.create(
            interno=interno,
            nivel_riesgo=nivel,
            score=score_normalizado,
            confianza=confianza,
            modelo_version=IAService.MODEL_VERSION,
            generado_por=usuario,
            factores={
                'score_raw': score_raw,
                'nivel': nivel,
                'features': features,           # ← dataset para ML futuro
                'factores_determinantes': factores,
                'recomendaciones': recomendaciones,
                'motor': 'heuristico',
            },
            observaciones=f"Score heurístico: {score_raw:.1f}/100 | Nivel: {nivel.upper()} | Confianza: {confianza:.0f}%",
        )

        logger.info(f'[IA] Predicción generada: interno={interno.cedula} nivel={nivel} score={score_raw:.1f}')
        return prediccion

    @staticmethod
    def _calcular_nivel(score: float) -> str:
        return MotorHeuristico.score_a_nivel(score * 100)
