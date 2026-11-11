"""Validación y atributos simétricos para pares de producto y color."""
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

CATEGORIAS = {"Tops", "Bottoms", "Calzado", "Accesorios"}
CATEGORICAS = ["categorias", "colores", "estilos"]
NUMERICAS = ["mismo_estilo", "mismo_color", "diferencia_precio", "precio_promedio"]


def cargar_datos(catalogo_path, valoraciones_path):
    catalogo = pd.read_csv(catalogo_path, dtype={"id_producto": str, "color": str})
    valoraciones = pd.read_csv(
        valoraciones_path,
        dtype={"id_producto_a": str, "id_producto_b": str, "color_a": str, "color_b": str},
    )
    requeridas = {"id_producto", "nombre", "categoria", "color", "estilo", "precio"}
    if not requeridas.issubset(catalogo.columns):
        raise ValueError(f"Faltan columnas del catálogo: {requeridas - set(catalogo.columns)}")
    etiquetas = {"id_producto_a", "color_a", "id_producto_b", "color_b", "valoracion"}
    if not etiquetas.issubset(valoraciones.columns):
        raise ValueError(f"Faltan columnas de valoraciones: {etiquetas - set(valoraciones.columns)}")
    if catalogo.empty or valoraciones.empty:
        raise ValueError("El catálogo y las valoraciones deben contener filas.")
    if catalogo[list(requeridas)].isna().any().any() or valoraciones[list(etiquetas)].isna().any().any():
        raise ValueError("Hay datos obligatorios vacíos.")
    texto = list(requeridas - {"precio"})
    for columna in texto:
        catalogo[columna] = catalogo[columna].str.strip()
        if catalogo[columna].eq("").any():
            raise ValueError(f"Valores vacíos en {columna}.")
    for columna in etiquetas - {"valoracion"}:
        valoraciones[columna] = valoraciones[columna].str.strip()
    catalogo["precio"] = pd.to_numeric(catalogo.precio, errors="raise")
    valoraciones["valoracion"] = pd.to_numeric(valoraciones.valoracion, errors="raise")
    if not np.isfinite(catalogo.precio).all() or (catalogo.precio < 0).any():
        raise ValueError("Los precios deben ser finitos y no negativos.")
    if not valoraciones.valoracion.between(1, 5).all():
        raise ValueError("Las valoraciones deben estar entre 1 y 5.")
    if not set(catalogo.categoria).issubset(CATEGORIAS):
        raise ValueError(f"Categorías admitidas: {sorted(CATEGORIAS)}")
    if catalogo.duplicated(["id_producto", "color"]).any():
        raise ValueError("Debe existir una fila por producto y color, agrupando las tallas.")
    if (catalogo.groupby("id_producto").categoria.nunique() > 1).any():
        raise ValueError("Un producto debe tener una sola categoría.")
    prendas = catalogo.set_index(["id_producto", "color"]).to_dict("index")
    # Promediar evaluadores y pares invertidos evita duplicados entre particiones.
    pares = {}
    for fila in valoraciones.itertuples(index=False):
        a = (fila.id_producto_a, fila.color_a)
        b = (fila.id_producto_b, fila.color_b)
        if a not in prendas or b not in prendas:
            raise ValueError(f"La valoración referencia una prenda inexistente: {a}, {b}")
        if a[0] == b[0] or prendas[a]["categoria"] == prendas[b]["categoria"]:
            raise ValueError("Evalúa pares de productos distintos y categorías distintas.")
        clave = tuple(sorted((a, b)))
        pares.setdefault(clave, []).append(fila.valoracion)
    return catalogo, [(a, b, float(np.mean(v))) for (a, b), v in sorted(pares.items())]


def atributos(a, b):
    return {
        "categorias": "|".join(sorted([a["categoria"], b["categoria"]])),
        "colores": "|".join(sorted([a["color"], b["color"]])),
        "estilos": "|".join(sorted([a["estilo"], b["estilo"]])),
        "mismo_estilo": int(a["estilo"] == b["estilo"]),
        "mismo_color": int(a["color"] == b["color"]),
        "diferencia_precio": abs(a["precio"] - b["precio"]),
        "precio_promedio": (a["precio"] + b["precio"]) / 2,
    }


def tabla_pares(catalogo, pares):
    prendas = catalogo.set_index(["id_producto", "color"], drop=False).to_dict("index")
    return pd.DataFrame([
        {**atributos(prendas[a], prendas[b]), "id_a": a[0], "id_b": b[0], "valoracion": v}
        for a, b, v in pares
    ])


def dividir_productos(catalogo, pares, semilla):
    # Todos los colores y todos los pares del producto quedan en una partición.
    productos = sorted(catalogo.id_producto.unique())
    if len(productos) < 15:
        raise ValueError("Se requieren al menos 15 productos para separar entrenamiento, validación y prueba.")
    train, resto = train_test_split(productos, test_size=0.4, random_state=semilla)
    validacion, prueba = train_test_split(resto, test_size=0.5, random_state=semilla)
    grupos = {"entrenamiento": train, "validacion": validacion, "prueba": prueba}
    tablas = {}
    for nombre, ids in grupos.items():
        seleccion = [p for p in pares if p[0][0] in ids and p[1][0] in ids]
        if not seleccion:
            raise ValueError(f"Faltan valoraciones dentro de la partición {nombre}.")
        tablas[nombre] = tabla_pares(catalogo, seleccion)
        if (tablas[nombre].valoracion >= 4).nunique() < 2:
            raise ValueError(f"{nombre} necesita pares recomendables y poco recomendables. Añade valoraciones.")
    return tablas, grupos


def candidatos(catalogo):
    prendas = catalogo.to_dict("records")
    return [(a, b) for a, b in combinations(prendas, 2)
            if a["id_producto"] != b["id_producto"] and a["categoria"] != b["categoria"]]
