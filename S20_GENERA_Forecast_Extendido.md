# 🧮 Módulo: `S20_GENERA_Forecast_Extendido.py`

## 🧾 Descripción General

Este módulo se encarga de enriquecer los datos del pronóstico de demanda previamente generados (estado `20`) con información adicional proveniente de tablas maestras y estadísticas de reposición.

El objetivo es construir un archivo extendido que integre información de producto, sucursal, precios, factores de venta y parámetros de stock para su uso en procesos posteriores (como visualización gráfica o carga a sistemas externos).

---

## 📂 Archivos involucrados

- `.../{etiqueta}_Ventas.csv`: histórico de ventas.
- `.../{etiqueta}_Articulos.csv`: maestro de artículos por sucursal.
- `.../{algoritmo}_Solicitudes_Compra.csv`: archivo original del forecast.
- `.../{algoritmo}_Pronostico_Extendido.csv`: archivo enriquecido final.

---

## 🔄 Flujo de ejecución

1. Recupera ejecuciones en estado `20` con `get_excecution_by_status(20)`.
2. Para cada forecast:
   - Lee archivos locales de ventas, artículos y forecast.
   - Consulta la base de datos para obtener:
     - Maestro de sucursales (`fnd_site`)
     - Maestro de productos (`fnd_product`)
   - Realiza un merge por código de artículo y sucursal.
   - Agrega parámetros relevantes desde el maestro de artículos.
   - Guarda el archivo extendido en disco.
   - Actualiza el estado del proceso a `30`.

---

## 🛠 Funciones utilizadas

### `extender_datos_forecast(algoritmo, name, id_proveedor)`
Lee los datos del forecast y ventas, enriquece con información de producto y sucursal, y devuelve un DataFrame consolidado.

---

## 🧠 Consideraciones Técnicas

- Se normalizan los códigos (`ext_code`, `code`) como `int` para permitir la fusión.
- Se utilizan claves compuestas (`Codigo_Articulo` y `Sucursal`) para garantizar la integridad del join.
- El proceso es seguro ante valores faltantes y realiza copias defensivas de los DataFrames.
- El archivo final se guarda con nombre `{algoritmo}_Pronostico_Extendido.csv`.

---

## ✅ Estados del Proceso

| Estado | Significado                            |
|--------|----------------------------------------|
| 20     | Forecast listo                         |
| 30     | Datos extendidos y enriquecidos        |

---

## ✍️ Autoría

- **Autor:** EWE - Zeetrex  
- **Fecha de creación:** 2025-03-22

---

## 📁 Ubicación esperada

Este script debe ejecutarse desde la raíz del proyecto, donde se encuentran los archivos `.csv` y la configuración `.env`.

---

## 🚀 Ejecución

Este módulo puede ser ejecutado manualmente o en una tarea planificada:

```bash
python S20_GENERA_Forecast_Extendido.py
```

Requiere tener acceso a los datos generados en la etapa anterior (`S10`) y a las funciones contenidas en `funciones_forecast.py`.