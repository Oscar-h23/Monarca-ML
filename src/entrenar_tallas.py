"""Entrenamiento experimental del clasificador de ajuste de tallas.

El dataset de entrada debe estar normalizado por src.preparar_tallas.
No combina fuentes, no activa modelos en producción y no reporta validación
con compradores reales cuando la fuente es PRUEBA.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

FEATURES = [
    "categoria", "talla_comprada", "holgura_pecho_cm",
    "holgura_cintura_cm", "holgura_cadera_cm",
]
LABELS = ["PEQUENA", "BIEN", "GRANDE"]
NUMERIC = ["holgura_pecho_cm", "holgura_cintura_cm", "holgura_cadera_cm"]


def train(csv_path: Path, output_dir: Path, source: str, seed: int = 42) -> dict:
    if source not in ("PRUEBA", "REALES"):
        raise ValueError("Fuente inválida: PRUEBA o REALES")
    df = pd.read_csv(csv_path, dtype={"categoria": str, "talla_comprada": str, "ajuste": str})
    required = set(FEATURES + ["ajuste"])
    if not required.issubset(df.columns):
        raise ValueError(f"Faltan columnas: {sorted(required - set(df.columns))}")
    df = df[FEATURES + ["ajuste"]].copy()
    if df.isna().any(axis=None) and df[["categoria", "talla_comprada", "ajuste"]].isna().any(axis=None):
        raise ValueError("Las categorías, tallas y etiquetas no pueden estar vacías")
    if not df["ajuste"].isin(LABELS).all():
        raise ValueError("Hay etiquetas de ajuste desconocidas")
    if len(df) < 30 or df["ajuste"].value_counts().min() < 5 or df["ajuste"].nunique() != 3:
        raise ValueError("Se requieren al menos 30 registros y 5 por cada una de las tres clases")
    for column in NUMERIC:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if df[NUMERIC].notna().sum().sum() == 0:
        raise ValueError("No se encontraron holguras numéricas")

    # En el dataset sintético puede haber filas correlacionadas. Esta prueba
    # demuestra funcionamiento técnico, NO precisión clínica/comercial real.
    x_train, x_hold, y_train, y_hold = train_test_split(
        df[FEATURES], df["ajuste"], test_size=0.30, stratify=df["ajuste"], random_state=seed
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_hold, y_hold, test_size=0.5, stratify=y_hold, random_state=seed
    )

    def pipeline(classifier):
        transform = ColumnTransformer([
            ("numeric", Pipeline([
                ("impute", SimpleImputer(strategy="constant", fill_value=0)),
                ("scale", StandardScaler()),
            ]), NUMERIC),
            ("categories", OneHotEncoder(handle_unknown="ignore"), ["categoria", "talla_comprada"]),
        ])
        return Pipeline([("features", transform), ("classifier", classifier)])

    models = {
        "knn": pipeline(KNeighborsClassifier(n_neighbors=5)),
        "arbol": pipeline(DecisionTreeClassifier(max_depth=5, min_samples_leaf=3, random_state=seed)),
    }
    validation = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        predicted = model.predict(x_val)
        validation[name] = {
            "accuracy": float(accuracy_score(y_val, predicted)),
            "macro_f1": float(f1_score(y_val, predicted, labels=LABELS, average="macro", zero_division=0)),
        }
    winner = sorted(models, key=lambda n: (-validation[n]["macro_f1"], -validation[n]["accuracy"], n))[0]
    # No se reentrena con validación: el test se conserva sin exposición previa.
    model = models[winner]
    y_pred = model.predict(x_test)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"tallas_{source.lower()}.joblib"
    joblib.dump(model, model_path)
    report = {
        "source": source,
        "experimental": True,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "rows": int(len(df)),
        "splits": {"train": len(x_train), "validation": len(x_val), "test": len(x_test)},
        "class_counts": {k: int(v) for k, v in df["ajuste"].value_counts().items()},
        "algorithm": winner,
        "validation": validation,
        "test": {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "macro_f1": float(f1_score(y_test, y_pred, labels=LABELS, average="macro", zero_division=0)),
            "confusion_matrix_labels": LABELS,
            "confusion_matrix": confusion_matrix(y_test, y_pred, labels=LABELS).tolist(),
            "classification_report": classification_report(y_test, y_pred, labels=LABELS, output_dict=True, zero_division=0),
        },
        "limitation": "Las métricas en PRUEBA miden etiquetas sintéticas; no validan compradores reales."
        if source == "PRUEBA" else "Dataset real: validar diversidad de clientes y ausencia de fuga antes de producción.",
        "model_file": model_path.name,
    }
    (output_dir / f"tallas_{source.lower()}_metricas.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--entrada", required=True, type=Path)
    parser.add_argument("--salida", required=True, type=Path)
    parser.add_argument("--fuente", choices=["PRUEBA", "REALES"], required=True)
    parser.add_argument("--semilla", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(train(args.entrada, args.salida, args.fuente, args.semilla), ensure_ascii=False, indent=2))
