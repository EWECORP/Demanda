"""
Nombre del módulo: S40_SUBIR_Forecast_Connexa.py

Descripción:
Partiendo de los datos extendidos con estado 40. El forecast está Listo, Completo y Graficado para subirlo a CONNEXA.
Se actualiza la grilla de Forecast Excecutión con los datos actualizados que resumen datos relevantes del pedido.
Forecast Valorizado Precio de Venta, a Precios de Costo y Margen potencial. Minigráfico de Tendencia de ventas.
Se utiliza estado 45 Intermedio porque el proceso es largo. Al finalizar se actualiza el estado a 40 en la base de datos.

### PROCESAR xxx_Ponostico_Extendido

1) Leer ejecuciones con Status 40.
2) Actualizar los Datos y el Minigráfico de la cabecera de ejecución.
3) Cargar datos en la tabla execuciton_excecute_result.
4) Actulizar Estado en connexa a 50 DISPONIBLE

Autor: EWE - Zeetrex
Fecha de creación: [2025-03-22]
"""

# Solo importar lo necesario desde el módulo de funciones
from funciones_forecast import (
    Open_Conn_Postgres,
    Close_Connection,
    get_excecution_by_status,
    update_execution,
    get_excecution_excecute_by_status,
    generar_grafico_base64
)

import pandas as pd # uso localmente la lectura de archivos.
import ace_tools_open as tools

from dotenv import dotenv_values
secrets = dotenv_values(".env")
folder = secrets["FOLDER_DATOS"]

# También podés importar funciones adicionales si tu módulo las necesita

def publish_excecution_results(df_forecast_ext, forecast_execution_excecute_id, supplier_id):
    print ('Comenzando a grabar el dataframe')
    for _, row in df_forecast_ext.iterrows():
        create_execution_execute_result(
            confidence_level=0.92,  # Valor por defecto ya que no está en df_meged
            error_margin=0.07,  # Valor por defecto
            expected_demand=row['Forecast'],
            average_daily_demand=row['Average'],
            lower_bound=row['Q_DIAS_STOCK'],  # Valor por defecto
            upper_bound=row['Q_VENTA_DIARIA_NORMAL'],  # Valor por defecto
            product_id=row['product_id'],
            site_id=row['site_id'],
            supply_forecast_execution_execute_id=forecast_execution_excecute_id,
            algorithm=row['algoritmo'],
            average=row['Average'],
            ext_product_code=row['Codigo_Articulo'],
            ext_site_code=row['Sucursal'],
            ext_supplier_code=row['id_proveedor'],
            forcast=row['Q_REPONER_INCLUIDO_SOBRE_STOCK'],
            graphic=row['GRAFICO'],
            quantity_stock=row['Q_TRANSF_PEND'],  # Valor por defecto
            sales_last=row['ventas_last'],
            sales_previous=row['ventas_previous'],
            sales_same_year=row['ventas_same_year'],
            supplier_id=supplier_id,
            windows=row['ventana'],
            deliveries_pending=1  # Valor por defecto
        )
    print ('--------------------------------')

def actualizar_site_ids(df_forecast_ext, conn):
    """Reemplaza site_id en df_forecast_ext con datos válidos desde fnd_site"""
    query = """
    SELECT code, name, id FROM public.fnd_site
    WHERE company_id = 'e7498b2e-2669-473f-ab73-e2c8b4dcc585'
    ORDER BY code 
    """
    stores = pd.read_sql(query, conn)
    stores = stores[pd.to_numeric(stores['code'], errors='coerce').notna()].copy()
    stores['code'] = stores['code'].astype(int)

    # Eliminar site_id anterior si ya existía
    df_forecast_ext = df_forecast_ext.drop(columns=['site_id'], errors='ignore')

    # Merge con los stores para obtener site_id
    df_forecast_ext = df_forecast_ext.merge(
        stores[['code', 'id']],
        left_on='Sucursal',
        right_on='code',
        how='left'
    ).rename(columns={'id': 'site_id'})

    # Validar valores faltantes
    missing = df_forecast_ext[df_forecast_ext['site_id'].isna()]
    if not missing.empty:
        print(f"⚠️ Faltan site_id en {len(missing)} registros")
        missing.to_csv(f"{folder}/{name}_Missing_Site_IDs.csv", index=False)
    else:
        print("✅ Todos los registros tienen site_id válido")

    return df_forecast_ext

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

    # Leer Dataframe de FORECAST EXECUTION LISTOS PARA IMPORTAR A CONNEXA (DE 40 A 50)
    fes = get_excecution_excecute_by_status(40)

    for index, row in fes[fes["supply_forecast_execution_status_id"] == 40].iterrows():
        algoritmo = row["name"]
        name = algoritmo.split('_ALGO')[0]
        execution_id = row["id"]
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

            # Agregar site_id desde fnd_site
            conn = Open_Conn_Postgres()
            df_forecast_ext = actualizar_site_ids(df_forecast_ext, conn)
            print(f"-> Se actualizaron los site_ids: {id_proveedor}, Label: {name}")
            
            # ✅ Actualizar Estado intermedio de Procesamiento....
            update_execution(execution_id, supply_forecast_execution_status_id=45)

            # Publicar en tabla de resultados
            publish_excecution_results(df_forecast_ext, forecast_execution_execute_id, supplier_id)
            print(f"-> Detalle Forecast Publicado CONNEXA: {id_proveedor}, Label: {name}")

            # Obtener precios y costos
            precio = get_precios(id_proveedor)
            precio['C_ARTICULO'] = precio['C_ARTICULO'].astype(int)
            precio['C_SUCU_EMPR'] = precio['C_SUCU_EMPR'].astype(int)

            # Merge con precios
            df_merged = df_forecast_ext.merge(
                precio,
                left_on=['Codigo_Articulo', 'Sucursal'],
                right_on=['C_ARTICULO', 'C_SUCU_EMPR'],
                how='left'
            )

            # Cálculo de métricas
            df_merged['Forecast_VENTA'] = (df_merged['Forecast'] * df_merged['I_PRECIO_VTA'] / 1000).round(2)
            df_merged['Forecast_COSTO'] = (df_merged['Forecast'] * df_merged['I_COSTO_ESTADISTICO'] / 1000).round(2)
            df_merged['MARGEN'] = (df_merged['Forecast_VENTA'] - df_merged['Forecast_COSTO']).round(2)

            # Guardar CSV actualizado
            file_path = f"{folder}/{algoritmo}_Pronostico_Extendido.csv"
            df_merged.to_csv(file_path, index=False)
            print(f"Archivo guardado: {file_path}")

            # Totales
            total_venta = df_merged['Forecast_VENTA'].sum()
            total_costo = df_merged['Forecast_COSTO'].sum()
            total_margen = df_merged['MARGEN'].sum()

            # Mini gráfico
            mini_grafico = generar_mini_grafico(folder, name)

            # Marcar como procesado en el dataframe local.
            fes.at[index, "supply_forecast_execution_status_id"] = 50

            # Actualizar en base de datos
            update_execution(
                execution_id,
                supply_forecast_execution_status_id=50,
                monthly_sales_in_millions=total_venta,
                monthly_purchases_in_millions=total_costo,
                monthly_net_margin_in_millions=total_margen,
                graphic=mini_grafico
            )
            print(f"✅ Estado actualizado a 50 para {execution_id}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error procesando {name}: {e}")
