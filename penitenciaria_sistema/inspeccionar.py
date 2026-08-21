import pandas as pd
import os

# Corregimos la ruta incluyendo la carpeta 'datasets'
ruta_dataset = os.path.join("ml", "datasets", "compas-scores-two-years.csv")

if not os.path.exists(ruta_dataset):
    print(f"Error: No se encontró el archivo en la ruta '{ruta_dataset}'.")
    print("Por favor, verifica que el nombre del archivo CSV sea exactamente 'compas-scores-two-years.csv'.")
else:
    # Cargar el dataset
    df = pd.read_csv(ruta_dataset)

    print("=========================================")
    print("      INSPECCIÓN INICIAL DEL DATASET     ")
    print("=========================================\n")

    print(f"1. Dimensiones (Filas, Columnas): {df.shape}\n")

    print("2. Lista Completa de Columnas:")
    print(df.columns.tolist())
    print("\n")

    print("3. Conteo de la Variable Objetivo (two_year_recid):")
    print(df['two_year_recid'].value_counts())