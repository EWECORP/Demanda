import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(14, 10))

# Elementos principales de la arquitectura
elements = [
    {"text": "Backoffice GDN\n(RMS / ITIM / RevPlan)", "xy": (4, 9), "color": "#DDEEFF"},
    {"text": "Middleware\n(Capa de Servicios REST/MQ)", "xy": (4, 7), "color": "#FFD580"},
    {"text": "Facility 7461\n(Operador Logístico)", "xy": (4, 5), "color": "#C1F0C1"},
    {"text": "WMS Propio del\nOperador", "xy": (4, 3), "color": "#FFCCCC"},
    {"text": "CD Físico / Logística\n(Recepción / Despacho)", "xy": (4, 1), "color": "#CCCCFF"},
]

# Dibujar rectángulos con texto
for elem in elements:
    rect = patches.FancyBboxPatch((elem["xy"][0], elem["xy"][1]), 4, 1.4,
                                  boxstyle="round,pad=0.1", linewidth=1, edgecolor="black",
                                  facecolor=elem["color"])
    ax.add_patch(rect)
    ax.text(elem["xy"][0] + 2, elem["xy"][1] + 0.7, elem["text"],
            ha="center", va="center", fontsize=10, weight="bold")

# Dibujar flechas
for y in range(9, 2, -2):
    ax.annotate("", xy=(6, y), xytext=(6, y-0.6),
                arrowprops=dict(facecolor='black', arrowstyle="->", lw=1.5))

# Estética general
ax.set_xlim(0, 12)
ax.set_ylim(0, 11)
ax.axis("off")
plt.title("Esquema de Arquitectura Propuesta - Integración con Operador Logístico", fontsize=14, weight="bold")
plt.tight_layout()
plt.show()
