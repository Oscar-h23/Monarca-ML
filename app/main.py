"""API privada de recomendación y entrenamiento supervisado de tallas."""
import base64
import hmac
import os
import tempfile
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from src.preparar_tallas import preparar
from src.entrenar_tallas import train
from .recomendacion import recomendar
from .supervisado import recomendar_supervisado

app = FastAPI(title="Monarca ML - Tallas", version="0.3.0")


def verificar_token(x_ml_token: str | None = Header(default=None)) -> None:
    esperado = os.environ.get("ML_INTERNAL_TOKEN", "")
    if not esperado or len(esperado) < 24 or not x_ml_token or not hmac.compare_digest(esperado, x_ml_token):
        raise HTTPException(status_code=401, detail="No autorizado")


class Entrada(BaseModel):
    categoria: str
    medidas: dict[str, float | None]
    variantes: list[dict]
    metodo: str = Field(default="reglas", pattern=r"^(reglas|vecino_cercano|supervisado)$")
    modelo_base64: str | None = None


class EntrenarRequest(BaseModel):
    fuente: str = Field(pattern=r"^(REALES|PRUEBA)$")
    dataset_csv: str = Field(min_length=40, max_length=300_000)


@app.get("/health")
def health():
    return {"status": "ok", "modelo_supervisado": "administrado_por_backend"}


@app.post("/internal/v1/tallas/recomendar", dependencies=[Depends(verificar_token)])
def talla(data: Entrada):
    if data.metodo == "supervisado":
        if not data.modelo_base64:
            raise HTTPException(status_code=422, detail="Falta el artefacto supervisado")
        try:
            r = recomendar_supervisado(data.categoria, data.medidas, data.variantes, data.modelo_base64)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Modelo experimental inválido") from exc
    else:
        r = recomendar(data.categoria, data.medidas, data.variantes, data.metodo)
    if r is None:
        return {"recomendacion": None, "motivo": "No hay talla apropiada con evidencia suficiente"}
    return {
        "recomendacion": r.__dict__,
        "advertencia": ("Predicción experimental; sin validación con compradores reales"
                        if data.metodo == "supervisado"
                        else "Recomendación heurística, no supervisada"),
    }


@app.post("/internal/v1/tallas/entrenar", dependencies=[Depends(verificar_token)])
def entrenar_tallas(data: EntrenarRequest):
    # La autenticación de administrador ocurre en Spring Boot.
    with tempfile.TemporaryDirectory(prefix="monarca-tallas-") as temp:
        root = Path(temp)
        raw = root / "tallas_raw.csv"
        prepared = root / "tallas_preparadas.csv"
        raw.write_text(data.dataset_csv, encoding="utf-8")
        try:
            summary = preparar(raw, prepared)
            if summary["validas"] < 30:
                raise ValueError("Datos insuficientes para entrenamiento")
            metrics = train(prepared, root / "models", data.fuente)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)[:180]) from exc
        artifact = (root / "models" / metrics["model_file"]).read_bytes()
        if len(artifact) > 1_500_000:
            raise HTTPException(status_code=422, detail="Modelo demasiado grande")
        return {
            "fuente": data.fuente,
            "algoritmo": metrics["algorithm"],
            "metricas": metrics,
            "modelo_base64": base64.b64encode(artifact).decode("ascii"),
            "preparacion": summary,
        }

# Módulos académicos nuevos: no alteran la recomendación pública de tallas.
from .modulos_academicos import ejecutar as ejecutar_modulo

class EjecucionAcademica(BaseModel):
    fuente: str = Field(pattern=r"^(REALES|PRUEBA)$")
    registros: list[dict] = Field(min_length=1, max_length=5000)
    presupuesto_soles: float | None = None

@app.post("/internal/v1/modulos/{modulo}/ejecutar", dependencies=[Depends(verificar_token)])
def ejecutar_academico(modulo: str, data: EjecucionAcademica):
    try:
        return ejecutar_modulo(modulo.upper(), data.registros, data.fuente, data.presupuesto_soles)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)[:200]) from exc

from .cocompra import complementos as calcular_complementos

class ConsultaCocompra(BaseModel):
    fuente: str = Field(pattern=r"^(REALES|PRUEBA)$")
    producto: int = Field(ge=1)
    cestas: list[list[int]] = Field(min_length=1, max_length=5000)

@app.post("/internal/v1/cocompra/recomendar", dependencies=[Depends(verificar_token)])
def recomendar_complemento(data: ConsultaCocompra):
    try:
        return calcular_complementos(data.cestas,data.producto,data.fuente)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422,detail=str(exc)[:180]) from exc
