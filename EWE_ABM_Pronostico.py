# Solo importa lo necesario desde el módulo de funciones

import psycopg2
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from dotenv import dotenv_values

# === CARGAR CREDENCIALES DESDE .env ===
secrets = dotenv_values(".env")
DB_CONFIG = {
    'host': secrets['SERVIDOR4'],
    'port': secrets['PUERTO4'],
    'dbname': secrets['BASE4'],
    'user': secrets['USUARIO4'],
    'password': secrets['CONTRASENA4']
}

# === FUNCIONES DE BASE DE DATOS ===
def obtener_proveedores():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, ext_code
                    FROM public.fnd_supplier
                    ORDER BY ext_code
                """)
                return cur.fetchall()
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener proveedores:\n{e}")
        return []

def obtener_modelos():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT method, name, id
                    FROM public.spl_supply_forecast_model
                    ORDER BY method
                """)
                return cur.fetchall()
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener modelos:\n{e}")
        return []

def obtener_parametros(model_id):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name, data_type, default_value, id
                    FROM public.spl_supply_forecast_model_parameter
                    WHERE supply_forecast_model_id = %s
                    ORDER BY name
                """, (model_id,))
                return cur.fetchall()
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener parámetros:\n{e}")
        return []

def obtener_supplier_id(ext_code):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id
                    FROM public.fnd_supplier
                    WHERE ext_code = %s
                """, (ext_code,))
                result = cur.fetchone()
                if result:
                    return result[0]  # Retorna el UUID
                else:
                    return None  # Si no encuentra resultados
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener supplier_id:\n{e}")
        return None

# === EVENTOS Y FUNCIONALIDAD ===
def filtrar_proveedores(*args):
    texto = filtro_var.get().lower()
    lista_filtrada = [
        f"{prov[2]} - {prov[1]}" for prov in proveedores
        if texto in (prov[2] or '').lower() or texto in (prov[1] or '').lower()
    ]
    combo_proveedores['values'] = lista_filtrada
    combo_proveedores.set('')
    limpiar_datos_proveedor()
    limpiar_modelos_y_parametros()

def mostrar_datos_proveedor(event):
    seleccion = combo_proveedores.get()
    for prov in proveedores:
        if seleccion == f"{prov[2]} - {prov[1]}":
            id_valor.set(prov[0])
            name_valor.set(prov[1])
            ext_code_valor.set(prov[2])
            break

def mostrar_datos_modelo(event):
    seleccion = combo_modelos.get()
    for mod in modelos:
        if seleccion == f"{mod[0]} - {mod[1]}":
            model_id_valor.set(mod[2])
            method_valor.set(mod[0])
            model_name_valor.set(mod[1])
            cargar_parametros(mod[2])
            break

def cargar_parametros(model_id):
    global param_entries, param_definitions
    for widget in param_frame.winfo_children():
        widget.destroy()

    parametros = obtener_parametros(model_id)
    param_entries.clear()
    param_definitions.clear()

    for i, p in enumerate(parametros):
        nombre = p[0]
        tipo = p[1]
        valor = p[2]
        id_param = p[3]

        tk.Label(param_frame, text=f"{nombre} ({tipo}):", anchor='w').grid(row=i, column=0, sticky='w', padx=5, pady=2)
        entry = tk.Entry(param_frame, width=40)
        entry.insert(0, valor if valor is not None else '')
        entry.grid(row=i, column=1, padx=5, pady=2)

        param_entries[id_param] = entry
        param_definitions.append((id_param, nombre, tipo))

def limpiar_datos_proveedor():
    id_valor.set('')
    name_valor.set('')
    ext_code_valor.set('')

def limpiar_modelos_y_parametros():
    combo_modelos.set('')
    model_id_valor.set('')
    method_valor.set('')
    model_name_valor.set('')
    for widget in param_frame.winfo_children():
        widget.destroy()
    param_entries.clear()
    param_definitions.clear()

