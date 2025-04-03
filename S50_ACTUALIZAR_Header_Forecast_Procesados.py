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
    generar_mini_grafico,
    Open_Connection,
    Close_Connection
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
            
def obtener_datos_stock(id_proveedor, etiqueta):
    secrets = dotenv_values(".env")   # Connection String from .env
    folder = secrets["FOLDER_DATOS"]
    
    #  Intento recuperar datos cacheados
    try:         
        print(f"-> Generando datos para ID: {id_proveedor}, Label: {etiqueta}")
        # Configuración de conexión
        conn = Open_Connection()
        
        # ----------------------------------------------------------------
        # FILTRA solo PRODUCTOS HABILITADOS y Traer datos de STOCK y PENDIENTES desde PRODUCCIÓN
        # ----------------------------------------------------------------
        query = f"""              
        SELECT A.[C_PROVEEDOR_PRIMARIO] as Codigo_Proveedor
            ,S.[C_ARTICULO] as Codigo_Articulo
            ,S.[C_SUCU_EMPR] as Codigo_Sucursal
            ,S.[I_PRECIO_VTA] as Precio_Venta
            ,S.[I_COSTO_ESTADISTICO] as Precio_Costo
            ,S.[Q_FACTOR_VTA_SUCU] as Factor_Venta
            ,ST.Q_UNID_ARTICULO + ST.Q_PESO_ARTICULO AS Stock_Unidades-- Stock Cierre Dia Anterior
            ,(R.[Q_VENTA_30_DIAS] + R.[Q_VENTA_15_DIAS]) * S.[Q_FACTOR_VTA_SUCU] AS Venta_Unidades_30_Dias -- OJO convertida desde BULTOS DIARCO
                    
            ,(ST.Q_UNID_ARTICULO + ST.Q_PESO_ARTICULO)* S.[I_COSTO_ESTADISTICO] AS Stock_Valorizado-- Stock Cierre Dia Anterior
            ,(R.[Q_VENTA_30_DIAS] + R.[Q_VENTA_15_DIAS]) * S.[Q_FACTOR_VTA_SUCU] * S.[I_COSTO_ESTADISTICO] AS Venta_Valorizada

            ,ROUND(((ST.Q_UNID_ARTICULO + ST.Q_PESO_ARTICULO)* S.[I_COSTO_ESTADISTICO]) / 	
                ((R.[Q_VENTA_30_DIAS] + R.[Q_VENTA_15_DIAS]+0.0001) * S.[Q_FACTOR_VTA_SUCU] * S.[I_COSTO_ESTADISTICO] ),0) * 30
                AS Dias_Stock
                    
            ,S.[F_ULTIMA_VTA]
            ,S.[Q_VTA_ULTIMOS_15DIAS] * S.[Q_FACTOR_VTA_SUCU] AS VENTA_UNIDADES_1Q -- OJO esto está en BULTOS DIARCO
            ,S.[Q_VTA_ULTIMOS_30DIAS] * S.[Q_FACTOR_VTA_SUCU] AS VENTA_UNIDADES_2Q -- OJO esto está en BULTOS DIARCO
                
        FROM [DIARCOP001].[DiarcoP].[dbo].[T051_ARTICULOS_SUCURSAL] S
        INNER JOIN [DIARCOP001].[DiarcoP].[dbo].[T050_ARTICULOS] A
            ON A.[C_ARTICULO] = S.[C_ARTICULO]
        LEFT JOIN [DIARCOP001].[DiarcoP].[dbo].[T060_STOCK] ST
            ON ST.C_ARTICULO = S.[C_ARTICULO] 
            AND ST.C_SUCU_EMPR = S.[C_SUCU_EMPR]
        LEFT JOIN [DIARCOP001].[DiarcoP].[dbo].[T710_ESTADIS_REPOSICION] R
            ON R.[C_ARTICULO] = S.[C_ARTICULO]
            AND R.[C_SUCU_EMPR] = S.[C_SUCU_EMPR]

        WHERE S.[M_HABILITADO_SUCU] = 'S' -- Permitido Reponer
            AND A.M_BAJA = 'N'  -- Activo en Maestro Artículos
            AND A.[C_PROVEEDOR_PRIMARIO] = {id_proveedor} -- Solo del Proveedor
                        
        ORDER BY S.[C_ARTICULO],S.[C_SUCU_EMPR];
        """
        # Ejecutar la consulta SQL
        df_stock = pd.read_sql(query, conn)
        file_path = f'{folder}/{etiqueta}_Stock.csv'
        df_stock['Codigo_Proveedor']= df_stock['Codigo_Proveedor'].astype(int)
        df_stock['Codigo_Articulo']= df_stock['Codigo_Articulo'].astype(int)
        df_stock['Codigo_Sucursal']= df_stock['Codigo_Sucursal'].astype(int)
        df_stock.fillna(0, inplace= True)
        # df_stock.to_csv(file_path, index=False, encoding='utf-8')        
        print(f"---> Datos de STOCK guardados: {file_path}")
        return df_stock
    except Exception as e:
        print(f"Error en get_execution: {e}")
        return None
    finally:
        Close_Connection(conn)


