"""
Nombre del módulo: S30_GENERA_Grafico_Detalle.py

Descripción:
Partiendo de los datos extendidos con estado 30, se generan los gráficos de detalle para cada artículo y sucursal.
Se guarda el archivo CSV con los datos extendidos y los gráficos en formato base64.
Utiliza estad intermedio 35 miestras está graficando. Al finalizar se actualiza el estado a 40 en la base de datos.

Autor: EWE - Zeetrex
Fecha de creación: [2025-03-22]
"""

# Solo importar lo necesario desde el módulo de funciones
from funciones_forecast import (
    Open_Conn_Postgres,
    Close_Connection,
    get_excecution_by_status,
    update_execution,
    generar_grafico_base64
)

import pandas as pd # uso localmente la lectura de archivos.
import ace_tools_open as tools

from dotenv import dotenv_values
secrets = dotenv_values(".env")
folder = secrets["FOLDER_DATOS"]

# También podés importar funciones adicionales si tu módulo las necesita
def insertar_graficos_forecast(algoritmo, name, id_proveedor):
        
    # Recuperar Historial de Ventas
    df_ventas = pd.read_csv(f'{folder}/{name}_Ventas.csv')
    df_ventas['Codigo_Articulo']= df_ventas['Codigo_Articulo'].astype(int)
    df_ventas['Sucursal']= df_ventas['Sucursal'].astype(int)
    df_ventas['Fecha']= pd.to_datetime(df_ventas['Fecha'])

    # Recuperando Forecast Calculado
    df_forecast = pd.read_csv(f'{folder}/{algoritmo}_Solicitudes_Compra.csv')
    df_forecast.fillna(0)   # Por si se filtró algún missing value
    print(f"-> Datos Recuperados del CACHE: {id_proveedor}, Label: {name}")
    
    # Agregar la nueva columna de gráficos en df_forecast Iterando sobre todo el DATAFRAME
    df_forecast["GRAFICO"] = df_forecast.apply(
        lambda row: generar_grafico_base64(df_ventas, row["Codigo_Articulo"], row["Sucursal"], row["Forecast"], row["Average"], row["ventas_last"], row["ventas_previous"], row["ventas_same_year"]) if not pd.isna(row["Codigo_Articulo"]) and not pd.isna(row["Sucursal"]) else None,
        axis=1
    )
    
    return df_forecast

# Punto de entrada
if __name__ == "__main__":
    fes = get_excecution_by_status(30)

# Filtrar registros con supply_forecast_execution_status_id = 30  #FORECAST con DFATOSK
for index, row in fes[fes["supply_forecast_execution_status_id"] == 30].iterrows():
    algoritmo = row["name"]
    name = algoritmo.split('_ALGO')[0]
    execution_id = row["id"]
    id_proveedor = row["ext_supplier_code"]
    print("Algoritmo: " + algoritmo + "  - Name: " + name + " exce_id:" + str(execution_id) + " id: Proveedor "+id_proveedor)
    
    try:
        # Actualizar el status_id a 35 Procesando Graficos....        
        update_execution(execution_id, supply_forecast_execution_status_id=35)
        print(f"Iniciando Graficación Local..... {execution_id}")
        
        # Llamar a la función que genera los gráficos y datos extendidos
        df_merged = insertar_graficos_forecast(algoritmo, name, id_proveedor)

        # Guardar el archivo CSV
        file_path = f"{folder}/{algoritmo}_Pronostico_Extendido.csv"
        df_merged.to_csv(file_path, index=False)
        print(f"Archivo guardado: {file_path}")

        # Actualizar el status_id a 40 en el DataFrame original
        fes.at[index, "supply_forecast_execution_status_id"] = 40
        # ✅ Actualizar directamente en la base de datos el estado a 40
        update_execution(execution_id, supply_forecast_execution_status_id=40)
        print(f"Estado actualizado a 40 para {execution_id}")

    except Exception as e:
        print(f"Error procesando {name}: {e}")