def ejecutar_configuracion():
    if not model_id_valor.get() or not id_valor.get():
        messagebox.showwarning("Datos faltantes", "Debe seleccionar un proveedor y un modelo.")
        return

    now = datetime.now()
    exec_id = str(uuid.uuid4())
    schedule_id = str(uuid.uuid4())
    execution_id = str(uuid.uuid4())
    supplier_id = obtener_supplier_id(ext_code_valor.get())
    print(f"Supplier ID obtenido: {supplier_id}")

    if not supplier_id:
        messagebox.showerror("Error", "No se pudo obtener el ID del proveedor.")
        return

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:                
                # Armar campos requeridos
                ext_code = ext_code_valor.get()
                proveedor = name_valor.get()
                label = proveedor.split(" ")[0]
                method = method_valor.get()
                model_name = model_name_valor.get()                
                execution_name = f"{ext_code}_{label}_{method}"
                execution_description = model_name

                # === INSERT 0: spl_supply_forecast_execution (registro principal) ===
                cur.execute("""
                    INSERT INTO public.spl_supply_forecast_execution (
                        id, "timestamp", supply_forecast_model_id, supplier_id, name, description, ext_supplier_code
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    exec_id, 
                    now,
                    model_id_valor.get(),
                    supplier_id,                
                    execution_name,
                    execution_description,
                    ext_code_valor.get()
                ))
                
                # INSERT INTO schedule
                cur.execute("""
                    INSERT INTO public.spl_supply_forecast_execution_schedule(
                        id, "timestamp", supply_forecast_execution_id)
                    VALUES (%s, %s, %s)
                """, (schedule_id, now, exec_id))

                # INSERT INTO execute
                cur.execute("""
                    INSERT INTO public.spl_supply_forecast_execution_execute(
                        id, end_execution, last_execution, start_execution, "timestamp", 
                        supply_forecast_execution_id, supply_forecast_execution_schedule_id, ext_supplier_code, supply_forecast_execution_status_id, supplier_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    execution_id,
                    now, True, now, now,
                    exec_id,
                    schedule_id,
                    ext_code_valor.get(),
                    10,
                    supplier_id
                ))

                # INSERT INTO parameters
                for model_param_id, entry in param_entries.items():
                    param_id = str(uuid.uuid4())
                    valor = entry.get()

                    cur.execute("""
                        INSERT INTO public.spl_supply_forecast_execution_parameter(
                            id, "timestamp", supply_forecast_execution_id, supply_forecast_model_parameter_id, value)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        param_id, now, exec_id, model_param_id, valor
                    ))

            conn.commit()
        messagebox.showinfo("Éxito", "Configuración ejecutada correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Error durante la ejecución:\n{e}")

# === INTERFAZ GRÁFICA ===
#root = tk.Tk()
root = ttk.Window(themename="cerculean")
root.title("Configurador de Ejecución de Pronóstico")
root.geometry("650x700")
root.resizable(False, False)

# Variables proveedor
id_valor = tk.StringVar()
name_valor = tk.StringVar()
ext_code_valor = tk.StringVar()
filtro_var = tk.StringVar()
filtro_var.trace_add("write", filtrar_proveedores)

# Variables modelo
model_id_valor = tk.StringVar()
method_valor = tk.StringVar()
model_name_valor = tk.StringVar()

# Diccionarios para parámetros
param_entries = {}
param_definitions = []

# Cargar datos iniciales
proveedores = obtener_proveedores()
modelos = obtener_modelos()

# UI Proveedor
tk.Label(root, text="Buscar proveedor (por ext_code o nombre):").pack(pady=5)
tk.Entry(root, textvariable=filtro_var, width=60).pack()
tk.Label(root, text="Seleccionar Proveedor:").pack(pady=5)
combo_proveedores = ttk.Combobox(root, values=[], state="readonly", width=60)
combo_proveedores.pack()
combo_proveedores.bind("<<ComboboxSelected>>", mostrar_datos_proveedor)
tk.Entry(root, textvariable=id_valor, state="readonly", width=60).pack(pady=2)
tk.Entry(root, textvariable=name_valor, state="readonly", width=60).pack(pady=2)
tk.Entry(root, textvariable=ext_code_valor, state="readonly", width=60).pack(pady=2)

# UI Modelo
tk.Label(root, text="Seleccionar Modelo de Pronóstico:").pack(pady=10)
combo_modelos = ttk.Combobox(root, values=[f"{m[0]} - {m[1]}" for m in modelos], state="readonly", width=60)
combo_modelos.pack()
combo_modelos.bind("<<ComboboxSelected>>", mostrar_datos_modelo)
tk.Entry(root, textvariable=model_id_valor, state="readonly", width=60).pack(pady=2)
tk.Entry(root, textvariable=method_valor, state="readonly", width=60).pack(pady=2)
tk.Entry(root, textvariable=model_name_valor, state="readonly", width=60).pack(pady=2)

# Parámetros editables
tk.Label(root, text="Parámetros del Modelo (editables):").pack(pady=10)
param_frame = tk.Frame(root)
param_frame.pack(pady=5, fill='x', padx=10)

# Botón de ejecución
tk.Button(root, text="Ejecutar configuración", command=ejecutar_configuracion, bg="#4CAF50", fg="white", height=2, width=30).pack(pady=20)

# Inicialización
filtrar_proveedores()
root.mainloop()

