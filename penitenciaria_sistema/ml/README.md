# Módulo ML — SGEP (Sistema de Gestión Penitenciaria)

## Estado Actual
Motor HEURÍSTICO funcional (v2.0). Las predicciones son reproducibles y documentadas.

## Arquitectura ML-Ready

```
ml/
├── models/         ← Modelos scikit-learn entrenados (.pkl via joblib)
├── datasets/       ← Datasets CSV exportados de PrediccionRiesgo.factores.features
├── train/          ← Scripts de entrenamiento
└── predict/        ← Pipeline de predicción
```

## Futuro: Migrar a ML Real

### Paso 1 — Exportar dataset
```python
# ml/datasets/exportar.py
from apps.ia_app.models import PrediccionRiesgo
import pandas as pd

registros = PrediccionRiesgo.objects.all()
data = []
for p in registros:
    features = p.factores.get('features', {})
    features['nivel_riesgo'] = p.nivel_riesgo
    features['score'] = p.score
    data.append(features)

df = pd.DataFrame(data)
df.to_csv('ml/datasets/riesgo_dataset.csv', index=False)
```

### Paso 2 — Entrenar modelo
```python
# ml/train/entrenar.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

df = pd.read_csv('ml/datasets/riesgo_dataset.csv')
features_cols = ['reincidencias','delito_violento','depresion_severa',
                 'ansiedad_severa','talleres_completados','apoyo_familiar',
                 'num_evaluaciones','progreso_rehabilitacion']

X = df[features_cols].fillna(0)
y = df['nivel_riesgo']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)
joblib.dump(modelo, 'ml/models/riesgo_rf_v3.pkl')
```

### Paso 3 — Usar en predicción
```python
# En apps/ia_app/services.py, reemplazar MotorHeuristico.calcular_score() con:
import joblib, pandas as pd

modelo = joblib.load('ml/models/riesgo_rf_v3.pkl')
X = pd.DataFrame([features])
nivel = modelo.predict(X)[0]
proba = modelo.predict_proba(X)[0]
score = max(proba) * 100
```

## Dependencias futuras
```
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
joblib>=1.3.0
```
