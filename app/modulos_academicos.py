"""Módulos académicos aislados: clustering, regresión y búsqueda heurística.

Las observaciones de PRUEBA son sintéticas y las métricas no acreditan
rendimiento con consumidores reales. El backend controla la fuente y acceso.
"""
from __future__ import annotations

from heapq import heappush, heappop
import math
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.linear_model import LinearRegression
from sklearn.metrics import silhouette_score, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler


def _frame(rows, columns, minimum=10):
    if len(rows) < minimum or len(rows) > 5000:
        raise ValueError(f"Se necesitan entre {minimum} y 5000 registros")
    df = pd.DataFrame(rows)
    absent = set(columns) - set(df.columns)
    if absent:
        raise ValueError("Columnas faltantes: " + ", ".join(sorted(absent)))
    return df.copy()


def segmentar(rows, fuente):
    cols = ["compras_ultimos_12_meses", "gasto_total_12_meses_soles",
            "ticket_promedio_soles", "dias_desde_ultima_compra",
            "visitas_web_ultimos_30_dias", "meses_antiguedad",
            "descuentos_usados_12_meses"]
    df = _frame(rows, cols, 15)
    x = df[cols].apply(pd.to_numeric, errors="coerce")
    x = x.fillna(x.median()).fillna(0)
    scaled = StandardScaler().fit_transform(x)
    km = KMeans(n_clusters=4, random_state=42, n_init=10).fit(scaled)
    dbscan = DBSCAN(eps=1.6, min_samples=4).fit(scaled)
    group = km.labels_.tolist()
    db_group = dbscan.labels_.tolist()
    unique = sorted(set(db_group) - {-1})
    def sil(labels):
        groups = set(labels) - {-1}
        if len(groups) < 2 or len(groups) >= len(labels):
            return None
        try:
            score = silhouette_score(scaled, labels)
            return round(float(score), 4)
        except ValueError:
            return None
    output = []
    for i in range(4):
        idx = [j for j, v in enumerate(group) if v == i]
        output.append({
            "segmento": i + 1,
            "clientes": len(idx),
            "compras_promedio": round(float(x.iloc[idx]["compras_ultimos_12_meses"].mean()), 2),
            "gasto_promedio_soles": round(float(x.iloc[idx]["gasto_total_12_meses_soles"].mean()), 2),
            "dias_desde_ultima_compra_promedio": round(float(x.iloc[idx]["dias_desde_ultima_compra"].mean()), 1),
        })
    return {
        "modulo": "CLUSTERING", "fuente": fuente, "registros": len(df),
        "algoritmos": {
            "kmeans": {"grupos": 4, "silhouette": sil(group)},
            "dbscan": {"grupos": len(unique), "ruido": db_group.count(-1), "silhouette": sil(db_group)}
        },
        "segmentos": output,
        "interpretacion": "Grupos descriptivos, no diagnósticos ni etiquetas reales."
    }


