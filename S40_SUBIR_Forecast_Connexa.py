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
    Open_Conn_Postgres,
    mover_archivos_procesados,
    actualizar_site_ids,
    get_precios,
    get_execution_execute_by_status,
    update_execution_execute,
    generar_mini_grafico,
    obtener_demora_oc,
    Open_Postgres_retry,
    id_aleatorio,
    Close_Connection,
    obtener_datos_stock
)

import pandas as pd # uso localmente la lectura de archivos.
import ace_tools_open as tools
from dotenv import dotenv_values
secrets = dotenv_values(".env")
folder = secrets["FOLDER_DATOS"]

import numpy as np
import json

# También podés importar funciones adicionales si tu módulo las necesita

from random import randint
from datetime import datetime
import shutil
import os
import math
import time
from functools import wraps

def medir_tiempo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n🕒 Iniciando ejecución de {func.__name__}...")
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fin = time.time()
        duracion = fin - inicio
        print(f"✅ Finalizó {func.__name__} en {duracion:.2f} segundos.\n")
        return resultado
    return wrapper

def mover_archivo(origen, destino_dir):
    if not os.path.exists(destino_dir):
        os.makedirs(destino_dir)
    destino = os.path.join(destino_dir, os.path.basename(origen))
    shutil.move(origen, destino)
    

# Decorador para medir tiempo de ejecución
def medir_tiempo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\n🕒 Iniciando ejecución de {func.__name__}...")
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fin = time.time()
        duracion = fin - inicio
        print(f"✅ Finalizó {func.__name__} en {duracion:.2f} segundos.\n")
        return resultado
    return wrapper

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
                window_sales_days, units_reserved, blocked_for_purchase, sales_previous15days_period, sales_recent15days_period
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

@medir_tiempo
def publicar_forecast_a_connexa(df_forecast_ext, forecast_execution_execute_id, id_proveedor, supplier_id, folder, algoritmo, batch_size=500):
    errores = []
    rows_to_insert = []

    for i, row in df_forecast_ext.iterrows():
        try:
            if pd.isna(row['product_id']) or pd.isna(row['site_id']):
                raise ValueError("Falta product_id o site_id")

            id_result = id_aleatorio()
            timestamp = datetime.utcnow()
            
            try:
                grafico_serializado = json.dumps(row['GRAFICO'])  # Asegura conversión a str JSON
                if len(grafico_serializado) > 100_000:
                    raise ValueError("El gráfico excede el tamaño permitido")
            except Exception as e:
                print(f"⚠️ Error serializando 'GRAFICO' para artículo {row['Codigo_Articulo']}: {e}")
                errores.append(i)
                continue
            
            fila = (
                #   id, expected_demand, "timestamp", product_id, site_id, supply_forecast_execution_execute_id, 
                id_result,
                row['Forecast'],
                timestamp,
                row['product_id'],
                row['site_id'],
                forecast_execution_execute_id,
                #     algorithm, average, ext_product_code, ext_site_code, ext_supplier_code, forcast, graphic, 
                row['algoritmo'],
                row['Average'],
                row['Codigo_Articulo'],
                row['Sucursal'],
                id_proveedor,
                row['Q_REPONER_INCLUIDO_SOBRE_STOCK'],
                grafico_serializado,    # row['GRAFICO'],
                #     quantity_stock, sales_last, sales_previous, sales_same_year, supplier_id, windows,
                row.get('Q_STOCK_UNIDADES', 0) + row.get('Q_STOCK_PESO', 0),
                row['ventas_last'],
                row['ventas_previous'],
                row['ventas_same_year'],
                str(supplier_id),
                row['ventana'],
                #     deliveries_pending, quantity_confirmed, approved, base_purchase_price, distribution_unit, 
                row.get('Q_TRANSF_PEND',0) + row.get('Q_TRANSF_EN_PREP',0), 
                0,
                False,
                row.get('I_LISTA_CALCULADO', 0),
                row.get('Q_FACTOR_VTA_SUCU',1),
                row.get('U_PISO_PALETIZADO', 1),
                #     layer_pallet, number_layer_pallet, purchase_unit, sales_price, statistic_base_price,
                row.get('U_ALTURA_PALETIZADO', 1),
                row.get('Q_FACTOR_PROVEEDOR', 1),
                row.get('I_PRECIO_VTA', 0),
                row.get('I_COSTO_ESTADISTICO', 0),
                #     window_sales_days
                row.get('Q_DIAS_STOCK', 0),
                row.get('Q_TRANSF_PEND', 0),  # <-- CERO FIJO PARA units_reserved
                row.get('M_HABILITADO_SUCU', 'S').strip().upper() == 'N',  # Bloqueado para compra
                row.get('Q_VTA_ULTIMOS_30DIAS', 0),  # Primeros 15
                row.get('Q_VTA_ULTIMOS_15DIAS', 0)   # Ultimos 15
            )
        
            if len(fila) != 34:
                print(f"❌ Fila malformada en registro {i+1}: contiene {len(fila)} columnas (esperadas: 34)")
                print(fila)
                continue
            
            if any(isinstance(v, (list, dict)) for v in fila):
                print(f"⚠️ Fila con estructura inválida: {fila}")
                continue

            rows_to_insert.append(fila)

        except Exception as e:
            print(f"❌ Error preparando fila {i+1}/{len(df_forecast_ext)} - Artículo {row['Codigo_Articulo']}: {e}")
            errores.append(i)

    if errores:
        print(f"❌ Publicación abortada: errores en {len(errores)} registros. Archivos no movidos.")
        return

    total_insertados = bulk_create_execution_execute_result(rows_to_insert, batch_size=batch_size)

    if total_insertados == len(rows_to_insert):
        print("🎯 Publicación finalizada.")
        print("✅ Publicación completa. Moviendo archivos...")
        mover_archivos_procesados(algoritmo, folder)
        print(f"📁 Archivos movidos correctamente para {algoritmo}")
    else:
        print("⚠️ Inserción parcial. Archivos NO fueron movidos.")

