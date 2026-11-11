"""Generador reproducible de datos SINTÉTICOS para aprender el flujo."""
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


def generar_demo(salida="data/demo"):
    rng = np.random.default_rng(23)
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    filas = []
    colores = ["negro", "blanco", "azul", "rojo", "beige"]
    for i in range(80):
        categoria = ["Tops", "Bottoms", "Calzado", "Accesorios"][i % 4]
        filas.append({"id_producto": str(i + 1), "nombre": f"Demo {categoria} {i + 1}",
                      "categoria": categoria, "color": colores[int(rng.integers(5))],
                      "estilo": ["casual", "formal", "deportivo"][int(rng.integers(3))],
                      "precio": round(float(rng.uniform(25, 180)), 2)})
    catalogo = pd.DataFrame(filas)
    valoraciones = []
    for a, b in combinations(filas, 2):
        if a["categoria"] == b["categoria"]:
            continue
        # Regla simulada con ruido: las métricas solo reflejan esta simulación.
        puntuacion = 2.3 + 2 * (a["estilo"] == b["estilo"])
        puntuacion += 0.3 * (a["color"] in {"negro", "blanco", "beige"} or b["color"] in {"negro", "blanco", "beige"})
        puntuacion += float(rng.normal(0, 0.5))
        valoraciones.append({"id_producto_a": a["id_producto"], "color_a": a["color"],
                             "id_producto_b": b["id_producto"], "color_b": b["color"],
                             "valoracion": round(float(np.clip(puntuacion, 1, 5)), 2)})
    catalogo.to_csv(salida / "catalogo.csv", index=False)
    pd.DataFrame(valoraciones).to_csv(salida / "valoraciones.csv", index=False)


if __name__ == "__main__":
    generar_demo()
