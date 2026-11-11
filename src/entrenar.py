"""Comparación con validación y evaluación final aislada por producto."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

from .preparar_datos import CATEGORICAS, NUMERICAS


def pipeline(modelo):
    return Pipeline([
        ("preparacion", ColumnTransformer([
            ("categoricas", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAS),
            ("numericas", StandardScaler(), NUMERICAS),
        ])),
        ("modelo", modelo),
    ])


def medir_clasificacion(modelo, tabla):
    y = tabla.valoracion >= 4
    pred = modelo.predict(tabla)
    return {
        "accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0), "f1": f1_score(y, pred, zero_division=0),
    }


def entrenar(tablas, semilla):
    train, val, test = (tablas[k] for k in ("entrenamiento", "validacion", "prueba"))
    modelos = {
        "arbol": pipeline(DecisionTreeClassifier(max_depth=4, min_samples_leaf=3, random_state=semilla)),
        "logistica": pipeline(LogisticRegression(max_iter=2000, random_state=semilla)),
        "baseline_mayoritaria": pipeline(DummyClassifier(strategy="most_frequent")),
    }
    validacion = {}
    for nombre, modelo in modelos.items():
        modelo.fit(train, train.valoracion >= 4)
        validacion[nombre] = medir_clasificacion(modelo, val)
    ganador = max(["arbol", "logistica"], key=lambda n: validacion[n]["f1"])
    # Prueba se consulta una vez después de elegir el clasificador con validación.
    prueba = {nombre: medir_clasificacion(modelo, test) for nombre, modelo in modelos.items()}
    regla = test.mismo_estilo == 1
    prueba["baseline_mismo_estilo"] = {"f1": f1_score(test.valoracion >= 4, regla, zero_division=0)}
    regresor = pipeline(LinearRegression())
    regresor.fit(train, train.valoracion)
    pred = np.clip(regresor.predict(test), 1, 5)
    metricas = {
        "seleccionado": ganador, "validacion": validacion, "prueba": prueba,
        "regresion": {"mae": mean_absolute_error(test.valoracion, pred),
                      "baseline_media_mae": mean_absolute_error(test.valoracion, np.full(len(test), train.valoracion.mean())),
                      "prediccion_recortada": [1, 5]},
        "filas": {k: len(v) for k, v in tablas.items()},
        "criterio": "Recomendable si promedio de valoraciones >= 4. Selección por F1 de validación.",
    }
    arbol = modelos["arbol"]
    reglas = export_text(arbol.named_steps["modelo"], feature_names=list(arbol.named_steps["preparacion"].get_feature_names_out()))
    return modelos[ganador], regresor, metricas, reglas