def obtener_demora_oc(id_proveedor, etiqueta):
    secrets = dotenv_values(".env")   # Connection String from .env
    folder = secrets["FOLDER_DATOS"]
    
    #  Intento recuperar datos cacheados
    try:         
        print(f"-> Generando datos para ID: {id_proveedor}, Label: {etiqueta}")
        # Configuración de conexión
        conn = Open_Connection()
        
        # ----------------------------------------------------------------
        # FILTRA solo PRODUCTOS HABILITADOS y Traer datos de STOCK y PENDIENTES desde PRODUCCIÓN
        # ----------------------------------------------------------------
        query = f"""              
        SELECT  [C_OC]
            ,[U_PREFIJO_OC]
            ,[U_SUFIJO_OC]      
            ,[U_DIAS_LIMITE_ENTREGA]
            , DATEADD(DAY, [U_DIAS_LIMITE_ENTREGA], [F_ENTREGA]) as FECHA_LIMITE
            , DATEDIFF (DAY, DATEADD(DAY, [U_DIAS_LIMITE_ENTREGA], [F_ENTREGA]), GETDATE()) as Demora
            ,[C_PROVEEDOR] as Codigo_Proveedor
            ,[C_SUCU_COMPRA] as Codigo_Sucursal
            ,[C_SUCU_DESTINO]
            ,[C_SUCU_DESTINO_ALT]
            ,[C_SITUAC]
            ,[F_SITUAC]
            ,[F_ALTA_SIST]
            ,[F_EMISION]
            ,[F_ENTREGA]    
            ,[C_USUARIO_OPERADOR]    
            
        FROM [DIARCOP001].[DiarcoP].[dbo].[T080_OC_CABE]  
        WHERE [C_SITUAC] = 1
        AND C_PROVEEDOR = {id_proveedor} 
        AND DATEADD(DAY, [U_DIAS_LIMITE_ENTREGA], [F_ENTREGA]) < GETDATE();
        """
        # Ejecutar la consulta SQL
        df_demoras = pd.read_sql(query, conn)
        df_demoras['Codigo_Proveedor']= df_demoras['Codigo_Proveedor'].astype(int)
        df_demoras['Codigo_Sucursal']= df_demoras['Codigo_Sucursal'].astype(int)
        df_demoras['Demora']= df_demoras['Demora'].astype(int)
        df_demoras.fillna(0, inplace= True)         
        print(f"---> Datos de OC DEMORADAS Recuperados: {etiqueta}")
        return df_demoras
    except Exception as e:
        print(f"Error en get_execution: {e}")
        return None
    finally:
        Close_Connection(conn)


# --------------------------------
# Punto de Entrada del Módulo
# --------------------------------

if __name__ == "__main__":

    # Leer Dataframe de FORECAST EXECUTION  de Estado 50 y Actualizar HEADER
    fes = get_execution_execute_by_status(45)
    
    for index, row in fes[fes["fee_status_id"] == 45].iterrows():
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
            
            # DATOS COMPLEMENTARIOS
            df_stock = obtener_datos_stock(id_proveedor= id_proveedor, etiqueta= algoritmo )
            total_stock_valorizado = float(round(df_stock['Stock_Valorizado'].sum() / 1000000, 2))
            total_venta_valorizada = float(round(df_stock['Venta_Valorizada'].sum() / 1000000, 2))
            days= int( total_stock_valorizado / total_venta_valorizada * 30 )
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
                sotck_days = days, # Viene de la Nueva Rutina              
                sotck_days_colors = semaforo, # Nueva Rutina
                maximum_backorder_days = maximo_atraso_oc, # Calcula Mäxima Demora
                contains_breaks = quiebres  # ICONO de FALTANTES
                
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