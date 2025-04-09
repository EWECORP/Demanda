import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import pandas as pd
import base64
from io import BytesIO
import os
import matplotlib.pyplot as plt


from funciones_forecast import (
    get_execution_execute_by_status,
    generar_grafico_json,
    insertar_graficos_json,
    graficar_desde_datos_json,
    update_execution_execute,
    generar_grafico_base64,
    generar_grafico_json
)
# Le

# Función para decodificar y mostrar imagen en Tkinter
def mostrar_en_tkinter(base64_str, image_label):
    try:
        img_data = base64.b64decode(base64_str)
        image = Image.open(BytesIO(img_data))
        image = image.resize((400, 300), Image.LANCZOS)
        tk_image = ImageTk.PhotoImage(image)
        image_label.configure(image=tk_image)
        image_label.image = tk_image
    except Exception as e:
        print(f"Error mostrando imagen: {e}")

# Función para calcular tamaño en KB
def obtener_tamano_grafico_kb(base64_str):
    try:
        bytes_data = base64.b64decode(base64_str)
        size_kb = len(bytes_data) / 1024
        return round(size_kb, 2)
    except Exception as e:
        print(f"Error al calcular el tamaño del gráfico: {e}")
        return 0.0

# Función para exportar gráfico seleccionado a imagen
def exportar_grafico():
    selected_item = tree.focus()
    if selected_item:
        grafico_b64 = graficos.get(int(selected_item), None)
        if grafico_b64:
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if file_path:
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(grafico_b64))
                print(f"Gráfico exportado: {file_path}")

# Función para cargar archivo y poblar la tabla
def cargar_archivo():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return
    global df_original
    df = pd.read_csv(file_path)
    df.fillna("", inplace=True)
    df_original = df
    actualizar_tabla(df)

# Función para actualizar la tabla con un DataFrame dado
def actualizar_tabla(df):
    tree.delete(*tree.get_children())
    graficos.clear()
    for i, row in df.iterrows():
        tree.insert("", "end", iid=i, values=(
            row['Codigo_Articulo'],
            row['Sucursal'],
            row['Forecast'],
            row['Average'],
            row['ventas_last'],
            row['ventas_previous'],
            row['ventas_same_year']
        ))
        graficos[i] = row['GRAFICO']

# Evento para seleccionar y mostrar gráfico
def on_select(event):
    selected_item = tree.focus()
    if selected_item:
        grafico_b64 = graficos.get(int(selected_item), None)
        if grafico_b64:
            # graficar_desde_datos_json(grafico_b64)
            mostrar_en_tkinter(grafico_b64, image_label)
            size_kb = obtener_tamano_grafico_kb(grafico_b64)
            size_label.config(text=f"Tamaño del gráfico: {size_kb} KB")

# Función para aplicar filtros
def aplicar_filtros():
    art = entry_articulo.get()
    suc = entry_sucursal.get()
    df = df_original.copy()
    if art:
        df = df[df['Codigo_Articulo'].astype(str).str.contains(art)]
    if suc:
        df = df[df['Sucursal'].astype(str).str.contains(suc)]
    actualizar_tabla(df)

Select>>", on_select)

def graficar_desde_datos_json(datos_dict):
    fechas = pd.to_datetime(datos_dict["fechas"])
    unidades = datos_dict["unidades"]
    media_movil = datos_dict["media_movil"]
    semana_num = datos_dict["semana_num"]
    forecast = datos_dict["forecast"]
    ventas_last = datos_dict["ventas_last"]
    ventas_previous = datos_dict["ventas_previous"]
    ventas_same_year = datos_dict["ventas_same_year"]
    average = datos_dict["average"]
    ventas_semanales = datos_dict["ventas_semanales"]

    fig, ax = plt.subplots(figsize=(8, 6), nrows=2, ncols=2)
    fig.suptitle(f"Demanda Articulo {datos_dict['articulo']} - Sucursal {datos_dict['sucursal']}")

    # Ventas diarias
    ax[0, 0].plot(fechas, unidades, marker="o", label="Ventas", color="red")
    ax[0, 0].plot(fechas, media_movil, linestyle="--", label="Media Móvil (7 días)", color="black")
    ax[0, 0].set_title("Ventas Diarias")
    ax[0, 0].legend()
    ax[0, 0].tick_params(axis='x', rotation=45)

    # Histograma de ventas semanales
    ax[0, 1].bar(semana_num, ventas_semanales, color="blue", alpha=0.7)
    ax[0, 1].set_title("Histograma de Ventas Semanales")
    ax[0, 1].grid(axis="y", linestyle="--", alpha=0.7)

    # Forecast vs ventas anteriores
    ax[1, 0].bar(["Forecast", "Actual", "Anterior", "Año Ant."],    
                [forecast, ventas_last, ventas_previous, ventas_same_year],
                color=["orange", "green", "blue", "purple"])
    ax[1, 0].set_title("Forecast vs Ventas Anteriores")
    ax[1, 0].grid(axis="y", linestyle="--", alpha=0.7)

    # Comparación últimos 30 días
    ax[1, 1].bar(["Últimos 30", "Anteriores 30", "Año Anterior", "Average"],
                [ventas_last, ventas_previous, ventas_same_year, average],
                color=["red", "blue", "purple", "gray"])
    ax[1, 1].set_title("Comparación de Ventas en 3 Períodos")
    ax[1, 1].grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

# Interfaz principal
root = tk.Tk()
root.title("Visualizador de Forecast con Gráficos")
root.geometry("1100x720")

frame_top = ttk.Frame(root)
frame_top.pack(fill=tk.X, padx=10, pady=5)

btn_cargar = ttk.Button(frame_top, text="📂 Cargar archivo CSV", command=cargar_archivo)
btn_cargar.pack(side=tk.LEFT, padx=5)

btn_exportar = ttk.Button(frame_top, text="💾 Exportar gráfico", command=exportar_grafico)
btn_exportar.pack(side=tk.LEFT, padx=5)

# Filtros
ttk.Label(frame_top, text="Filtrar por Artículo:").pack(side=tk.LEFT, padx=5)
entry_articulo = ttk.Entry(frame_top, width=10)
entry_articulo.pack(side=tk.LEFT)

ttk.Label(frame_top, text="Sucursal:").pack(side=tk.LEFT, padx=5)
entry_sucursal = ttk.Entry(frame_top, width=10)
entry_sucursal.pack(side=tk.LEFT)

btn_filtrar = ttk.Button(frame_top, text="🔍 Aplicar filtros", command=aplicar_filtros)
btn_filtrar.pack(side=tk.LEFT, padx=5)

frame_middle = ttk.Frame(root)
frame_middle.pack(fill=tk.BOTH, expand=True, padx=10)

columns = ('Codigo_Articulo', 'Sucursal', 'Forecast', 'Average', 'ventas_last', 'ventas_previous', 'ventas_same_year')
tree = ttk.Treeview(frame_middle, columns=columns, show='headings', height=15)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor=tk.CENTER)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
tree.bind("<<Treeview
scrollbar = ttk.Scrollbar(frame_middle, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.LEFT, fill=tk.Y)

image_label = ttk.Label(root)
image_label.pack(pady=10)

size_label = ttk.Label(root, text=" 📦 Tamaño del gráfico: - KB")
size_label.pack()

df_original = pd.DataFrame()
graficos = {}

root.mainloop()
