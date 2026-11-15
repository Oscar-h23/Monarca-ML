# Recomendación de tallas — Fase 1

Módulo integrado en el repositorio Monarca-ML, independiente del pipeline existente de recomendaciones de outfits.

## Estado

- Prototipo heurístico: **no es un modelo supervisado entrenado**.
- Dos métodos: `reglas` y `vecino_cercano` (búsqueda de vecino sobre las variantes disponibles).
- No se entrenan modelos con datos personales, fotografías ni identificadores de compradores.
- La regla usa **2 cm de holgura mínima** en las dimensiones relevantes y descarta variantes sin stock.
- Si faltan medidas del cuerpo o prenda, no inventa una talla.
- No se ha conectado aún esta API al backend Spring Boot ni a Supabase.

## Iniciar

Desde la raíz del repositorio, con Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Abrir la documentación interactiva en `http://localhost:8001/docs`.

## Probar

```bash
python -m unittest discover -s tests -v
```

## Ejemplo

```bash
curl -X POST http://localhost:8001/internal/v1/tallas/recomendar \
  -H 'Content-Type: application/json' \
  -d '{"categoria":"Tops","medidas":{"pecho":90,"cintura":72},"variantes":[{"id_variante":3,"talla":"S","stock":8,"pecho":92,"cintura":74},{"id_variante":4,"talla":"M","stock":8,"pecho":98,"cintura":80}],"metodo":"reglas"}'
```

## Limitaciones y despliegue

**No exponer** `/internal/v1/tallas/recomendar` públicamente: el prototipo carece de autenticación. En una integración posterior, Spring Boot deberá validar autorización, recuperar las medidas del perfil autenticado y consultar únicamente las variantes del producto solicitado. El modelo recibirá solo las medidas necesarias.

Se requiere recopilar etiquetas reales de ajuste con consentimiento y realizar evaluación separada antes de afirmar rendimiento de clasificación supervisada.

## Relación con el frontend

La ficha de producto de Monarca-front dispone de un baseline por reglas implementado en Angular. Este módulo FastAPI es experimental y no reemplaza automáticamente al baseline del frontend.
