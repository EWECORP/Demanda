"""
Nombre del módulo: S30_GENERA_Grafico_Detalle.py

Descripción:
Partiendo de los datos extendidos con estado 30, se generan los gráficos de detalle para cada artículo y sucursal.
Se guarda el archivo CSV con los datos extendidos y los gráficos en formato base64.
Utiliza estad intermedio 35 miestras está graficando. Al finalizar se actualiza el estado a 40 en la base de datos.

Autor: EWE - Zeetrex
Fecha de creación: [2025-03-22]
"""
import traceback
import os

# Solo importar lo necesario desde el módulo de funciones
from funciones_forecast import (
    get_execution_by_status,
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
    print("Insertando Gráficos Forecast:   " + name)    
    # Recuperar Historial de Ventas
    df_ventas = pd.read_csv(f'{folder}/{name}_Ventas.csv')
    df_ventas['Codigo_Articulo']= df_ventas['Codigo_Articulo'].astype(int)
    df_ventas['Sucursal']= df_ventas['Sucursal'].astype(int)
    df_ventas['Fecha']= pd.to_datetime(df_ventas['Fecha'])

    # Recuperando Forecast Calculado
    df_forecast = pd.read_csv(f'{folder}/{algoritmo}_Pronostico_Extendido.csv')
    df_forecast.fillna(0)   # Por si se filtró algún missing value
    print(f"-> Datos Recuperados del CACHE: {id_proveedor}, Label: {name}")
    
    # Agregar la nueva columna de gráficos en df_forecast Iterando sobre todo el DATAFRAME
    df_forecast["GRAFICO"] = df_forecast.apply(
        lambda row: generar_grafico_base64(df_ventas, row["Codigo_Articulo"], row["Sucursal"], row["Forecast"], row["Average"], row["ventas_last"], row["ventas_previous"], row["ventas_same_year"]) if not pd.isna(row["Codigo_Articulo"]) and not pd.isna(row["Sucursal"]) else None,
        axis=1
    )
    print ("Fin Graficos del proveeodr")
    return df_forecast

# Punto de entrada
if __name__ == "__main__":
    fes = get_execution_by_status(30)

# Filtrar registros con supply_forecast_execution_status_id = 30  #FORECAST con DFATOSK
for index, row in fes[fes["supply_forecast_execution_status_id"].isin([30])].iterrows():
    algoritmo = row["name"]
    name = algoritmo.split('_ALGO')[0]
    execution_id = row["id"]
    id_proveedor = row["ext_supplier_code"]

    print(f"Algoritmo: {algoritmo}  - Name: {name}  exce_id: {execution_id}  Proveedor: {id_proveedor}")

    try:
        # Estado intermedio: 35 (procesando gráficos)
        print(f"🛠 Marcando como 'Procesando Gráficos' para {execution_id}")
        update_execution(execution_id, supply_forecast_execution_status_id=35)
        print(f"🛠 Iniciando graficación para {execution_id}...")

        # Generación del dataframe extendido con gráficos
        df_merged = insertar_graficos_forecast(algoritmo, name, id_proveedor)

        # Guardar el CSV con datos extendidos y gráficos
        file_path = f"{folder}/{algoritmo}_Pronostico_Extendido.csv"
        df_merged.to_csv(file_path, index=False)
        print(f"📁 Archivo guardado correctamente: {file_path}")

        # ✅ Solo si todo fue exitoso, actualizamos el estado a 40
        update_execution(execution_id, supply_forecast_execution_status_id=40)
        print(f"✅ Estado actualizado a 40 para {execution_id}")

    except Exception as e:
        traceback.print_exc()
        print(f"❌ Error procesando {name}: {e}")
        
        log_path = os.path.join(folder, "errores_s30.log")
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{name}] ID: {execution_id} - ERROR: {str(e)}\n")
        
        continue


