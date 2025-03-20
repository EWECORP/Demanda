
# 🧠 S10_GENERAR_FORECAST_Planificado

Este script permite automatizar la ejecución de pronósticos de demanda utilizando distintos algoritmos predefinidos. Fue diseñado para integrarse con la base de datos PostgreSQL y trabajar en conjunto con la arquitectura de ejecución de modelos de forecasting del sistema.

---

## 📌 Objetivo

Ejecutar automáticamente, en horarios programados, los modelos de pronóstico de demanda definidos para distintos proveedores, tomando como referencia una lista de ejecuciones pendientes.

---

## 📂 Archivo principal

- `S10_GENERAR_FORECAST_Planificado.py`

---

## ⚙️ Funcionalidad principal

1. Consulta la base de datos buscando ejecuciones con estado **pendiente** (estado `10`).
2. Para cada ejecución:
   - Lee parámetros de configuración del modelo (`1_Window`, `f1`, `f2`, `f3`).
   - Cambia el estado de la ejecución a **en curso** (`15`).
   - Ejecuta el algoritmo correspondiente (ALGO_01 a ALGO_06).
   - Guarda resultados en la base de datos.
   - Actualiza el estado a **completado** (`20`).
   - En caso de error, cambia el estado a **error** (`99`).

---

## 🧪 Requisitos

- Python 3.8+
- `.env` con los parámetros de conexión a las bases de datos.
- Módulo `funciones_forecast.py` con:
  - `get_forecast`
  - `get_excecution_excecute_by_status`
  - `get_execution_parameter`
  - `update_execution`

---

## 🔁 Variables clave

| Variable | Descripción |
|----------|-------------|
| `execution_id` | Identificador de ejecución del modelo. |
| `id_proveedor` | Código del proveedor a procesar. |
| `method` | Nombre del algoritmo a utilizar (ALGO_01 a ALGO_06). |
| `ventana` | Ventana de análisis de días. |
| `f1`, `f2`, `f3` | Parámetros del modelo según el algoritmo. |

---

## 📅 Ejecución programada

Este archivo puede ser ejecutado de manera automática mediante:

### En Windows (Task Scheduler)
1. Crear archivo `.bat`:
   ```bat
   @echo off
   cd C:\ruta\al\script
   call venv\Scripts\activate
   python S10_GENERAR_FORECAST_Planificado.py
   ```

2. Programarlo desde el **Programador de tareas de Windows**.

### En Linux (cron)
Agregar al `crontab`:
```bash
0 7 * * * /usr/bin/python3 /ruta/S10_GENERAR_FORECAST_Planificado.py >> /ruta/logs/forecast.log 2>&1
```

---

## ✅ Estados de Ejecución

| Estado | Descripción |
|--------|-------------|
| 10 | Pendiente de ejecución |
| 15 | En curso |
| 20 | Finalizado correctamente |
| 99 | Error durante ejecución |

---

## 🧩 Modularidad

Este script está diseñado para integrarse fácilmente dentro de una arquitectura de microservicios o ejecución agendada. Se recomienda centralizar los algoritmos en `funciones_forecast.py`.

---

## 🔐 Seguridad

Las credenciales de conexión están aisladas en el archivo `.env` y no deben incluirse en el repositorio.

---

## 👨‍💻 Autor

- Proyecto: Zeetrex Forecast Engine
- Creado por: Equipo de Ingeniería + ChatGPT
