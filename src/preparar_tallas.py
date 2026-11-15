"""Prepara observaciones reales para clasificación de ajuste de tallas.

Entrada: CSV exportado administrativamente desde la consulta de
docs/dataset-tallas.md. No contiene nombres ni identificadores de compradores.
Los faltantes se descartan, sin imputación ni etiquetas sintéticas.
"""
import argparse
import csv
from pathlib import Path

DIMENSIONES = {
    "Tops": ("pecho", "cintura"),
    "Bottoms": ("cintura", "cadera"),
    "Vestidos": ("pecho", "cintura", "cadera"),
}
AJUSTES = {"PEQUENA", "BIEN", "GRANDE"}
SALIDA = ["categoria", "talla_comprada", "holgura_pecho_cm",
          "holgura_cintura_cm", "holgura_cadera_cm", "ajuste"]

def preparar(entrada: Path, salida: Path) -> dict[str, int]:
    totales = {"filas": 0, "validas": 0, "incompletas": 0, "invalidas": 0}
    filas = []
    with entrada.open(newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)
        necesarias = {"categoria", "talla_comprada", "ajuste",
                       "busto_cm", "cintura_cm", "cadera_cm",
                       "prenda_pecho_cm", "prenda_cintura_cm", "prenda_cadera_cm"}
        if not lector.fieldnames or not necesarias.issubset(lector.fieldnames):
            raise ValueError("El CSV no coincide con la consulta de exportación.")
        for fila in lector:
            totales["filas"] += 1
            categoria = fila["categoria"]
            if categoria not in DIMENSIONES or fila["ajuste"] not in AJUSTES or not fila["talla_comprada"]:
                totales["invalidas"] += 1
                continue
            holguras = {k: "" for k in ("pecho", "cintura", "cadera")}
            incompleta = False
            invalida = False
            for dim in DIMENSIONES[categoria]:
                cuerpo = "busto_cm" if dim == "pecho" else dim + "_cm"
                prenda = "prenda_" + ("pecho" if dim == "pecho" else dim) + "_cm"
                if not fila[cuerpo] or not fila[prenda]:
                    incompleta = True
                    break
                try:
                    valor_cuerpo = float(fila[cuerpo])
                    valor_prenda = float(fila[prenda])
                    if not (25 <= valor_cuerpo <= 300 and 25 <= valor_prenda <= 300):
                        invalida = True
                        break
                    holguras[dim] = round(valor_prenda - valor_cuerpo, 2)
                except (TypeError, ValueError):
                    invalida = True
                    break
            if invalida:
                totales["invalidas"] += 1
                continue
            if incompleta:
                totales["incompletas"] += 1
                continue
            filas.append({
                "categoria": categoria,
                "talla_comprada": fila["talla_comprada"],
                "holgura_pecho_cm": holguras["pecho"],
                "holgura_cintura_cm": holguras["cintura"],
                "holgura_cadera_cm": holguras["cadera"],
                "ajuste": fila["ajuste"],
            })
            totales["validas"] += 1
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=SALIDA)
        escritor.writeheader()
        escritor.writerows(filas)
    return totales

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--entrada", type=Path, required=True)
    parser.add_argument("--salida", type=Path, default=Path("data/reales/tallas_entrenamiento.csv"))
    args = parser.parse_args()
    print(preparar(args.entrada, args.salida))
