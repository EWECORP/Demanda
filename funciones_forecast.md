# 🧠 Módulo: `funciones_forecast.py`

## 🧾 Descripción General

Este módulo centraliza todas las funciones reutilizables del sistema de pronóstico de demanda desarrollado por Zeetrex. Está diseñado para ser importado por los distintos scripts del pipeline (`S10`, `S20`, `S30`, etc.), proveyendo acceso a la lógica de negocio, consultas, cálculos y exportaciones necesarias para generar, extender y visualizar el forecast de reposición.

Incluye funcionalidades de:

- Conexión a bases de datos (PostgreSQL y SQL Server)
- Cálculo de pronóstico con múltiples algoritmos (ALGO_01 a ALGO_06)
- Exportación a PostgreSQL
- Recuperación de ejecuciones programadas
- Manejo de parámetros dinámicos
- Generación de gráficos embebidos en base64

---

## 🔧 Funcionalidades principales

### 📡 Conexiones
- `Open_Connection()`, `Open_Diarco_Data()`, `Open_Conn_Postgres()`, `Open_Postgres_retry()`: conexiones a diferentes bases.
- `Close_Connection()`: cierre de conexión seguro.

### 📊 Forecast y datos
- `generar_datos(...)`: genera y cachea ventas y artículos de un proveedor.
- `Exportar_Pronostico(...)`: exporta resultados del forecast a tabla Postgres.
- `get_forecast(...)`: punto de entrada que ejecuta el forecast según algoritmo.

### 📈 Algoritmos de pronóstico

| Algoritmo  | Función                               | Descripción |
|------------|----------------------------------------|-------------|
| ALGO_01    | `Calcular_Demanda_ALGO_01`             | Promedio ponderado |
| ALGO_02    | `Calcular_Demanda_ALGO_02`             | Holt (tendencia) |
| ALGO_03    | `Calcular_Demanda_ALGO_03`             | Holt-Winters (tendencia + estacionalidad) |
| ALGO_04    | `Calcular_Demanda_ALGO_04`             | EWMA (suavizado exponencial simple) |
| ALGO_05    | `Calcular_Demanda_ALGO_05`             | Promedio simple (30 días) |
| ALGO_06    | `Calcular_Demanda_ALGO_06`             | Holt semanal agrupado |

Además, cada uno tiene su función `Procesar_ALGO_xx(...)` que gestiona su ejecución y exportación.

### ⚙️ Control de ejecución

- `get_excecution_by_status(status)`: trae las ejecuciones con un estado específico.
- `get_execution(...)`: recupera una ejecución completa por ID.
- `update_execution(...)`: actualiza una ejecución con nuevos valores.
- `get_execution_parameter(...)`: obtiene los parámetros definidos en el modelo para cada ejecución.

### 🖼 Visualización

- `generar_grafico_base64(...)`: genera un gráfico en base64 a partir de un artículo/sucursal.
- Utilizado por el módulo `S30` para embebido visual en CSV.

---

## 📁 Organización del módulo

Todas las funciones están agrupadas por sección lógica:

- 🔌 Conexión a bases de datos
- 📦 Recuperación de datos de entrada
- 🧠 Cálculo de forecast
- 📤 Exportación de resultados
- ⚙️ Control de ejecución y estado
- 📊 Visualización gráfica

Cada función está documentada con comentarios inline y tiene nombres intuitivos alineados con su propósito.

---

## 💡 Recomendaciones de uso

- Este archivo debe ser importado desde todos los módulos `SXX_*.py`.
- No debe contener lógica de ejecución (`if __name__ == "__main__"`), solo definiciones.
- Se recomienda mantener este archivo sincronizado y controlado con control de versiones (Git).

---

## ✍️ Autoría

- **Autor:** EWE - Zeetrex  
- **Última actualización:** 2025-03-22

---

## 🔗 Ejemplo de importación

```python
from funciones_forecast import (
    get_forecast,
    Open_Conn_Postgres,
    update_execution
)
```

---

## 📦 Requisitos

- Python ≥ 3.8
- Librerías: `pandas`, `psycopg2`, `pyodbc`, `statsmodels`, `dotenv`, `matplotlib`, `numpy`, `uuid`, `getpass`