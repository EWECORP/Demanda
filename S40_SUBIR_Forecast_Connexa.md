# 🚀 Módulo: `S40_SUBIR_Forecast_Connexa.py`

## 🧾 Descripción General

Este módulo representa el paso final del pipeline de generación de forecast, y está encargado de subir los resultados extendidos y graficados a la plataforma **CONNEXA**. Trabaja sobre ejecuciones con estado `40`, ya listas y validadas, y actualiza la cabecera de la ejecución con métricas agregadas de valor.

El proceso incluye:
- Publicación del detalle de cada artículo/sucursal en la tabla `execution_execute_result`.
- Cálculo del forecast valorizado a precio de venta, costo y margen estimado.
- Generación de un minigráfico embebido en la cabecera.
- Actualización del estado de la ejecución a `50`, indicando que el forecast está disponible.

---

## 📂 Archivos involucrados

- `.../{algoritmo}_Pronostico_Extendido.csv`: archivo con datos extendidos y graficados.

---

## 🔄 Flujo de ejecución

1. Lee ejecuciones en estado `40` usando `get_excecution_excecute_by_status(40)`.
2. Actualiza el estado a `45` como paso intermedio.
3. Lee el archivo extendido del forecast.
4. Enlaza con `fnd_site` para obtener el `site_id`.
5. Carga en la tabla de resultados individuales con `publish_excecution_results(...)`.
6. Calcula métricas agregadas:
   - Forecast valorizado a venta (en miles)
   - Forecast valorizado a costo (en miles)
   - Margen potencial
7. Genera un gráfico de resumen (`mini_grafico`).
8. Actualiza la ejecución con las métricas, gráfico y cambia el estado a `50`.

---

## 🛠 Funciones utilizadas

### `publish_excecution_results(...)`
Carga el detalle de cada línea de forecast (por artículo y sucursal) en la tabla `execution_execute_result`.

### `actualizar_site_ids(...)`
Obtiene el `site_id` de cada sucursal a partir del código y lo fusiona con el forecast extendido.

### `insertar_graficos_forecast(...)`
Vuelve a aplicar `generar_grafico_base64(...)` para generar una columna `GRAFICO` si hiciera falta.

---

## 🧠 Consideraciones Técnicas

- Utiliza `update_execution(...)` para modificar la cabecera de forecast execution.
- El minigráfico embebido se genera mediante `generar_mini_grafico(...)` (debe estar disponible).
- Todas las métricas son calculadas en miles para facilitar su visualización.
- El módulo es tolerante a datos nulos y valida correctamente los `site_id`.

---

## ✅ Estados del Proceso

| Estado | Descripción                             |
|--------|------------------------------------------|
| 40     | Forecast finalizado y graficado          |
| 45     | En proceso de carga a CONNEXA            |
| 50     | Forecast publicado y disponible          |

---

## ✍️ Autoría

- **Autor:** EWE - Zeetrex  
- **Fecha de creación:** 2025-03-22

---

## 📁 Ubicación esperada

Este script debe ejecutarse en la etapa final del proceso de forecast, una vez que los archivos extendidos están completos.

---

## 🚀 Ejecución

```bash
python S40_SUBIR_Forecast_Connexa.py
```

Debe ser programado como parte de la ejecución planificada, luego del paso `S30`.

---

## 🧩 Requiere

- forecast extendido y graficado (`estado = 40`)
- acceso a funciones de `funciones_forecast.py`
- funciones adicionales como `create_execution_execute_result`, `get_precios(...)` y `generar_mini_grafico(...)`