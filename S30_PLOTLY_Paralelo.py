import traceback
import os
import time
from datetime import datetime

import pandas as pd
from dotenv import dotenv_values

from funciones_forecast import (
    get_execution_execute_by_status,
    update_execution_execute,
    generar_grafico_base64_plotly
)

secrets = dotenv_values(".env")
folder = secrets["FOLDER_DATOS"]

def procesar_item(args):
    articulo, sucursal, df_filtrado, Forecast, Average, ventas_last, ventas_previous, ventas_same_year = args
    try:
        grafico = generar_grafico_base64_plotly(
            df_filtrado, articulo, sucursal,
            Forecast, Average, ventas_last, ventas_previous, ventas_same_year
        )
        return {
            'Codigo_Articulo': articulo,
            'Sucursal': sucursal,
            'Forecast': Forecast,
            'Average': Average,
            'ventas_last': ventas_last,
            'ventas_previous': ventas_previous,
            'ventas_same_year': ventas_same_year,
            'GRAFICO': grafico
        }
    except Exception as e:
        print(f"❌ Error en {articulo}-{sucursal}: {e}")
        return None

def insertar_graficos_forecast(algoritmo, name, id_proveedor):
    print("📊 Insertando Gráficos Forecast:   " + name)
    start_time = time.time()

    path_ventas = f'{folder}/{name}_Ventas.csv'
    path_forecast = f'{folder}/{algoritmo}_Pronostico_Extendido.csv'
    path_backup = f'{folder}/{algoritmo}_Pronostico_Extendido_Con_Graficos.csv'
    path_log = f'{folder}/log_graficos_{name}.txt'

    df_ventas = pd.read_csv(path_ventas)
    df_ventas['Codigo_Articulo'] = df_ventas['Codigo_Articulo'].astype(int)
    df_ventas['Sucursal'] = df_ventas['Sucursal'].astype(int)
    df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha'])

    df_forecast = pd.read_csv(path_forecast)
    df_forecast.fillna(0, inplace=True)
    print(f"-> Datos Recuperados del CACHE: {id_proveedor}, Label: {name}")

    if os.path.exists(path_backup):
        df_backup = pd.read_csv(path_backup)
        procesados = set(zip(df_backup['Codigo_Articulo'], df_backup['Sucursal']))
        print(f"🔁 Recuperando avance previo: {len(procesados)} registros ya procesados")
    else:
        df_backup = pd.DataFrame(columns=list(df_forecast.columns) + ['GRAFICO'])
        procesados = set()

    fecha_max = df_ventas['Fecha'].max()
    nuevos = 0
    total = len(df_forecast)

    for i, row in df_forecast.iterrows():
        clave = (row['Codigo_Articulo'], row['Sucursal'])
        if clave in procesados:
            continue

        df_filt = df_ventas[
            (df_ventas['Codigo_Articulo'] == row['Codigo_Articulo']) &
            (df_ventas['Sucursal'] == row['Sucursal']) &
            (df_ventas['Fecha'] >= fecha_max - pd.Timedelta(days=50))
        ].copy()

        result = procesar_item((
            row['Codigo_Articulo'], row['Sucursal'], df_filt,
            row['Forecast'], row['Average'],
            row['ventas_last'], row['ventas_previous'], row['ventas_same_year']
        ))

        if result:
            df_backup = pd.concat([df_backup, pd.DataFrame([result])], ignore_index=True)
            nuevos += 1

            if nuevos % 5 == 0 or i == total - 1:
                df_backup.to_csv(path_backup, index=False)
                elapsed = time.time() - start_time
                avg_time = elapsed / nuevos if nuevos else 0
                remaining = avg_time * (total - nuevos)
                print(f"🖼️ Procesados {nuevos}/{total} registros - Tiempo: {round(elapsed, 2)} seg - Estimado restante: {round(remaining / 60, 2)} min")
                with open(path_log, "a", encoding="utf-8") as log:
                    log.write(f"[{datetime.now()}] {nuevos} registros procesados ({nuevos}/{total}) - Tiempo: {round(elapsed, 2)} seg - Restante estimado: {round(remaining / 60, 2)} min\n")

    df_backup.to_csv(path_backup, index=False)
    elapsed = round(time.time() - start_time, 2)
    print(f"✅ Finalizado: {name} - Total nuevos: {nuevos} - Tiempo total: {elapsed} segundos")
    with open(path_log, "a", encoding="utf-8") as log:
        log.write(f"[{datetime.now()}] FINALIZADO: {nuevos} registros nuevos - Tiempo total: {elapsed} seg\n")

    return df_backup

if __name__ == "__main__":
    fes = get_execution_execute_by_status(30)

    for index, row in fes[fes["fee_status_id"].isin([30])].iterrows():
        algoritmo = row["name"] 
        name = algoritmo.split('_ALGO')[0]
        execution_id = row["forecast_execution_id"]
        id_proveedor = row["ext_supplier_code"]
        forecast_execution_execute_id = row["forecast_execution_execute_id"]

        print(f"Algoritmo: {algoritmo}  - Name: {name}  exce_id: {execution_id}  Proveedor: {id_proveedor}")

        try:
            print(f"🛠 Marcando como 'Procesando Gráficos' para {execution_id}")
            update_execution_execute(forecast_execution_execute_id, supply_forecast_execution_status_id=35)
            print(f"🛠 Iniciando graficación para {execution_id}...")

            df_merged = insertar_graficos_forecast(algoritmo, name, id_proveedor)

            file_path = f"{folder}/{algoritmo}_Pronostico_Extendido_FINAL.csv"
            df_merged.to_csv(file_path, index=False)
            print(f"📁 Archivo guardado correctamente: {file_path}")

            update_execution_execute(forecast_execution_execute_id, supply_forecast_execution_status_id=40)
            print(f"✅ Estado actualizado a 40 para {execution_id}")

        except Exception as e:
            traceback.print_exc()
            print(f"❌ Error procesando {name}: {e}")

            log_path = os.path.join(folder, "errores_s30.log")
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{name}] ID: {execution_id} - ERROR: {str(e)}\n")

            continue
