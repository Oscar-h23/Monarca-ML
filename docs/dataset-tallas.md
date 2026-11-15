# Dataset real de ajuste de tallas

Este módulo prepara datos para el **futuro entrenamiento supervisado**. No entrena ni despliega modelos automáticamente.

## Captura

Después de recibir un pedido con estado `FINALIZADO`, `ENTREGADO` o `COMPLETADO`, el propietario autenticado puede valorar **una vez** cada línea de prenda como `PEQUENA`, `BIEN` o `GRANDE`, aceptando expresamente su uso para ML.

Se guardan medidas actuales del cliente y medidas de la variante **en el momento de la valoración** (`origen_medidas=AL_VALORAR`), no las medidas históricas de la fecha de compra. El API ahora exige que las medidas corporales necesarias para la categoría estén completas antes de aceptar valoraciones nuevas. Si el cliente o la prenda cambian sus medidas entre la compra y la valoración, la observación podría no reflejar las dimensiones originales.

Las filas sin medidas completas para la categoría son válidas como opiniones históricas, pero el exportador **las excluye** del dataset de entrenamiento. Los registros históricos completados a partir de medidas posteriores, con confirmación del usuario de que no cambiaron, se identifican como `CONFIRMADA_POSTERIOR`; esta procedencia debe conservarse en los metadatos de análisis.

## Extraer datos con SQL Editor de Supabase

Ejecutar esta consulta como administrador. Exportar el resultado a un CSV privado en `data/reales/tallas_raw.csv`. No compartir públicamente los datos, aunque no tengan nombres.

```sql
SELECT
  categoria, talla_comprada, ajuste,
  busto_cm, cintura_cm, cadera_cm,
  prenda_pecho_cm, prenda_cintura_cm, prenda_cadera_cm
FROM monarca.valoraciones_talla
WHERE consentimiento_ml = TRUE
  AND origen_medidas IN ('AL_VALORAR', 'CONFIRMADA_POSTERIOR')
ORDER BY fecha_valoracion;
```

La consulta deliberadamente omite identificadores de clientes, pedidos y correos. **No subir los CSV al repositorio**.

## Preparar dataset

```bash
python -m src.preparar_tallas --entrada data/reales/tallas_raw.csv --salida data/reales/tallas_entrenamiento.csv
```

El resultado incluye categoría, talla y diferencias (holguras) por dimensión, con etiqueta de ajuste. El script informa cuántas filas se descartaron por ausencia de medidas o valores inválidos; no inventa ejemplos.

## Evaluación futura

Cuando haya ejemplos auténticos suficientes, comparar reglas con KNN y árboles de decisión usando particiones sin fuga entre clientes, fecha o producto. La exportación actual **no incluye un grupo pseudónimo para separar por usuario**; antes de reportar métricas rigurosas se debe habilitar una exportación restringida de grupos mediante un identificador seudónimo generado en backend o mantener las particiones dentro del backend. No dar por probada una accuracy usando una partición aleatoria de filas que pueda mezclar compras del mismo cliente.

Verificar consentimiento, balance de etiquetas, diversidad de artículos y cambios de medidas antes de entrenar.
