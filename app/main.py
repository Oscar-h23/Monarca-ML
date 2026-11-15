"""API interna de recomendación de tallas; acceso solo servidor a servidor."""
import hmac
import os
import base64
import io
import tempfile
from pathlib import Path
import joblib
from src.preparar_tallas import preparar
from src.entrenar_tallas import train
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from .recomendacion import recomendar
from .supervisado import recomendar_supervisado

app = FastAPI(title='Monarca ML - Tallas', version='0.2.0')

def verificar_token(x_ml_token: str | None = Header(default=None)) -> None:
    esperado = os.environ.get('ML_INTERNAL_TOKEN', '')
    if not esperado or len(esperado) < 24 or not x_ml_token or not hmac.compare_digest(esperado, x_ml_token):
        raise HTTPException(status_code=401, detail='No autorizado')

class Entrada(BaseModel):
    categoria: str
    medidas: dict[str, float | None]
    variantes: list[dict]
    metodo: str = Field(default='reglas', pattern='^(reglas|vecino_cercano|supervisado))

@app.get('/health')
def health():
    return {'status':'ok','modelo_entrenado':False}

@app.post('/internal/v1/tallas/recomendar', dependencies=[Depends(verificar_token)])
def talla(data: Entrada):
    if data.metodo == 'supervisado':
        if not data.modelo_base64:
            raise HTTPException(status_code=422, detail='Falta el modelo supervisado')
        try:
            r = recomendar_supervisado(data.categoria, data.medidas, data.variantes, data.modelo_base64)
        except (ValueError, TypeError, ImportError) as exc:
            raise HTTPException(status_code=422, detail='Modelo experimental inválido') from exc
    else:
        r = recomendar(data.categoria, data.medidas, data.variantes, data.metodo)
    if r is None:
        return {'recomendacion':None,'motivo':'Medidas insuficientes, incompatibles o sin stock'}
    advertencia = ('Predicción experimental; no validada con compradores reales' if data.metodo == 'supervisado' else 'Recomendación heurística, no modelo supervisado entrenado')
    return {'recomendacion':r.__dict__,'advertencia': advertencia}
)

@app.get('/health')
def health():
    return {'status':'ok','modelo_entrenado':False}

@app.post('/internal/v1/tallas/recomendar', dependencies=[Depends(verificar_token)])
def talla(data: Entrada):
    r = recomendar(data.categoria, data.medidas, data.variantes, data.metodo)
    if r is None:
        return {'recomendacion':None,'motivo':'Medidas insuficientes, incompatibles o sin stock'}
    return {'recomendacion':r.__dict__,'advertencia':'Recomendación heurística, no modelo supervisado entrenado'}

class EntrenarRequest(BaseModel):
    fuente: str = Field(pattern='^(REALES|PRUEBA)$')
    dataset_csv: str = Field(min_length=40, max_length=300_000)

@app.post('/internal/v1/tallas/entrenar', dependencies=[Depends(verificar_token)])
def entrenar_tallas(data: EntrenarRequest):
    # Solo accesible desde Spring Boot autenticado como ADMIN.
    with tempfile.TemporaryDirectory(prefix='monarca-tallas-') as tmp:
        root = Path(tmp)
        raw = root / 'tallas_raw.csv'
        prepared = root / 'tallas_preparadas.csv'
        raw.write_text(data.dataset_csv, encoding='utf-8')
        try:
            summary = preparar(raw, prepared)
            if summary['validas'] < 30:
                raise ValueError('Datos insuficientes para entrenamiento')
            metrics = train(prepared, root / 'models', data.fuente)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)[:180]) from exc
        artifact = (root / 'models' / metrics['model_file']).read_bytes()
        if len(artifact) > 1_500_000:
            raise HTTPException(status_code=422, detail='Artefacto demasiado grande')
        return {
            'fuente':data.fuente,
            'algoritmo':metrics['algorithm'],
            'metricas':metrics,
            'modelo_base64':base64.b64encode(artifact).decode('ascii'),
            'preparacion':summary
        }
