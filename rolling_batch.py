
import pandas as pd
from rolling_backtest import rolling_backtest
from tqdm import tqdm

def aplicar_rolling_batch(df_ventas, df_forecast, window_size=52, horizon=4, step=1):
    '''
    Ejecuta rolling_backtest para cada combinación de SKU, sucursal y algoritmo disponible.
    Devuelve un DataFrame consolidado con todas las métricas de evaluación.
    '''
    combinaciones = df_forecast[['Codigo_Articulo', 'Sucursal', 'algoritmo']].drop_duplicates()
    resultados = []

    for _, row in tqdm(combinaciones.iterrows(), total=len(combinaciones)):
        sku = row['Codigo_Articulo']
        sucursal = row['Sucursal']
        algoritmo = row['algoritmo']

        df_result = rolling_backtest(
            df_ventas=df_ventas,
            df_forecast=df_forecast,
            sku=sku,
            sucursal=sucursal,
            algoritmo=algoritmo,
            window_size=window_size,
            horizon=horizon,
            step=step
        )

        if not df_result.empty:
            resultados.append(df_result)

    return pd.concat(resultados, ignore_index=True) if resultados else pd.DataFrame()
