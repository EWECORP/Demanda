# 📊 Módulo: `S30_GENERA_Grafico_Detalle.py`

## 🧾 Descripción General

Este módulo forma parte del flujo de generación de pronósticos de demanda para el sistema de reposición de Zeetrex. Está diseñado para generar gráficos detallados por artículo y sucursal, basados en datos históricos y pronósticos previamente calculados.

Se utiliza cuando una ejecución tiene estado `30` (forecast calculado con datos completos), y su propósito es:

- Leer datos de ventas y forecast para un proveedor específico.
- Generar visualizaciones gráficas (ventas históricas + forecast) codificadas en base64.
- Guardar un archivo CSV extendido con dichos gráficos embebidos.
- Actualizar el estado del proceso a `35` durante la generación, y luego a `40` al finalizar.

---

## 📂 Archivos involucrados

- `.../{etiqueta}_Ventas.csv`: contiene el histórico de ventas.
- `.../{algoritmo}_Solicitudes_Compra.csv`: contiene los resultados del forecast.
- `.../{algoritmo}_Pronostico_Extendido.csv`: archivo de salida con los gráficos embebidos.

---

## 🔄 Flujo de ejecución

1. Recupera todas las ejecuciones con estado `30` (`get_excecution_by_status(30)`).
2. Para cada ejecución:
   - Cambia el estado a `35` (procesando gráficos).
   - Lee los archivos CSV de ventas y forecast.
   - Aplica `generar_grafico_base64(...)` a cada combinación artículo-sucursal.
   - Guarda el archivo extendido con la columna `GRAFICO`.
   - Actualiza el estado a `40` en la base de datos (`update_execution`).

---

## 🛠 Funciones utilizadas

### `insertar_graficos_forecast(algoritmo, name, id_proveedor)`
Genera y embebe gráficos en el DataFrame de forecast usando datos históricos.

### `generar_grafico_base64(...)`
Función importada desde `funciones_forecast.py` que genera una imagen base64 a partir de datos de ventas y pronóstico.

---

## 🧠 Consideraciones Técnicas

- El gráfico generado se almacena en una nueva columna `GRAFICO`, en formato texto base64.
- La conversión a entero y a tipo `datetime` de los datos leídos es necesaria para evitar errores en el gráfico.
- Si algún artículo o sucursal tiene datos incompletos (`NaN`), se omite la generación del gráfico.
- Se utiliza `ace_tools_open` para visualización interna opcional en entorno Jupyter.

---

## ✅ Estados del Proceso

| Estado | Significado                        |
|--------|------------------------------------|
| 30     | Forecast calculado con datos       |
| 35     | Procesando generación de gráficos  |
| 40     | Finalizado y exportado             |

---

## ✍️ Autoría

- **Autor:** EWE - Zeetrex  
- **Fecha de creación:** 2025-03-22

---

## 📁 Ubicación esperada

Este script debe ejecutarse desde la raíz del proyecto donde se encuentren los archivos CSV y `.env`.

---

## 🚀 Ejecución

Este módulo se puede ejecutar manualmente o ser integrado como parte de una ejecución planificada, por ejemplo:

```bash
python S30_GENERA_Grafico_Detalle.py
```

Requiere que el archivo `funciones_forecast.py` esté disponible y correctamente importado.