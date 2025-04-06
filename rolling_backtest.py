
import pandas as pd
import numpy as np

def rolling_backtest(df_ventas, df_forecast, sku, sucursal, algoritmo, window_size=52, horizon=4, step=1):
    '''
    Realiza backtesting con rolling window para un SKU, sucursal y algoritmo específico.
    
    Parámetros:
        df_ventas: DataFrame con columnas ['Codigo_Articulo', 'Sucursal', 'Fecha', 'Unidades']
        df_forecast: DataFrame con columnas ['Codigo_Articulo', 'Sucursal', 'Semana', 'algoritmo', 'Forecast']
        sku: código del artículo
        sucursal: código de la sucursal
        algoritmo: nombre del algoritmo (ej: 'ALGO_01')
        window_size: tamaño de la ventana (en semanas)
        horizon: horizonte de predicción (en semanas)
        step: cantidad de semanas que se desliza la ventana
    
    Devuelve:
        DataFrame con errores por cada ventana simulada
    '''
    
    # Filtrar datos para el SKU, sucursal y algoritmo
    df_ventas = df_ventas.copy()
    df_ventas['Semana'] = df_ventas['Fecha'].dt.isocalendar().week
    df_ventas['Anio'] = df_ventas['Fecha'].dt.year

    ventas_filtradas = df_ventas[(df_ventas['Codigo_Articulo'] == sku) & (df_ventas['Sucursal'] == sucursal)]
    forecast_filtrado = df_forecast[(df_forecast['Codigo_Articulo'] == sku) & 
                                    (df_forecast['Sucursal'] == sucursal) & 
                                    (df_forecast['algoritmo'] == algoritmo)]

    # Generar índice temporal ordenado por año + semana
    ventas_filtradas = ventas_filtradas.sort_values('Fecha').reset_index(drop=True)
    ventas_filtradas['Index'] = range(len(ventas_filtradas))

    resultados = []

    for start in range(0, len(ventas_filtradas) - window_size - horizon + 1, step):
        end_train = start + window_size
        start_test = end_train
        end_test = start_test + horizon

        df_train = ventas_filtradas.iloc[start:end_train]
        df_test = ventas_filtradas.iloc[start_test:end_test]

        # Obtener semanas y años para el período de testeo
        semanas_test = df_test[['Anio', 'Semana']].drop_duplicates()

        # Unir con el forecast
        forecast_test = pd.merge(
            df_test,
            forecast_filtrado,
            on=['Codigo_Articulo', 'Sucursal', 'Semana'],
            how='inner',
            suffixes=('_real', '_forecast')
        )

        if len(forecast_test) == 0:
            continue

        # Calcular métricas
        mae = np.mean(np.abs(forecast_test['Forecast'] - forecast_test['Unidades']))
        rmse = np.sqrt(np.mean((forecast_test['Forecast'] - forecast_test['Unidades']) ** 2))
        smape = np.mean(
            2 * np.abs(forecast_test['Forecast'] - forecast_test['Unidades']) / 
            (np.abs(forecast_test['Forecast']) + np.abs(forecast_test['Unidades']) + 1e-6)
        )

        resultados.append({
            'Codigo_Articulo': sku,
            'Sucursal': sucursal,
            'algoritmo': algoritmo,
            'Inicio_Ventana': df_train['Fecha'].iloc[0],
            'Fin_Ventana': df_train['Fecha'].iloc[-1],
            'MAE': mae,
            'RMSE': rmse,
            'sMAPE': smape
        })

    return pd.DataFrame(resultados)
