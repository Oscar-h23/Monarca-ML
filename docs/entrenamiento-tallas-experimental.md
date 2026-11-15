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

## Pendiente de integración

- Backend Spring Boot: endpoint ADMIN para solicitar entrenamiento sobre la fuente guardada; autenticación entre servicios y registro auditable de ejecuciones.
- Servicio FastAPI: entrenamiento controlado y persistencia de artefactos versionados en almacenamiento duradero, no en disco efímero de Railway.
- Frontend Angular: botón **Entrenar modelo**, estado de ejecución, visualización de métricas y botón **Activar modelo**.
- Inferencia: cargar exclusivamente el modelo aprobado y conservar el recomendador actual como respaldo; separar modo académico de la experiencia de clientes.
- Pruebas integradas y despliegue verificado. **Estas piezas no están implementadas por este commit.**
