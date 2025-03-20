"""
Nombre del módulo: M00_TEMPLATE_PRONOSTICO.py

Descripción:
Este archivo sirve como plantilla base para la creación de nuevos módulos de pronóstico
basados en el motor y lógica definidos en funciones_forecast.py.

Autor: [Tu nombre o equipo]
Fecha de creación: [YYYY-MM-DD]
"""

# Solo importa lo necesario desde el módulo de funciones
from funciones_forecast import (
    get_forecast,
    get_excecution_excecute_by_status,
    get_execution_parameter,
    update_execution
)

# También podés importar funciones adicionales si tu módulo las necesita

def ejecutar_forecast_personalizado():
    """
    Ejecuta un forecast para un proveedor específico, ideal para pruebas o desarrollos.
    """
    # Parametrización
    id_proveedor = 12345
    nombre_proveedor = "Proveedor_TEST"
    algoritmo = "ALGO_01"
    ventana = 30
    f1, f2, f3 = 70, 20, 10
    fecha_base = None  # Puede ser datetime.today() o una fecha específica

    print(f"🔍 Ejecutando forecast para {nombre_proveedor} usando {algoritmo} con ventana {ventana} días...")
    
    try:
        get_forecast(id_proveedor, nombre_proveedor, ventana, algoritmo, f1, f2, f3, fecha_base)
        print("✅ Forecast ejecutado correctamente.")
    except Exception as e:
        print(f"❌ Error al ejecutar forecast: {e}")

# Punto de entrada
if __name__ == "__main__":
    ejecutar_forecast_personalizado()