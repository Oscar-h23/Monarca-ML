"""API interna de recomendación de tallas; acceso solo servidor a servidor."""
import hmac
import os
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .recomendacion import recomendar

app = FastAPI(title='Monarca ML - Tallas', version='0.2.0')

def verificar_token(x_ml_token: str | None = Header(default=None)) -> None:
    esperado = os.environ.get('ML_INTERNAL_TOKEN', '')
    if not esperado or len(esperado) < 24 or not x_ml_token or not hmac.compare_digest(esperado, x_ml_token):
        raise HTTPException(status_code=401, detail='No autorizado')

class Entrada(BaseModel):
    categoria: str
    medidas: dict[str, float | None]
    variantes: list[dict]
    metodo: str = Field(default='reglas', pattern='^(reglas|vecino_cercano)$')

@app.get('/health')
def health():
    return {'status':'ok','modelo_entrenado':False}

@app.post('/internal/v1/tallas/recomendar', dependencies=[Depends(verificar_token)])
def talla(data: Entrada):
    r = recomendar(data.categoria, data.medidas, data.variantes, data.metodo)
    if r is None:
        return {'recomendacion':None,'motivo':'Medidas insuficientes, incompatibles o sin stock'}
    return {'recomendacion':r.__dict__,'advertencia':'Recomendación heurística, no modelo supervisado entrenado'}
