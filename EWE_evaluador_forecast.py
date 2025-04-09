

#
# Este script evalúa los pronósticos de ventas generados por diferentes algoritmos
# y selecciona el mejor algoritmo para cada SKU y sucursal.

# Preparar los datos con los siguientes campos:
# SKU | Fecha_Pronóstico | Horizonte | Algoritmo | Predicción | Real | Error  (forecast)
# SKU | Fecha_Pronóstico | Semana_Pronosticada | Algoritmo | Predicción

"""
    PROVEEDOR_ID = 596
    ALGORITMO = "ALGO_01"
    ARCHIVO_FORECAST = "596_PROCTER_ALGO_01_Solicitudes_Compra.csv"

    
"""

import os
import time
import pandas as pd
import numpy as np
from dotenv import dotenv_values
import pyodbc
import psycopg2 as pg2

secrets = dotenv_values(".env")   # Connection String from .env
folder = secrets["FOLDER_DATOS"]

# Función de conexión a SQL Server
def Open_Connection():
    secrets = dotenv_values(".env")
    conn_str = f'DRIVER={secrets["DRIVER2"]};SERVER={secrets["SERVIDOR2"]};PORT={secrets["PUERTO2"]};DATABASE={secrets["BASE2"]};UID={secrets["USUARIO2"]};PWD={secrets["CONTRASENA2"]}'
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Error en la conexión SQL Server: {e}")
        return None

# Función de conexión a PostgreSQL
def Open_Conn_Postgres():
    secrets = dotenv_values(".env")
    conn_str = f"dbname={secrets['BASE4']} user={secrets['USUARIO4']} password={secrets['CONTRASENA4']} host={secrets['SERVIDOR4']} port={secrets['PUERTO4']}"
    for i in range(5):
        try:
            conn = pg2.connect(conn_str)
            return conn
        except Exception as e:
            print(f"Error en la conexión PostgreSQL, intento {i+1}/5: {e}")
            time.sleep(5)
    return None

# Carga de todos los archivos CSV de forecast
def cargar_todos_los_forecasts(carpeta_path, id_proveedor):
    dfs = []
    for file in os.listdir(carpeta_path):
        if file.startswith(str(id_proveedor)) and file.endswith("Compra.csv"):
            df = pd.read_csv(os.path.join(carpeta_path, file))
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# Extracción de ventas desde SQL Server
def extraer_ventas(id_proveedor):
    query = f"""
    SELECT V.[F_VENTA] as Fecha,
        V.[C_ARTICULO] as Codigo_Articulo,
        V.[C_SUCU_EMPR] as Sucursal,
        V.[Q_UNIDADES_VENDIDAS] as Unidades
    FROM [DCO-DBCORE-P02].[DiarcoEst].[dbo].[T702_EST_VTAS_POR_ARTICULO] V
    LEFT JOIN [DCO-DBCORE-P02].[DiarcoEst].[dbo].[T050_ARTICULOS] A 
        ON V.C_ARTICULO = A.C_ARTICULO
    WHERE A.[C_PROVEEDOR_PRIMARIO] = {id_proveedor} 
        AND V.F_VENTA >= '20250301' AND A.M_BAJA ='N'
    """
    conn = Open_Connection()
    if conn:
        df_ventas = pd.read_sql(query, conn)
        conn.close()
        df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha'])
        df_ventas['Semana'] = df_ventas['Fecha'].dt.isocalendar().week
        return df_ventas
    else:
        return pd.DataFrame()

# Cálculo de métricas por SKU y algoritmo
def consolidar_metricas_para_todos(df_forecast, df_ventas):
    df_forecast['Semana'] = df_forecast['ventana']
    df = pd.merge(
        df_forecast,
        df_ventas,
        how='inner',
        on=['Codigo_Articulo', 'Sucursal', 'Semana']
    )
    df['Error_Absoluto'] = np.abs(df['Forecast'] - df['Unidades'])
    df['Error_Cuadratico'] = (df['Forecast'] - df['Unidades']) ** 2
    df['sMAPE'] = 2 * np.abs(df['Forecast'] - df['Unidades']) / (
        np.abs(df['Forecast']) + np.abs(df['Unidades']) + 1e-6
    )

    resumen = df.groupby(
        ['Codigo_Articulo', 'algoritmo'], as_index=False
    ).agg({
        'Error_Absoluto': 'mean',
        'Error_Cuadratico': 'mean',
        'sMAPE': 'mean'
    })

    resumen.rename(columns={
        'Error_Absoluto': 'MAE',
        'Error_Cuadratico': 'RMSE'
    }, inplace=True)
    resumen['RMSE'] = np.sqrt(resumen['RMSE'])

    return resumen

# Selección del mejor algoritmo por SKU
def seleccionar_mejor_algoritmo(df_metricas, criterio='MAE'):
    df_metricas['Rank'] = df_metricas.groupby('Codigo_Articulo')[criterio].rank(method='min')
    df_mejor = df_metricas[df_metricas['Rank'] == 1].drop(columns='Rank')
    df_mejor.rename(columns={'algoritmo': 'Algoritmo_Optimo'}, inplace=True)
    df_mejor['Fecha_Evaluacion'] = pd.Timestamp.today().normalize()
    return df_mejor

# Guardar resultado en PostgreSQL
def guardar_en_postgres(df, tabla_destino):
    conn = Open_Conn_Postgres()
    if conn is not None:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute(f"""
                INSERT INTO {tabla_destino} 
                (Codigo_Articulo, Algoritmo_Optimo, MAE, RMSE, sMAPE, Fecha_Evaluacion)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (Codigo_Articulo) DO UPDATE 
                SET Algoritmo_Optimo = EXCLUDED.Algoritmo_Optimo,
                    MAE = EXCLUDED.MAE,
                    RMSE = EXCLUDED.RMSE,
                    sMAPE = EXCLUDED.sMAPE,
                    Fecha_Evaluacion = EXCLUDED.Fecha_Evaluacion;
            """, (
                int(row['Codigo_Articulo']),
                row['Algoritmo_Optimo'],
                float(row['MAE']),
                float(row['RMSE']),
                float(row['sMAPE']),
                row['Fecha_Evaluacion']
            ))
        conn.commit()
        cursor.close()
        conn.close()
        print("Datos cargados en PostgreSQL.")
    else:
        print("No se pudo establecer conexión con PostgreSQL.")

# Main
if __name__ == "__main__":
    id_proveedor = 1074
    carpeta_forecasts = folder
    tabla_destino = "forecast_algoritmo_optimo"

    print("Cargando predicciones...")
    df_forecast = cargar_todos_los_forecasts(carpeta_forecasts, id_proveedor)

    print("Extrayendo ventas reales...")
    df_ventas = extraer_ventas(id_proveedor)

    print("Calculando métricas...")
    df_metricas = consolidar_metricas_para_todos(df_forecast, df_ventas)

    print("Seleccionando el mejor algoritmo...")
    df_mejor_algoritmo = seleccionar_mejor_algoritmo(df_metricas, criterio='MAE')

    print("Guardando resultados...")
    guardar_en_postgres(df_mejor_algoritmo, tabla_destino)

    print("Proceso finalizado.")
