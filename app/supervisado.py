"""Predicción experimental a partir de un artefacto entrenado por el servidor.

Solo se acepta un artefacto obtenido por Spring Boot de la tabla privada de
modelos; nunca debe aceptarse este campo desde el navegador. joblib utiliza
pickle y NO es seguro deserializar modelos de procedencia desconocida.
"""
import base64
import io
from math import isfinite

import joblib
import pandas as pd
from .recomendacion import DIMENSIONES, Resultado, _validar_medida


def recomendar_supervisado(categoria, medidas_cliente, variantes, modelo_base64):
    if categoria not in DIMENSIONES or len(modelo_base64) > 2_000_000:
        return None
    raw = base64.b64decode(modelo_base64, validate=True)
    if len(raw) > 1_500_000:
        return None
    model = joblib.load(io.BytesIO(raw))
    dimensiones = DIMENSIONES[categoria]
    medidas = {k: _validar_medida(medidas_cliente.get(k)) for k in dimensiones}
    if any(v is None for v in medidas.values()):
        return None
    candidatos = []
    for variante in variantes:
        if (variante.get("stock") or 0) <= 0:
            continue
        prenda = {k: _validar_medida(variante.get(k)) for k in dimensiones}
        if any(v is None for v in prenda.values()):
            continue
        holguras = {k: round(prenda[k] - medidas[k], 2) for k in dimensiones}
        # Completar holguras no relevantes con NaN, igual que en entrenamiento.
        fila = {
            "categoria": categoria,
            "talla_comprada": str(variante["talla"]),
            "holgura_pecho_cm": holguras.get("pecho"),
            "holgura_cintura_cm": holguras.get("cintura"),
            "holgura_cadera_cm": holguras.get("cadera"),
        }
        probabilities = model.predict_proba(pd.DataFrame([fila]))[0]
        classes = list(model.classes_)
        score = float(probabilities[classes.index("BIEN")]) if "BIEN" in classes else 0.0
        # Penalizar resultados con clase predominante distinta de BIEN; mostrar
        # sugerencia solo si el ajuste favorable supera un umbral prudente.
        if score < 0.50:
            continue
        excess = sum(abs(v - 6.0) for v in holguras.values())
        candidatos.append((-score, excess, str(variante["talla"]), int(variante["id_variante"]), holguras))
    if not candidatos:
        return None
    candidatos.sort()
    negative_score, _, talla, variant_id, holguras = candidatos[0]
    return Resultado(talla, variant_id, dimensiones, holguras, round(-negative_score, 3),
                     "supervisado", "modelo_experimental")
