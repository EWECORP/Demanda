import matplotlib.pyplot as plt


grafico = {'articulo': 166, 'sucursal': 1,
            'fechas': ['2025-02-13', '2025-02-15', '2025-02-17', '2025-02-20', '2025-02-23', '2025-02-24', 
                       '2025-02-25', '2025-02-28', '2025-03-01', '2025-03-02', '2025-03-04', '2025-03-05', '2025-03-06', 
                       '2025-03-07', '2025-03-08', '2025-03-11', '2025-03-12', '2025-03-13', '2025-03-14', '2025-03-15', 
                       '2025-03-18', '2025-03-21', '2025-03-22', '2025-03-23', '2025-03-24', '2025-03-26', '2025-03-28', '2025-03-29', 
                       '2025-03-30', '2025-03-31', '2025-03-31', '2025-04-01', '2025-04-02', '2025-04-03', '2025-04-04', '2025-04-04'],
            'unidades': [4.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 3.0, 1.0, 7.0, 3.0, 2.0, 1.0, 1.0, 1.0, 2.0, 4.0, 1.0, 1.0, 1.0,
                          2.0, 2.0, 4.0, 1.0, 5.0, 4.0, 1.0, 1.0, 4.0, 2.0, 8.0, 1.0, 3.0], 
            'media_movil': [0, 0, 0, 0, 0, 0, 1.5714285714285714, 1.2857142857142858, 1.2857142857142858, 1.2857142857142858, 1.5714285714285714, 1.5714285714285714, 2.4285714285714284, 2.7142857142857144, 2.7142857142857144, 2.5714285714285716, 2.5714285714285716, 2.2857142857142856, 2.4285714285714284, 2.0, 1.7142857142857142, 1.5714285714285714, 1.5714285714285714, 1.7142857142857142, 1.8571428571428572, 2.142857142857143, 1.7142857142857142, 2.2857142857142856, 2.7142857142857144, 2.7142857142857144, 2.5714285714285716, 2.857142857142857, 2.5714285714285716, 3.5714285714285716, 3.0, 2.857142857142857], 
            'semana_num': [7, 8, 9, 10, 11, 12, 13, 14], 
            'ventas_semanales': [6.0, 3.0, 7.0, 16.0, 9.0, 5.0, 16.0, 20.0], 
            'forecast': 15.0, 'ventas_last': 14.0, 
            'ventas_previous': 10.0, 'ventas_same_year': 9.0, 
            'average': 1.484, 'ventas_ultimos_30': np.float64(62.0), 
            'ventas_previos_30': np.float64(20.0), 
            'ventas_anio_anterior': np.float64(0.0)}

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

graficar_desde_datos_json(grafico)
