import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Dropout
# pyrefly: ignore [missing-import]
import joblib

print("Cargando entorno y verificando TensorFlow...")
print(f"Versión de TensorFlow: {tf.__version__}\n")

# Definición de rutas base absolutas del proyecto SGEP para evitar errores de consola
BASE_ML_DIR = r"C:\Users\DIEGO\Documents\SGEP_V3.1\penitenciaria_sistema\ml"
ruta_csv = os.path.join(BASE_ML_DIR, "datasets", "compas-scores-two-years.csv")

# 1. Cargar datos
if not os.path.exists(ruta_csv):
    raise FileNotFoundError(f"No se encontró el dataset en la ruta absoluta configurada: {ruta_csv}")

df = pd.read_csv(ruta_csv)

# 2. Seleccionar variables (Features y Target)
features = ['age', 'sex', 'race', 'priors_count', 'juv_fel_count', 'juv_misd_count', 'juv_other_count', 'c_charge_degree']
target = 'two_year_recid'

X = df[features].copy()
y = df[target].copy()

# Limpieza básica de valores nulos
X = X.fillna({
    'age': X['age'].median(),
    'priors_count': 0,
    'juv_fel_count': 0,
    'juv_misd_count': 0,
    'juv_other_count': 0
})

# 3. Separar en conjuntos de Entrenamiento (80%) y Prueba (20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 4. Pipeline de Preprocesamiento
num_features = ['age', 'priors_count', 'juv_fel_count', 'juv_misd_count', 'juv_other_count']
cat_features = ['sex', 'race', 'c_charge_degree']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_features),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_features)
    ])

# Ajustar y transformar datos
X_train_proc = preprocessor.fit_transform(X_train).astype(np.float32)
X_test_proc = preprocessor.transform(X_test).astype(np.float32)

# Crear carpeta para guardar el preprocesador y el modelo si no existen
carpeta_models = os.path.join(BASE_ML_DIR, "models")
os.makedirs(carpeta_models, exist_ok=True)

# Guardar el preprocesador (lo necesitaremos en Django para transformar los datos nuevos de los internos)
joblib.dump(preprocessor, os.path.join(carpeta_models, "preprocesador.joblib"))
print("¡Preprocesador guardado con éxito!")

# 5. DISEÑO DE LA ARQUITECTURA DE LA IA (Red Neuronal)
input_dim = X_train_proc.shape[1]

model = Sequential([
    # Capa de entrada y primera capa oculta
    Dense(32, activation='relu', input_shape=(input_dim,)),
    Dropout(0.2),  # Evita el sobreajuste (overfitting)
    
    # Segunda capa oculta
    Dense(16, activation='relu'),
    Dropout(0.2),
    
    # Capa de salida (1 neurona con sigmoide para clasificación binaria: 0 o 1)
    Dense(1, activation='sigmoid')
])

# Compilación del modelo
model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy', tf.keras.metrics.Recall(), tf.keras.metrics.Precision()]
)

model.summary()

# 6. ENTRENAMIENTO DE LA IA
print("\nIniciando el entrenamiento del modelo...")
history = model.fit(
    X_train_proc, y_train,
    validation_data=(X_test_proc, y_test),
    epochs=30,
    batch_size=32,
    verbose=1
)

# 7. GUARDAR EL MODELO ENTRENADO
ruta_modelo = os.path.join(carpeta_models, "modelo_riesgo_reincidencia.keras")
model.save(ruta_modelo)
print(f"\n¡Modelo de IA guardado exitosamente en: {ruta_modelo}!")

# 8. Gráfico de rendimiento (Guarda una imagen en ml/reports)
carpeta_reports = os.path.join(BASE_ML_DIR, "reports")
os.makedirs(carpeta_reports, exist_ok=True)

plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Val Accuracy')
plt.legend()
plt.title('Precisión del Modelo')

plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.legend()
plt.title('Pérdida del Modelo')

plt.savefig(os.path.join(carpeta_reports, "rendimiento_entrenamiento.png"))
print(f"Gráfico de rendimiento guardado en: {os.path.join(carpeta_reports, 'rendimiento_entrenamiento.png')}")