
# Análisis de Algoritmos de Forecast - MOLINOS
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob, os, re

# Carga y unificacion archivos CSV del proveedor 


folder_path = r".\data\procesado"
csv_files = glob.glob(os.path.join(folder_path, "8449_CAGNOLI_ALGO_*_Solicitudes_Compra.csv"))

dataframes = []
for file in csv_files:
    df = pd.read_csv(file)
    match = re.search(r'ALGO_\d+', os.path.basename(file))
    algoritmo = match.group(0) if match else "DESCONOCIDO"
    df["algoritmo_file"] = algoritmo
    dataframes.append(df)

df_all = pd.concat(dataframes, ignore_index=True)

# Calcular MAE y Bias
df_all["error_abs"] = abs(df_all["Forecast"] - df_all["ventas_last"])
df_all["bias"] = df_all["Forecast"] - df_all["ventas_last"]

mae_df = df_all.groupby("algoritmo")["error_abs"].mean().reset_index()
bias_df = df_all.groupby("algoritmo")["bias"].mean().reset_index()

#Gráfico: MAE y Bias por algoritmo
fig1 = make_subplots(rows=1, cols=2, subplot_titles=("MAE por Algoritmo", "Bias por Algoritmo"))
fig1.add_trace(go.Bar(x=mae_df["algoritmo"], y=mae_df["error_abs"], name="MAE", marker_color="steelblue"), row=1, col=1)
fig1.add_trace(go.Bar(x=bias_df["algoritmo"], y=bias_df["bias"], name="Bias", marker_color="darkorange"), row=1, col=2)
fig1.update_layout(title="Comparación de Error Medio y Tendencia por Algoritmo", height=500, showlegend=False)
fig1.show()

#Dispersión Forecast vs Ventas Reales por algoritmo
fig2 = px.scatter(df_all, x="ventas_last", y="Forecast", color="algoritmo_file",
                  title="Forecast vs Ventas Últimas por Algoritmo",
                  labels={"ventas_last": "Ventas Últimas", "Forecast": "Forecast", "algoritmo_file": "Algoritmo"},
                  hover_data=["Codigo_Articulo", "Sucursal"])
min_val = min(df_all["ventas_last"].min(), df_all["Forecast"].min())
max_val = max(df_all["ventas_last"].max(), df_all["Forecast"].max())
fig2.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val], mode="lines", name="Línea Igualdad",
                          line=dict(color="black", dash="dash")))
fig2.show()

# Boxplot de error absoluto por algoritmo + anotación del mejor
mae_por_algoritmo = df_all.groupby("algoritmo_file")["error_abs"].mean().reset_index()
mejor_algoritmo = mae_por_algoritmo.loc[mae_por_algoritmo["error_abs"].idxmin()]
algoritmo_nombre = mejor_algoritmo["algoritmo_file"]
error_minimo = mejor_algoritmo["error_abs"]

fig3 = px.box(df_all, x="algoritmo_file", y="error_abs",
              title="Error Absoluto del Forecast por Algoritmo",
              labels={"algoritmo_file": "Algoritmo", "error_abs": "Error Absoluto"})
fig3.add_annotation(x=algoritmo_nombre, y=error_minimo,
                    text=f"✅ Menor Error absoluto: {algoritmo_nombre} ({error_minimo:.2f})",
                    showarrow=True, arrowhead=1, yshift=20,
                    font=dict(size=12, color="black"), bgcolor="lightgreen", bordercolor="gray")
fig3.show()

#Productos con MAE > 100
mae_por_producto = df_all.groupby("Codigo_Articulo")["error_abs"].mean().reset_index()
total_productos = mae_por_producto["Codigo_Articulo"].nunique()
mae_filtrados = mae_por_producto[mae_por_producto["error_abs"] > 100]
mae_filtrados["Codigo_Articulo"] = mae_filtrados["Codigo_Articulo"].astype(str)
cantidad_productos = len(mae_filtrados)
porcentaje = (cantidad_productos / total_productos) * 100

fig = px.bar(mae_filtrados.sort_values("error_abs", ascending=False),
             x="Codigo_Articulo", y="error_abs",
             title="Productos con Error de Forecast (MAE) Mayor a 100",
             labels={"Codigo_Articulo": "Código de Artículo", "error_abs": "Error Absoluto Medio (MAE)"},
             text="error_abs")
fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=-45)
fig.add_annotation(xref="paper", yref="paper", x=0.50, y=0.98,
                   text=f"Productos con MAE > 100: <b>{cantidad_productos}</b><br>Representa el <b>{porcentaje:.1f}%</b> del total ({total_productos})",
                   showarrow=False, bgcolor="lightyellow", bordercolor="gray", font=dict(size=12))
fig.show()

# Top 10 combinaciones producto–sucursal con mayor error
mae_producto_sucursal = df_all.groupby(["Codigo_Articulo", "Sucursal"])["error_abs"].mean().reset_index()
mae_producto_sucursal = mae_producto_sucursal.sort_values("error_abs", ascending=False).head(10)
mae_producto_sucursal["Producto_Sucursal"] = mae_producto_sucursal["Codigo_Articulo"].astype(str) + " - Suc " + mae_producto_sucursal["Sucursal"].astype(str)

fig = px.bar(mae_producto_sucursal, x="Producto_Sucursal", y="error_abs",
             title="Top 10 Combinaciones Producto–Sucursal con Mayor Error de Forecast",
             labels={"Producto_Sucursal": "Producto - Sucursal", "error_abs": "Error Absoluto Medio (MAE)"},
             text="error_abs")
fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=-45)
fig.show()

# Sucursales con MAE > 100
mae_por_sucursal = df_all.groupby("Sucursal")["error_abs"].mean().reset_index()
total_sucursales = mae_por_sucursal["Sucursal"].nunique()
mae_filtradas = mae_por_sucursal[mae_por_sucursal["error_abs"] > 100]
mae_filtradas["Sucursal"] = mae_filtradas["Sucursal"].astype(str)
cantidad_sucursales = len(mae_filtradas)
porcentaje_suc = (cantidad_sucursales / total_sucursales) * 100

fig = px.bar(mae_filtradas.sort_values("error_abs", ascending=False),
             x="Sucursal", y="error_abs",
             title="Sucursales con Error de Forecast (MAE) Mayor a 100",
             labels={"Sucursal": "Sucursal", "error_abs": "Error Absoluto Medio (MAE)"},
             text="error_abs")
fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=-45)
fig.add_annotation(xref="paper", yref="paper", x=0.50, y=0.98,
                   text=f"Sucursales con MAE > 100: <b>{cantidad_sucursales}</b><br>Representan el <b>{porcentaje_suc:.1f}%</b> del total ({total_sucursales})",
                   showarrow=False, bgcolor="lightyellow", bordercolor="gray", font=dict(size=12))
fig.show()
