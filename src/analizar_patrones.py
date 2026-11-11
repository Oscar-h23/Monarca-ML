"""Estadísticas NumPy, patrones etiquetados y clustering exploratorio."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def analizar(catalogo, pares):
    precios = catalogo.precio.to_numpy()
    q1, q3 = np.percentile(precios, [25, 75])
    resumen = {
        "media": float(np.mean(precios)), "mediana": float(np.median(precios)),
        "desviacion": float(np.std(precios)), "minimo": float(np.min(precios)),
        "maximo": float(np.max(precios)),
        "atipicos_iqr": int(np.sum((precios < q1 - 1.5 * (q3 - q1)) | (precios > q3 + 1.5 * (q3 - q1)))),
        "unidad": "Una fila por producto y color; los atípicos se revisan y se conservan.",
    }
    transformador = ColumnTransformer([
        ("categorias", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["categoria", "color", "estilo"]),
        ("precio", StandardScaler(), ["precio"]),
    ])
    x = transformador.fit_transform(catalogo)
    unicos = len(np.unique(x, axis=0))
    opciones = []
    for k in range(2, min(5, unicos, len(catalogo) - 1) + 1):
        etiquetas = KMeans(n_clusters=k, random_state=23, n_init=10).fit_predict(x)
        if 1 < len(set(etiquetas)) < len(x):
            opciones.append((silhouette_score(x, etiquetas), k, etiquetas))
    if opciones:
        silueta, k, etiquetas = max(opciones, key=lambda opcion: opcion[0])
    else:
        silueta, k, etiquetas = None, 1, np.zeros(len(catalogo), dtype=int)
    grupos = catalogo.assign(cluster=etiquetas)
    patrones = pares.assign(recomendable=pares.valoracion >= 4).groupby(
        ["categorias", "estilos"], as_index=False
    ).agg(ejemplos=("valoracion", "size"), puntuacion_media=("valoracion", "mean"),
          proporcion_recomendable=("recomendable", "mean"))
    return {"precios": resumen, "clustering": {"k": k, "silueta": silueta}}, grupos, patrones
