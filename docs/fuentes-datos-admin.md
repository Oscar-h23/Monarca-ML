# Fuentes de datos de Machine Learning (modo académico)

La aplicación Nayeli's Moda dispone de un selector por módulo en
**Administración > Machine Learning**. Los modos se almacenan en Supabase:
`monarca.ml_fuentes_datos` con `modulo` y `fuente` (`REALES` o `PRUEBA`).

## Módulos

| Módulo | Modo real | Modo prueba |
| --- | --- | --- |
| TALLAS | Valoraciones consentidas en `monarca.valoraciones_talla` (el script excluye faltantes) | 100 registros claramente sintéticos en `monarca.ml_tallas_prueba` |
| OUTFITS | Fuente por conectar | Fuente por conectar |
| PATRONES | Fuente por conectar | Fuente por conectar |

El selector es **persistente**, independiente por módulo y solo editable por administradores.
No altera pedidos, valoraciones reales, stock ni perfil de compradores.

## Exportación de entrenamiento para tallas

Desde el panel de administración, elegir la fuente de TALLAS y pulsar
**Descargar CSV de la fuente seleccionada**.

El endpoint protegido del backend es
`GET /api/admin/ml/tallas/dataset.csv` y usa siempre la fuente guardada.
El CSV resultante incluye exactamente las columnas de entrada requeridas por
`src.preparar_tallas`. El resultado NO contiene correos ni IDs de usuarios.

Guardar el archivo descargado como `data/reales/tallas_raw.csv`, aunque sea
sintético (la carpeta está excluida de Git), y ejecutar:

```bash
python -m src.preparar_tallas \
  --entrada data/reales/tallas_raw.csv \
  --salida data/reales/tallas_entrenamiento.csv
```

**Importante:** seleccionar PRUEBA no entrena ni despliega un modelo automáticamente,
ni cambia las recomendaciones públicas de talla del sistema, que por ahora siguen
utilizando el recomendador inicial de reglas/vecino cercano. Antes de integrar otros
algoritmos, su pipeline deberá leer la configuración de `ml_fuentes_datos` y utilizar
un almacenamiento segregado equivalente al de tallas.

No unir datos sintéticos y reales para reportar precisión de clientes. Las etiquetas
sintéticas fueron generadas con una regla artificial de holgura, por lo que medir
buenos resultados sobre ellas solo demuestra que el entrenamiento reproduce la
simulación y no prueba precisión real.
