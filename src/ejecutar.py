"""Entrada CLI y función usada por Colab."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .analizar_patrones import analizar
from .entrenar import entrenar
from .generar_outfits import generar
from .preparar_datos import cargar_datos, dividir_productos, tabla_pares


def guardar_json(path, contenido):
    # Reemplazo atómico de cada archivo. outfits.json se publica al final.
    temporal = path.with_suffix(".tmp")
    temporal.write_text(json.dumps(contenido, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    temporal.replace(path)


def ejecutar(catalogo_path, valoraciones_path, salida="resultados", semilla=23, demo=False):
    salida = Path(salida)
    catalogo, pares = cargar_datos(catalogo_path, valoraciones_path)
    tablas, grupos = dividir_productos(catalogo, pares, semilla)
    clasificador, regresor, metricas, reglas = entrenar(tablas, semilla)
    estadisticas, clusters, patrones = analizar(catalogo, tabla_pares(catalogo, pares))
    # Después de evaluar, reajustar los modelos elegidos con todas las etiquetas.
    todas = tabla_pares(catalogo, pares)
    clasificador.fit(todas, todas.valoracion >= 4)
    regresor.fit(todas, todas.valoracion)
    recomendaciones = generar(catalogo, clasificador, regresor)
    salida.mkdir(parents=True, exist_ok=True)
    # Escribir desde un staging distinto por ejecución evita archivos temporales compartidos.
    with tempfile.TemporaryDirectory(dir=salida) as carpeta:
        staging = Path(carpeta)
        meta = {
            "versionContrato": 1, "generadoEn": datetime.now(timezone.utc).isoformat(),
            "demo": demo, "semilla": semilla,
            "catalogoSha256": hashlib.sha256(Path(catalogo_path).read_bytes()).hexdigest(),
            "clasificador": metricas["seleccionado"],
            "aviso": "Datos sintéticos educativos" if demo else "Compatibilidad aprendida de las valoraciones suministradas",
            "busqueda": {"piezas": 3, "maxVecinos": 20, "maxOutfitsPorOrigen": 10},
            "recomendaciones": recomendaciones,
        }
        guardar_json(staging / "metricas.json", {**metricas, "demo": demo, "productos_por_particion": grupos,
                                                "evaluacion": "Modelos ajustados solo con entrenamiento; productos disjuntos. Los pares entre particiones se excluyen."})
        guardar_json(staging / "estadisticas.json", estadisticas)
        guardar_json(staging / "outfits.json", meta)
        clusters.to_csv(staging / "clusters.csv", index=False)
        patrones.to_csv(staging / "patrones.csv", index=False)
        (staging / "arbol_evaluado.txt").write_text(reglas, encoding="utf-8")
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        axes[0].hist(catalogo.precio, bins=10, edgecolor="white")
        axes[0].set(xlabel="Precio S/", ylabel="Productos y colores", title="Distribución de precios")
        axes[1].bar(list(metricas["prueba"]), [m["f1"] for m in metricas["prueba"].values()])
        axes[1].set(ylabel="F1", ylim=(0, 1.05), title="Evaluación en productos reservados")
        axes[1].tick_params(axis="x", rotation=25)
        fig.tight_layout()
        fig.savefig(staging / "analisis.png", dpi=140)
        plt.close(fig)
        for path in sorted(staging.iterdir(), key=lambda p: p.name == "outfits.json"):
            path.replace(salida / path.name)
    return metricas


def main():
    parser = argparse.ArgumentParser(description="Analizador de patrones y outfits Monarka ML")
    parser.add_argument("--catalogo", default="data/demo/catalogo.csv")
    parser.add_argument("--valoraciones", default="data/demo/valoraciones.csv")
    parser.add_argument("--salida", default="resultados")
    parser.add_argument("--semilla", type=int, default=23)
    args = parser.parse_args()
    demo = Path(args.catalogo).resolve() == Path("data/demo/catalogo.csv").resolve()
    metricas = ejecutar(args.catalogo, args.valoraciones, args.salida, args.semilla, demo)
    print(json.dumps({"demo": demo, "seleccionado": metricas["seleccionado"], "salida": args.salida}, ensure_ascii=False))


if __name__ == "__main__":
    main()
