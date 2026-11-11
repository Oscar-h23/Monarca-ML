"""Grafo de compatibilidad y DFS con verificación de todos los pares."""
from itertools import combinations

import numpy as np
import pandas as pd

from .preparar_datos import atributos, candidatos


def clave(prenda):
    return (prenda["id_producto"], prenda["color"])


def construir_grafo(catalogo, clasificador, regresor):
    grafo = {clave(p): {} for p in catalogo.to_dict("records")}
    pares = candidatos(catalogo)
    if not pares:
        return grafo
    tabla = pd.DataFrame([atributos(a, b) for a, b in pares])
    aceptados = clasificador.predict(tabla)
    puntuaciones = np.clip(regresor.predict(tabla), 1, 5)
    for (a, b), aceptado, puntuacion in zip(pares, aceptados, puntuaciones):
        if aceptado:
            grafo[clave(a)][clave(b)] = float(puntuacion)
            grafo[clave(b)][clave(a)] = float(puntuacion)
    return grafo


def buscar_outfits(origen, grafo, prendas, limite=10, max_vecinos=20):
    """DFS de profundidad tres; candidatos acotados y conjuntos sin duplicados."""
    encontrados = {}

    def dfs(camino):
        if len(camino) == 3:
            pares = list(combinations(camino, 2))
            puntuacion = sum(grafo[a][b] for a, b in pares) / len(pares)
            encontrados[tuple(sorted(camino))] = {
                "prendas": [{"idProducto": p[0], "color": p[1]} for p in camino],
                "puntuacion": round(puntuacion, 3),
            }
            return
        vecinos = sorted(grafo[origen], key=lambda p: (-grafo[origen][p], p))[:max_vecinos]
        ids = {p[0] for p in camino}
        categorias = {prendas[p]["categoria"] for p in camino}
        for vecino in vecinos:
            if vecino[0] in ids or prendas[vecino]["categoria"] in categorias:
                continue
            if all(vecino in grafo[p] for p in camino):
                dfs(camino + [vecino])

    dfs([origen])
    return sorted(encontrados.values(), key=lambda outfit: (-outfit["puntuacion"], str(outfit["prendas"])))[:limite]


def generar(catalogo, clasificador, regresor):
    grafo = construir_grafo(catalogo, clasificador, regresor)
    prendas = {clave(p): p for p in catalogo.to_dict("records")}
    return [
        {"idProducto": origen[0], "color": origen[1],
         "outfits": buscar_outfits(origen, grafo, prendas)}
        for origen in sorted(grafo)
    ]
