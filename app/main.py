"""API prototipo; no exponer públicamente sin autenticación y proxy backend."""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from .recomendacion import recomendar

app = FastAPI(title='Nayelis-ML — prototipo de tallas', version='0.1.0')

class Entrada(BaseModel):
    categoria: str
    medidas: dict[str, float | None]
    variantes: list[dict]
    metodo: str = Field(default='reglas', pattern='^(reglas|vecino_cercano)$')

@app.get('/health')
def health():
    return {'status': 'ok', 'modelo_entrenado': False}

@app.post('/internal/v1/tallas/recomendar')
def talla(data: Entrada):
    r = recomendar(data.categoria, data.medidas, data.variantes, data.metodo)
    if r is None:
        return {'recomendacion': None, 'motivo': 'Medidas insuficientes, incompatibles o sin stock'}
    return {'recomendacion': r.__dict__, 'advertencia': 'Sugerencia heurística; no hay ML supervisado entrenado'}
