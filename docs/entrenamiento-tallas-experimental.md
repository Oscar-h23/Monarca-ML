# Entrenamiento supervisado de tallas (experimental)

El selector de fuentes de **Administración → Machine Learning** almacena `PRUEBA` o `REALES` por módulo. La exportación administrativa es `GET /api/admin/ml/tallas/dataset.csv`; requiere la sesión autorizada del administrador.

## Probar el entrenamiento desde terminal

1. En el panel, seleccionar **Datos de prueba** para TALLAS y descargar el CSV.
2. Guardarlo en `data/prueba/tallas_raw.csv`.
3. Ejecutar:

```bash
pip install -r requirements.txt
python -m src.preparar_tallas --entrada data/prueba/tallas_raw.csv --salida data/prueba/tallas_preparadas.csv
python -m src.entrenar_tallas --entrada data/prueba/tallas_preparadas.csv --fuente PRUEBA --salida artifacts/prueba
python -m unittest discover -s tests
```

Se generan `artifacts/prueba/tallas_prueba.joblib` y `artifacts/prueba/tallas_prueba_metricas.json`. El modelo **no se activa automáticamente** en el sitio público. En particular, no basta cambiar la fuente administrativa para que la recomendación del cliente use este modelo.

Para trabajar con datos reales, exportar nuevamente seleccionando **Datos reales** y utilizar `--fuente REALES --salida artifacts/reales`. Los scripts no mezclan ambos conjuntos. Si los datos reales aún son escasos o no contienen las tres clases, el entrenamiento se rechaza en lugar de publicar una métrica engañosa.

## Cómo interpretar las métricas

La selección entre KNN y árbol usa macro-F1 de validación (desempate por accuracy). Se informa accuracy, macro-F1 y matriz de confusión de una partición de prueba no usada para seleccionar el algoritmo. Partición prevista: 70 % entrenamiento, 15 % validación, 15 % prueba.

**Advertencia académica:** 100 filas sintéticas basadas en reglas sirven para comprobar la ejecución del pipeline y describir una prueba de concepto, no para demostrar que el sistema acierta con compradores reales. No se deben mezclar con valoraciones reales ni afirmar que el modelo está validado en producción.

## Flujo administrativo integrado

- **Administración → Machine Learning → TALLAS**: elige REALES o PRUEBA.
- **Entrenar modelo**: Spring Boot exporta la fuente seleccionada, envía el CSV autenticado a FastAPI, registra un artefacto en `monarca.ml_modelos_talla` y retorna métricas de entrenamiento, validación y prueba.
- **Versiones y métricas**: compara modelos KNN y árbol, visualiza macro-F1, accuracy y matriz de confusión. La versión nueva se guarda inactiva.
- **Activar versión experimental**: almacena cuál modelo está activo en Supabase. El recomendador de productos consulta el modelo guardado y presenta advertencia experimental, especialmente si usa datos sintéticos.
- **Volver a recomendaciones por reglas**: desactiva todos los artefactos, sin borrar los historiales.
- **OUTFITS/PATRONES**: la fuente se puede configurar, pero sus datasets y entrenamientos todavía necesitan integración propia.

Los endpoints de entrenamiento y activación requieren `ROLE_ADMIN` en Spring Boot. El servicio ML solo admite token interno de servicio. Los modelos se serializan en un campo privado accesible por JDBC, **no** directamente por el cliente.

Un cambio de fuente no cambia el modelo que ya está activo; el administrador debe entrenar y activar explícitamente otra versión. No se mezclan datos de prueba con valoraciones reales. La precisión del modelo de prueba no representa precisión con clientas reales.

## Verificación pendiente

El CI valida compilación y pruebas automatizadas. La publicación final en Cloudflare y la verificación funcional en navegador autenticado deben comprobarse por separado; no se debe asumir que un CI exitoso demuestra que todo el recorrido de usuario funciona. Para exponer, entrenar con PRUEBA, revisar resultados y activar experimentalmente; no afirmar validación comercial del modelo.
