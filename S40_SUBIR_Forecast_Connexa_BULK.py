"""
Nombre del módulo: S40_SUBIR_Forecast_Connexa.py

Descripción:
Partiendo de los datos extendidos con estado 40. El forecast está Listo, Completo y Graficado para subirlo a CONNEXA.
Se actualiza la grilla de Forecast executión con los datos actualizados que resumen datos relevantes del pedido.
Forecast Valorizado Precio de Venta, a Precios de Costo y Margen potencial. Minigráfico de Tendencia de ventas.
Se utiliza estado 45 Intermedio porque el proceso es largo. Al finalizar se actualiza el estado a 40 en la base de datos.

### PROCESAR xxx_Ponostico_Extendido

1) Leer ejecuciones con Status 40.
2) Actualizar los Datos y el Minigráfico de la cabecera de ejecución.
3) Cargar datos en la tabla execuciton_execute_result.
4) Actulizar Estado en connexa a 50 DISPONIBLE

Autor: EWE - Zeetrex
Fecha de creación: [2025-03-22]
"""

# Solo importar lo necesario desde el módulo de funciones
from funciones_forecast import (
    Open_Postgres_retry,
    id_aleatorio,
    Close_Connection,
    mover_archivos_procesados,
    actualizar_site_ids,
    get_precios,
    get_execution_execute_by_status,
    update_execution_execute,
    create_execution_execute_result,
    generar_mini_grafico,
    generar_grafico_base64,
    obtener_demora_oc,
    obtener_datos_stock
)

import pandas as pd # uso localmente la lectura de archivos.
import ace_tools_open as tools
from dotenv import dotenv_values
secrets = dotenv_values(".env")
folder = secrets["FOLDER_DATOS"]

import numpy as np

from datetime import datetime
import shutil
import os
import math

def mover_archivo(origen, destino_dir):
    if not os.path.exists(destino_dir):
        os.makedirs(destino_dir)
    destino = os.path.join(destino_dir, os.path.basename(origen))
    shutil.move(origen, destino)

def bulk_create_execution_execute_result(rows_to_insert, batch_size=500):
    if not rows_to_insert:
        print("⚠️ No hay registros para insertar.")
        return 0

    conn = Open_Postgres_retry()
    if conn is None:
        print("❌ No se pudo conectar después de varios intentos")
        return 0

    total_insertados = 0
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO public.spl_supply_forecast_execution_execute_result (
                id, expected_demand, "timestamp", product_id, site_id, supply_forecast_execution_execute_id, 
                algorithm, average, ext_product_code, ext_site_code, ext_supplier_code, forcast, graphic, 
                quantity_stock, sales_last, sales_previous, sales_same_year, supplier_id, windows, 
                deliveries_pending, quantity_confirmed, approved, base_purchase_price, distribution_unit, 
                layer_pallet, number_layer_pallet, purchase_unit, sales_price, statistic_base_price, 
                window_sales_days
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        total_batches = math.ceil(len(rows_to_insert) / batch_size)

        for i in range(total_batches):
            start = i * batch_size
            end = start + batch_size
            batch = rows_to_insert[start:end]
            cur.executemany(query, batch)
            conn.commit()
            total_insertados += len(batch)
            print(f"✅ Batch {i+1}/{total_batches} insertado con {len(batch)} registros.")

        cur.close()
        return total_insertados

    except Exception as e:
        print(f"❌ Error en bulk_create_execution_execute_result: {e}")
        conn.rollback()
        return total_insertados
    finally:
        Close_Connection(conn)

def publicar_forecast_a_connexa(df_forecast_ext, execution_id, id_proveedor, supplier_id, folder, name, batch_size=500):
    errores = []
    rows_to_insert = []

    for i, row in df_forecast_ext.iterrows():
        try:
            if pd.isna(row['product_id']) or pd.isna(row['site_id']):
                raise ValueError("Falta product_id o site_id")

            id_result = id_aleatorio()
            timestamp = datetime.utcnow()

            fila = (
                id_result,
                row['Forecast'],
                timestamp,
                row['product_id'],
                row['site_id'],
                execution_id,
                row['algoritmo'],
                row['Average'],
                row['Codigo_Articulo'],
                row['Sucursal'],
                str(id_proveedor),
                row['Forecast'],
                row['grafico'],
                row['Stock_Unidades'],
                row['ventas_last'],
                row['ventas_previous'],
                row['ventas_same_year'],
                str(supplier_id),
                row['ventana'],
                row.get('Pedidos_Demorados', 0),
                row['Forecast'],
                True,
                row.get('Costo', 0),
                row.get('Unidad_Distribucion', 'UN'),
                row.get('Capas_Pallet', 1),
                row.get('Unidades_x_Capa', 1),
                row.get('Unidad_Compra', 'UN'),
                row.get('Precio', 0),
                row.get('Costo_Estadistico', 0),
                row.get('stock_days', 0)
            )
            rows_to_insert.append(fila)

        except Exception as e:
            print(f"❌ Error preparando fila {i+1}/{len(df_forecast_ext)} - Artículo {row['Codigo_Articulo']}: {e}")
            errores.append(i)

    if errores:
        print(f"❌ Publicación abortada: errores en {len(errores)} registros. Archivos no movidos.")
        return

    total_insertados = bulk_create_execution_execute_result(rows_to_insert, batch_size=batch_size)

    if total_insertados == len(rows_to_insert):
        print("✅ Publicación completa. Moviendo archivos...")
        mover_archivo(f"{folder}/{name}_Pronostico_Extendido_FINAL.csv", "data/procesado/")
        mover_archivo(f"{folder}/{name}_Pronostico_Extendido_Con_Graficos.csv", "data/procesado/")
        mover_archivo(f"{folder}/{name}_Solicitudes_Compra.csv", "data/procesado/")
        print(f"📁 Archivos movidos correctamente para {name}")
    else:
        print("⚠️ Inserción parcial. Archivos NO fueron movidos.")
