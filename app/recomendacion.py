"""Motor inicial de recomendación de tallas.

No es un modelo supervisado: usa tablas de medidas del inventario, sin datos de usuarios
para entrenar. Algoritmos: regla de holgura y búsqueda de vecinos más cercanos.
"""
from dataclasses import dataclass
from math import isfinite
from typing import Any

DIMENSIONES = {'Tops': ('pecho', 'cintura'),
               'Bottoms': ('cintura', 'cadera'),
               'Vestidos': ('pecho', 'cintura', 'cadera')}
HOLGURA_MIN_CM = 2.0

@dataclass(frozen=True)
class Resultado:
    talla: str
    variante_id: int
    dimensiones: tuple[str, ...]
    holguras_cm: dict[str, float]
    distancia: float
    metodo: str
    nivel_evidencia: str


def _validar_medida(x: Any) -> float | None:
    if x is None or isinstance(x, bool):
        return None
    try:
        n = float(x)
    except (TypeError, ValueError):
        return None
    return n if isfinite(n) and 25 <= n <= 300 else None


def recomendar(categoria: str, medidas_cliente: dict[str, Any], variantes: list[dict[str, Any]], metodo: str = 'reglas') -> Resultado | None:
    """Retorna una sugerencia, no una garantía de ajuste.

    Se requieren TODAS las dimensiones relevantes de la categoría tanto en el
    cliente como en cada variante. No se usan fotos ni identificadores de usuario.
    El KNN experimental recupera el vecino más cercano de la tabla, sin entrenar.
    """
    if categoria not in DIMENSIONES:
        return None
    if metodo not in {'reglas', 'vecino_cercano'}:
        raise ValueError('Método no soportado')
    dimensiones = DIMENSIONES[categoria]
    cliente = {k: _validar_medida(medidas_cliente.get(k)) for k in dimensiones}
    if any(v is None for v in cliente.values()):
        return None
    candidatos = []
    for variante in variantes:
        if (variante.get('stock') or 0) <= 0:
            continue
        prenda = {k: _validar_medida(variante.get(k)) for k in dimensiones}
        if any(v is None for v in prenda.values()):
            continue
        diferencias = {k: round(prenda[k] - cliente[k], 2) for k in dimensiones}
        if any(x < HOLGURA_MIN_CM for x in diferencias.values()):
            continue
        # Reglas: elegir la holgura excedente mínima de forma conjunta.
        # Vecino cercano: distancia euclidiana a cliente + holgura mínima.
        error = sum((x-HOLGURA_MIN_CM)**2 for x in diferencias.values())
        if metodo == 'reglas':
            # Selección clásica basada en promedio de holguras.
            error = sum(diferencias.values()) / len(diferencias)
        candidatos.append((error, variante, diferencias))
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: (x[0], str(x[1]['talla']), int(x[1]['id_variante'])))
    score, variante, diferencias = candidatos[0]
    return Resultado(str(variante['talla']), int(variante['id_variante']), dimensiones,
                     diferencias, round(score, 3), metodo, 'tabla_medidas_no_validada')
