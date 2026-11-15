# Módulos académicos de Nayeli's Moda (Monarca-ML)

## Alcance de esta versión

Se integraron tres demostraciones adicionales al clasificador de tallas existente:

| Módulo administrativo | Algoritmos | Fuente de prueba |
|---|---|---|
| Segmentación de clientes | K-Means y DBSCAN | 100 perfiles ficticios, sin datos personales |
| Predicción de demanda | Regresión lineal | 100 observaciones semanales simuladas |
| Búsqueda de outfits | A* (heurística cero) y Hill Climbing | 100 escenarios ficticios con prendas del catálogo |

**Datos sintéticos:** Los ejemplos se generan en la tabla privada `monarca.ml_demo_registros`; están aislados de pedidos, perfiles, valoraciones y estadísticas reales. Proceden de una simulación independiente del ZIP descargable anterior (comparten las columnas conceptuales, no necesariamente cada fila). Solo el backend administra su consulta; la tabla tiene RLS.

## Flujo administrativo

1. Entrar a **Administración → Machine Learning**.
2. En Segmentación, Demanda o Outfits seleccionar **Prueba**.
3. Deben mostrarse 100 ejemplos disponibles.
4. Pulsar «Ejecutar K-Means y DBSCAN», «Entrenar regresión lineal» o «Buscar outfits con Hill Climbing y A*», respectivamente.
5. El backend lee la fuente seleccionada, llama a FastAPI mediante `X-ML-Token` y guarda resultados en `monarca.ml_ejecuciones_academicas`.
6. El frontend presenta métricas y la última ejecución, incluso tras recargar. Ninguna ejecución modifica modelos de tallas o compras reales.

Los endpoints internos del servicio ML son:
`POST /internal/v1/modulos/CLUSTERING/ejecutar`,
`POST /internal/v1/modulos/DEMANDA/ejecutar` y
`POST /internal/v1/modulos/OUTFITS/ejecutar`. Requieren token interno.

Endpoints de backend (todos requieren rol `ADMIN`):
`POST /api/admin/ml/modulos/{modulo}/ejecutar`
y `GET /api/admin/ml/modulos/resultados`.

### Datos reales

- Outfits: puede usar el catálogo y los precios actuales con stock, pero no hay una puntuación estética real. Se aplica un valor neutral de estilo para evaluar principalmente la restricción de presupuesto.
- Clustering: se bloquea el modo real hasta contar con variables verificables de comportamiento y diversidad suficiente. No se crean visitas ficticias para clientes reales.
- Demanda: se bloquea el modo real hasta recopilar una serie histórica completa de variables necesarias, incluidas visitas, sin rellenar artificialmente datos faltantes.

### Interpretación académica

- Silhouette K-Means/DBSCAN: indicadores descriptivos de separación entre segmentos simulados, **no** validación de mercado.
- MAE de regresión: evalúa el ajuste a ventas sintéticas en un corte temporal, **no** demuestra predicción futura real. Los datos de visitas de la semana constituyen una variable conocida solo al terminarla.
- A*: busca combinaciones dentro del presupuesto; usa heurística admisible 0, equivalente a costo uniforme en un espacio de soluciones de dos prendas. Hill Climbing prueba movimientos locales con reinicios y puede encontrar un óptimo local. **No son clasificadores entrenados.**
- Cloud & DevOps: FastAPI en Railway, Spring Boot en Railway, Angular en la web, GitHub Actions y Supabase para persistencia.

## Limitaciones y verificación

Las pruebas de GitHub validan código y algoritmos; para completar verificación en producción debe ejecutarse el recorrido autenticado por el administrador y confirmarse publicación del frontend. Este flujo no publica nuevos modelos supervisados a compradores ni altera el modelo #1 de tallas.