def actualizar_site_ids(df_forecast_ext, conn, name):
    """
    Reemplaza site_id en df_forecast_ext con datos válidos desde fnd_site.
    Asegura que no haya conflictos de columnas durante el merge.
    """
    query = """
    SELECT code, name, id FROM public.fnd_site
    WHERE company_id = 'e7498b2e-2669-473f-ab73-e2c8b4dcc585'
    ORDER BY code
    """
    stores = pd.read_sql(query, conn)

    # Asegurar que el campo 'code' sea numérico y entero
    stores = stores[pd.to_numeric(stores['code'], errors='coerce').notna()].copy()
    stores['code'] = stores['code'].astype(int)

    # Eliminar columna 'site_id' si ya existe
    df_forecast_ext = df_forecast_ext.drop(columns=['site_id'], errors='ignore')

    # Eliminar columna 'code' si ya existe en df_forecast_ext para evitar colisión en el merge
    if 'code' in df_forecast_ext.columns:
        df_forecast_ext = df_forecast_ext.drop(columns=['code'])

    # Realizar el merge con stores (fnd_site) para traer el site_id
    df_forecast_ext = df_forecast_ext.merge(
        stores[['code', 'id']],
        left_on='Sucursal',
        right_on='code',
        how='left'
    ).rename(columns={'id': 'site_id'})

    # Validar valores faltantes de site_id
    missing = df_forecast_ext[df_forecast_ext['site_id'].isna()]
    if not missing.empty:
        print(f"⚠️ Faltan site_id en {len(missing)} registros")
        missing.to_csv(f"{folder}/{name}_Missing_Site_IDs.csv", index=False)
    else:
        print("✅ Todos los registros tienen site_id válido")

    return df_forecast_ext


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

    # Leer Dataframe de FORECAST EXECUTION LISTOS PARA IMPORTAR A CONNEXA (DE 40 A 50)
    fes = get_execution_execute_by_status(40)
    
    for index, row in fes[fes["fee_status_id"] == 40].iterrows():
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
            df_forecast_ext = pd.read_csv(f'{folder}/{algoritmo}_Pronostico_Extendido_FINAL.csv')
            df_forecast_ext['Codigo_Articulo'] = df_forecast_ext['Codigo_Articulo'].astype(int)
            df_forecast_ext['Sucursal'] = df_forecast_ext['Sucursal'].astype(int)
            df_forecast_ext.fillna(0, inplace=True)
            print(f"-> Datos Recuperados del CACHE: {id_proveedor}, Label: {name}")
            print("❗Filas con site_id inválido:", df_forecast_ext['site_id'].isna().sum())
            print("❗Filas con product_id inválido:", df_forecast_ext['product_id'].isna().sum())

            # Agregar site_id desde fnd_site
            conn = Open_Conn_Postgres()
            df_forecast_ext = actualizar_site_ids(df_forecast_ext, conn, name)
            print(f"-> Se actualizaron los site_ids: {id_proveedor}, Label: {name}")
            
            # Verificar columnas necesarias después del merge
            columnas_requeridas = ['I_PRECIO_VTA', 'I_COSTO_ESTADISTICO']
            for col in columnas_requeridas:
                if col not in df_forecast_ext.columns:
                    print(f"❌ ERROR: Falta la columna requerida '{col}' en df_forecast_ext para el proveedor {id_proveedor}")
                    df_forecast_ext.to_csv(f"{folder}/{algoritmo}_ERROR_MERGE.csv", index=False)
                    raise ValueError(f"Column '{col}' missing in df_forecast_ext. No se puede continuar.")
            
            # Hacer merge solo si no existen las columnas de precios y costos
            if 'I_PRECIO_VTA' not in df_forecast_ext.columns or 'I_COSTO_ESTADISTICO' not in df_forecast_ext.columns:
                #print(f"❌ ERROR: Falta la columna requerida '{col}' procedemos a actualizar {id_proveedor}")
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

            # Cálculo de métricas x Línea en miles
            df_forecast_ext['Forecast_VENTA'] = (df_forecast_ext['Forecast'] * df_forecast_ext['I_PRECIO_VTA'] / 1000).round(2)
            df_forecast_ext['Forecast_COSTO'] = (df_forecast_ext['Forecast'] * df_forecast_ext['I_COSTO_ESTADISTICO'] / 1000).round(2)
            df_forecast_ext['MARGEN'] = (df_forecast_ext['Forecast_VENTA'] - df_forecast_ext['Forecast_COSTO'])

            # Guardar CSV actualizado
            file_path = f"{folder}/{algoritmo}_Pronostico_Extendido_FINAL.csv"
            df_forecast_ext.to_csv(file_path, index=False)
            print(f"Archivo guardado: {file_path}")
            
            # Asegurar que los valores son del tipo float (nativo de Python)
            total_venta = float(round(df_forecast_ext['Forecast_VENTA'].sum() / 1000, 2))
            total_costo = float(round(df_forecast_ext['Forecast_COSTO'].sum() / 1000, 2))
            total_margen = float(round(df_forecast_ext['MARGEN'].sum() / 1000, 2))
            total_productos = df_forecast_ext['Codigo_Articulo'].nunique()
            total_unidades = float(round(df_forecast_ext['Forecast'].sum() , 0))

            # Mini gráfico
            mini_grafico = generar_mini_grafico(folder, name)

            # DATOS COMPLEMENTARIOS
            df_stock = obtener_datos_stock(id_proveedor= id_proveedor, etiqueta= algoritmo )
            if df_stock is None or df_stock.empty:
                print(f"⚠️ No se pudo recuperar datos de stock para el proveedor {id_proveedor}. Se omite cálculo de stock.")
                total_stock_valorizado = 0
                total_venta_valorizada = 0
                days = 0
                semaforo = 'white'
            else:
                total_stock_valorizado = float(round(df_stock['Stock_Valorizado'].sum() / 1000000, 2))
                total_venta_valorizada = float(round(df_stock['Venta_Valorizada'].sum() / 1000000, 2))
                if total_venta_valorizada == 0:
                    days = 0
                else:
                    days = int(total_stock_valorizado / total_venta_valorizada * 30)

            # Condiciones Dias de STOCK
            if days > 30:
                semaforo= 'green'
            elif 10 < days <= 30:
                semaforo ='yellow'
            elif days <= 10:
                semaforo ='red'
            else:
                semaforo = 'white' # Valor predeterminado

            # DEMORA de OC
            df_demora = obtener_demora_oc(id_proveedor= id_proveedor, etiqueta= algoritmo )
            if df_demora.empty:  # Verifica si el DataFrame está vacío
                maximo_atraso_oc = 0
            else:
                maximo_atraso_oc = int(round(df_demora['Demora'].max()))
            
            # ARTICULOS FALTANTES
            articulos_faltantes = df_stock[df_stock["Stock_Unidades"] == 0]["Codigo_Articulo"].nunique()
            if articulos_faltantes > 5:
                quiebres= 'R'
            elif 1 < articulos_faltantes <= 5:
                quiebres ='Y'
            elif articulos_faltantes <= 1:
                quiebres ='G'
            else:
                quiebres = 'white' # Valor predeterminado
                                    
            update_execution_execute(
                forecast_execution_execute_id,
                supply_forecast_execution_status_id=45,
                monthly_sales_in_millions=total_venta,
                monthly_purchases_in_millions=total_costo,
                monthly_net_margin_in_millions=total_margen,
                graphic=mini_grafico,
                total_products=total_productos,
                total_units=total_unidades,
                otif = randint(70, 100),  # Simulación de OTIF entre 70 y 100
                sotck_days = days, # Viene de la Nueva Rutina              
                sotck_days_colors = semaforo, # Nueva Rutina
                maximum_backorder_days = maximo_atraso_oc, # Calcula Mäxima Demora
                contains_breaks = quiebres  # ICONO de FALTANTES
            )
            
            ### NUEVA RUTINA BULK            
            publicar_forecast_a_connexa(df_forecast_ext, forecast_execution_execute_id, id_proveedor, supplier_id, folder, algoritmo, batch_size=500)
            print(f"-> Detalle Forecast Publicado CONNEXA: {id_proveedor}, Label: {name}")
                        
            # ✅ Actualizar Estado intermedio de Procesamiento....
            update_execution_execute(forecast_execution_execute_id, supply_forecast_execution_status_id=50)
            print(f"✅ Estado actualizado a 50 para {execution_id}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error procesando {name}: {e}")
            
# --------------------------------