def demanda(rows, fuente):
    cols = ["fecha_inicio_semana", "id_producto", "precio_soles",
            "descuento_porcentaje", "visitas_producto_semana",
            "unidades_vendidas_semana"]
    df = _frame(rows, cols, 30)
    df["fecha_inicio_semana"] = pd.to_datetime(df["fecha_inicio_semana"], errors="coerce")
    if df["fecha_inicio_semana"].isna().any():
        raise ValueError("Fechas inválidas")
    df = df.sort_values(["fecha_inicio_semana", "id_producto"]).reset_index(drop=True)
    if df["fecha_inicio_semana"].nunique() < 5:
        raise ValueError("Se necesitan cinco semanas diferentes como mínimo")
    inputs = ["precio_soles", "descuento_porcentaje", "visitas_producto_semana"]
    for col in inputs + ["unidades_vendidas_semana"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[inputs + ["unidades_vendidas_semana"]].isna().any().any():
        raise ValueError("Las variables de demanda deben estar completas")
    # Corte cronológico para reducir fuga temporal. Los datos de visitas de
    # la semana son conocidos sólo al terminarla: no es pronóstico futuro real.
    dates = sorted(df["fecha_inicio_semana"].unique())
    boundary = dates[max(1, int(len(dates) * .8))]
    train = df[df["fecha_inicio_semana"] < boundary]
    test = df[df["fecha_inicio_semana"] >= boundary]
    if len(train) < 15 or len(test) < 5:
        raise ValueError("Separación temporal insuficiente")
    model = LinearRegression().fit(train[inputs], train["unidades_vendidas_semana"])
    predicted = np.maximum(0, model.predict(test[inputs]))
    baseline = np.full(len(test), float(train["unidades_vendidas_semana"].mean()))
    return {
        "modulo": "DEMANDA", "fuente": fuente, "algoritmo": "regresion_lineal",
        "registros": len(df), "entrenamiento": len(train), "prueba": len(test),
        "semanas": len(dates),
        "mae_unidades": round(float(mean_absolute_error(test["unidades_vendidas_semana"], predicted)), 3),
        "mae_baseline_unidades": round(float(mean_absolute_error(test["unidades_vendidas_semana"], baseline)), 3),
        "r2_prueba": round(float(r2_score(test["unidades_vendidas_semana"], predicted)), 4) if len(test) > 1 else None,
        "ejemplos": [{"producto": str(row["id_producto"]), "real": int(row["unidades_vendidas_semana"]),
                      "estimado": round(float(predicted[i]), 1)}
                     for i, (_, row) in enumerate(test.head(5).iterrows())],
        "advertencia": "Evaluación retrospectiva con visitas conocidas; no demuestra pronóstico de demanda futura."
    }


def outfits(rows, fuente, presupuesto=None):
    cols = ["id_variante_superior","superior","precio_superior_soles",
            "id_variante_inferior","inferior","precio_inferior_soles",
            "puntuacion_estilo_simulada_0_100","presupuesto_soles"]
    df = _frame(rows, cols, 1)
    if presupuesto is None:
        presupuesto = float(pd.to_numeric(df["presupuesto_soles"]).median())
    presupuesto = float(presupuesto)
    if not math.isfinite(presupuesto) or not 20 <= presupuesto <= 2000:
        raise ValueError("Presupuesto debe estar entre S/20 y S/2000")
    # El espacio de búsqueda lo forman combinaciones distintas presentes
    # en el escenario; no se presenta como combinaciones evaluadas por usuarios.
    candidates = {}
    for row in df.to_dict("records"):
        try:
            price = float(row["precio_superior_soles"])+float(row["precio_inferior_soles"])
            style = float(row["puntuacion_estilo_simulada_0_100"])
        except (ValueError, TypeError):
            continue
        if not math.isfinite(price) or not math.isfinite(style) or price <= 0 or price > presupuesto:
            continue
        key=(int(row["id_variante_superior"]),int(row["id_variante_inferior"]))
        candidates[key] = {"superior":str(row["superior"]), "inferior":str(row["inferior"]),
                           "precio_soles":round(price,2), "estilo":max(0,min(100,style)),
                           "id_variantes":list(key)}
    if not candidates:
        return {"modulo":"OUTFITS", "fuente":fuente,"presupuesto_soles":presupuesto,
                "factibles":0,"mensaje":"No existe una combinación dentro del presupuesto"}
    values = list(candidates.values())
    # Puntaje reproducible que recompensa estilo y aprovechamiento prudente del presupuesto.
    def score(v):
        return .8*v["estilo"]+.2*100*v["precio_soles"]/presupuesto
    # Búsqueda A*: desde un estado vacío, se elige superior e inferior.
    # El costo de cada meta es 100 - puntuación, nunca negativo.
    # La heurística admisible es 0, por lo que A* equivale aquí a
    # búsqueda de costo uniforme sobre metas de profundidad 2.
    heap=[(0.0, 0, None)]
    best=None
    while heap:
        cost, depth, index=heappop(heap)
        if depth==2:
            best=values[index]
            break
        if depth==0:
            # Estados parciales con cada variante superior distinta.
            by_top={}
            for i,v in enumerate(values):
                by_top.setdefault(v["id_variantes"][0],[]).append(i)
            for top,indices in by_top.items():
                heappush(heap,(0.0,1,indices))
        else:
            for i in index:
                heappush(heap,(100-score(values[i]),2,i))
    if best is None:
        raise ValueError("No hay combinaciones factibles")
    # Hill Climbing: vecinos del orden del catálogo, con tres reinicios.
    # Puede detenerse en un óptimo local; no realiza búsqueda exhaustiva.
    hill=None
    for seed in (0,len(values)//2,len(values)-1):
        current=seed
        while True:
            neighbours=[i for i in (current-1,current+1) if 0<=i<len(values)]
            improves=[i for i in neighbours if score(values[i])>score(values[current])+1e-9]
            if not improves:
                break
            current=max(improves,key=lambda i:score(values[i]))
        if hill is None or score(values[current])>score(hill):
            hill=values[current]
    return {
        "modulo":"OUTFITS","fuente":fuente,"presupuesto_soles":round(presupuesto,2),
        "escenarios":len(df),"factibles":len(values),
        "a_estrella":{"combinacion":best,"puntuacion":round(score(best),2)},
        "hill_climbing":{"combinacion":hill,"puntuacion":round(score(hill),2)},
        "nota":"Búsqueda sobre combinaciones precalculadas, no aprendizaje supervisado; puntuaciones de estilo simuladas."
    }


def ejecutar(modulo, rows, fuente, presupuesto=None):
    if fuente not in {"REALES","PRUEBA"}:
        raise ValueError("Fuente inválida")
    if modulo=="CLUSTERING":
        return segmentar(rows, fuente)
    if modulo=="DEMANDA":
        return demanda(rows, fuente)
    if modulo=="OUTFITS":
        return outfits(rows, fuente, presupuesto)
    raise ValueError("Módulo no compatible")
