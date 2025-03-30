"""
Nombre del módulo S50_ACTUALIZAR_Header_Forecast_Connexa.py

Descripción:
Por los cambios en las entidades y el ajuste del color de los gráficos. 
Aquí se podrán corregir futuross resúmenes de Dias_Stock, OTIF,OC_Atrasos.

Autor: EWE - Zeetrex
Fecha de creación: [2025-03-22]
"""

# Solo importar lo necesario desde el módulo de funciones
from funciones_forecast import (
    mover_archivos_procesados,
    get_precios,
    get_execution_execute_by_status,
    update_execution_execute,
    generar_mini_grafico
)

import pandas as pd # uso localmente la lectura de archivos.
import ace_tools_open as tools
from dotenv import dotenv_values
secrets = dotenv_values(".env")
folder = secrets["FOLDER_DATOS"]

# También podés importar funciones adicionales si tu módulo las necesita

import time
from datetime import datetime
import os
from random import randint
import shutil
import numpy as np

def mover_archivos_procesados(algoritmo, folder):
    destino = os.path.join(folder, "procesado")
    os.makedirs(destino, exist_ok=True)  # Crea la carpeta si no existe

    for archivo in os.listdir(folder):
        if archivo.startswith(algoritmo):
            origen = os.path.join(folder, archivo)
            destino_final = os.path.join(destino, archivo)
            shutil.move(origen, destino_final)
            print(f"📁 Archivo movido: {archivo} → {destino_final}")

# --------------------------------
# Punto de Entrada del Módulo
# --------------------------------

if __name__ == "__main__":

    # Leer Dataframe de FORECAST EXECUTION  de Estado 50 y Actualizar HEADER
    fes = get_execution_execute_by_status(50)
    
    for index, row in fes[fes["fee_status_id"] == 50].iterrows():
        algoritmo = row["name"]
        name = algoritmo.split('_ALGO')[0]
        execution_id = row["forecast_execution_id"]
        id_proveedor = row["ext_supplier_code"]
        forecast_execution_execute_id = row["forecast_execution_execute_id"]
        supplier_id = row["supplier_id"]

        print(f"Algoritmo: {algoritmo}  - Name: {name} exce_id: {forecast_execution_execute_id} id: Proveedor {id_proveedor}")
        print(f"supplier-id: {supplier_id} ----------------------------------------------------")

        try:
            # Leer forecast extendido
            df_forecast_ext = pd.read_csv(f'{folder}/{algoritmo}_Pronostico_Extendido.csv')
            df_forecast_ext['Codigo_Articulo'] = df_forecast_ext['Codigo_Articulo'].astype(int)
            df_forecast_ext['Sucursal'] = df_forecast_ext['Sucursal'].astype(int)
            df_forecast_ext.fillna(0, inplace=True)
            print(f"-> Datos Recuperados del CACHE: {id_proveedor}, Label: {name}")
            print("❗Filas con site_id inválido:", df_forecast_ext['site_id'].isna().sum())
            print("❗Filas con product_id inválido:", df_forecast_ext['product_id'].isna().sum())

            # Hacer merge solo si no existen las columnas de precios y costos
            if 'I_PRECIO_VTA' not in df_forecast_ext.columns or 'I_COSTO_ESTADISTICO' not in df_forecast_ext.columns:
                print(f"❌ ERROR: Falta la columna requerida '{col}' procedemos a actualizar {id_proveedor}")
                precio = get_precios(id_proveedor)
                precio['C_ARTICULO'] = precio['C_ARTICULO'].astype(int)
                precio['C_SUCU_EMPR'] = precio['C_SUCU_EMPR'].astype(int)

                df_forecast_ext = df_forecast_ext.merge(
                    precio,
                    left_on=['Codigo_Articulo', 'Sucursal'],
                    right_on=['C_ARTICULO', 'C_SUCU_EMPR'],
                    how='left'
                )
            else:
                print(f"⚠️ El DataFrame ya contiene precios y costos. Merge evitado para {id_proveedor}")
            
            # Verificar columnas necesarias después del merge
            columnas_requeridas = ['I_PRECIO_VTA', 'I_COSTO_ESTADISTICO']
            for col in columnas_requeridas:
                if col not in df_forecast_ext.columns:
                    print(f"❌ ERROR: Falta la columna requerida '{col}' en df_forecast_ext para el proveedor {id_proveedor}")
                    df_forecast_ext.to_csv(f"{folder}/{algoritmo}_ERROR_MERGE.csv", index=False)
                    raise ValueError(f"Column '{col}' missing in df_forecast_ext. No se puede continuar.")

            # Cálculo de métricas x Línea en miles
            df_forecast_ext['Forecast_VENTA'] = (df_forecast_ext['Forecast'] * df_forecast_ext['I_PRECIO_VTA'] / 1000).round(2)
            df_forecast_ext['Forecast_COSTO'] = (df_forecast_ext['Forecast'] * df_forecast_ext['I_COSTO_ESTADISTICO'] / 1000).round(2)
            df_forecast_ext['MARGEN'] = (df_forecast_ext['Forecast_VENTA'] - df_forecast_ext['Forecast_COSTO'])

            # Asegurar que los valores son del tipo float (nativo de Python)
            total_venta = float(round(df_forecast_ext['Forecast_VENTA'].sum() / 1000, 2))
            total_costo = float(round(df_forecast_ext['Forecast_COSTO'].sum() / 1000, 2))
            total_margen = float(round(df_forecast_ext['MARGEN'].sum() / 1000, 2))
            total_productos = df_forecast_ext['Codigo_Articulo'].nunique()
            total_unidades = float(round(df_forecast_ext['Forecast'].sum() , 0))

            # Mini gráfico
            mini_grafico = generar_mini_grafico(folder, name)
            
            ############# SIMULAR VALORES
            days = randint(0,75), # Simulación de stock_days entre 0 y 75
                
            # Definición de condiciones
            condiciones = [
                days > 30,
                (days > 10) & (days <= 30),
                days <= 10
            ]
            colores = ['green', 'yellow', 'red']
            
            semaforo = np.select(condiciones, colores)

            # Actualizar en base de datos            
            update_execution_execute(
                forecast_execution_execute_id,
                supply_forecast_execution_status_id=50,
                monthly_sales_in_millions=total_venta,
                monthly_purchases_in_millions=total_costo,
                monthly_net_margin_in_millions=total_margen,
                graphic=mini_grafico,
                total_products=total_productos,
                total_units=total_unidades,
                otif = randint(70, 100),  # Simulación de OTIF entre 70 y 100
                stock_days = days,
                sotck_days_colors = semaforo,
                maximum_backorder_days = randint(0, 45) # Simulación de oc_delay entre 0 y 45
                
            )
            
            print(f"✅ Estado actualizado a 50 para {execution_id}")
            
            # ✅ Morver Archivo a carpeta de Procesado ....
            mover_archivos_procesados(algoritmo, folder)
            print(f"✅ Archivo movido a Procesado: {algoritmo}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error procesando {name}: {e}")
            
# --------------------------------