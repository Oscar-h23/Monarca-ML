"""Recomendaciones por asociación de productos comprados conjuntamente.

Minería de patrones frecuentes de cestas (no clasificador supervisado).
Métricas: soporte, confianza y lift. Los ejemplos sintéticos solo prueban
la usabilidad del recorrido, no representan ventas auténticas.
"""
from collections import Counter


def complementos(cestas: list[list[int]], id_producto: int, fuente: str, max_resultados: int = 4):
    if fuente not in ("PRUEBA", "REALES"):
        raise ValueError("Fuente no válida")
    if not 1 <= len(cestas) <= 5000:
        raise ValueError("Número de cestas inválido")
    if max_resultados < 1 or max_resultados > 10 or id_producto < 1:
        raise ValueError("Solicitud inválida")
    datos = []
    for cesta in cestas:
        if not isinstance(cesta, list) or len(cesta) > 30:
            raise ValueError("Cesta inválida")
        valores = set()
        for producto in cesta:
            if not isinstance(producto, int) or producto <= 0:
                raise ValueError("Identificador de producto inválido")
            valores.add(producto)
        if valores:
            datos.append(valores)

    n = len(datos)
    recuento = Counter(item for cesta in datos for item in cesta)
    anclas = recuento[id_producto]
    # Con muy pocas compras reales no publicamos asociaciones no fiables.
    if fuente == "REALES" and (n < 20 or anclas < 5):
        return {
            "modulo": "COCOMPRA", "fuente": fuente, "cestas": n,
            "producto": id_producto, "recomendaciones": [],
            "mensaje": "No hay compras auténticas suficientes para una asociación fiable."
        }
    coincidencias = Counter(
        item for cesta in datos if id_producto in cesta
        for item in cesta if item != id_producto
    )
    resultados = []
    for producto, juntos in coincidencias.items():
        if juntos < (3 if fuente == "REALES" else 2):
            continue
        confianza = juntos / anclas
        soporte = juntos / n
        lift = confianza / (recuento[producto] / n)
        resultados.append({
            "idProducto": producto, "cestasJuntas": juntos,
            "soporte": round(soporte, 4),
            "confianza": round(confianza, 4),
            "lift": round(lift, 4),
        })
    resultados.sort(key=lambda r: (-r["lift"], -r["confianza"], -r["cestasJuntas"], r["idProducto"]))
    return {
        "modulo": "COCOMPRA", "fuente": fuente, "cestas": n,
        "producto": id_producto, "recomendaciones": resultados[:max_resultados],
        "mensaje": (
            "Asociaciones simuladas para demostración académica."
            if fuente == "PRUEBA" else
            "Asociaciones de pedidos finalizados; no implican causalidad."
        ),
    }
