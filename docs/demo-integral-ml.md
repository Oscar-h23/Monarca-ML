# Demostración integral de Machine Learning en Nayeli's Moda

## Acceso

Entra con una cuenta administradora a **Administración → Machine Learning → Abrir laboratorio interactivo para la presentación** o visita `/demo-ml`. La ruta requiere permiso de administrador.

## 5 recorridos para mostrar a la docente

1. **Clasificación de tallas:** selecciona un producto desde el laboratorio, abre su ficha y observa el comparador de medidas. La pantalla distingue entre recomendaciones por reglas y modelos supervisados experimentales. La versión entrenada se activa solo de forma explícita desde administración.
2. **Compras complementarias:** selecciona una blusa y consulta artículos que aparecen juntos en cestas de compra simuladas. El algoritmo usa reglas de asociación con soporte, confianza y lift. Puedes navegar a la ficha de la prenda complementaria, elegir variante y agregarla a la bolsa. Los datos demo se guardan como 100 cestas ficticias en `monarca.ml_cocompra_cestas_demo`, sin alterar pedidos.
3. **Clustering:** ejecuta K-Means/DBSCAN con la fuente PRUEBA y presenta cantidad de perfiles por grupo, gasto promedio, frecuencia y Silhouette.
4. **Demanda:** ejecuta regresión lineal con 100 semanas-producto simulados y compara MAE, MAE baseline y R². Explica que es una prueba retrospectiva sintética, no una predicción real de ventas futuras.
5. **Outfits:** introduce un presupuesto, ejecuta A* y Hill Climbing, muestra combinaciones, abre las prendas y utiliza **Agregar outfit a la bolsa**, validando IDs de variante, precio actual y stock real. El escenario de asociación y estilo es sintético.

## Controles de origen

En `monarca.ml_fuentes_datos` se guarda `REALES` o `PRUEBA` de modo independiente para `TALLAS`, `CLUSTERING`, `DEMANDA`, `OUTFITS` y `COCOMPRA`.

El recomendador de compras conjuntas accede a `GET /api/productos/{id}/complementos` a través de Spring Boot. No envía identificadores de compradores ni pedidos a FastAPI, únicamente conjuntos de IDs de producto. FastAPI recibe el token interno y devuelve las reglas; Spring Boot solo publica productos **activos y con stock**.

En modo REALES, la asociación usa exclusivamente pedidos `FINALIZADO`, y no muestra asociaciones cuando hay menos de 20 cestas o menos de 5 cestas con el producto de referencia. En modo PRUEBA consulta las 100 cestas ficticias, identificadas como **DEMOSTRACIÓN** en la ficha de productos.

## Cómo interpretar correctamente la recomendación

- **Soporte:** proporción de todas las cestas que contienen tanto A como B.
- **Confianza:** proporción de cestas que contienen A y también contienen B.
- **Lift:** confianza dividida entre la frecuencia global de B; un lift superior a 1 indica una asociación positiva dentro del conjunto analizado.
- Estos valores no demuestran que dos prendas sean visualmente compatibles, ni que el cliente tenga intención real de comprarlas.

### Limitaciones académicas y comerciales

- El origen sintético está visible; ninguna cifra es evidencia de comportamiento real.
- Los 100 registros demo de asociación son distintos de los CSV sintéticos para clustering, demanda y búsqueda heurística.
- La segmentación y la regresión con fuente REALES siguen bloqueadas hasta disponer de datos verificables suficientes.
- El outfit usa variantes y stock del catálogo real en la bolsa, pero puede estar construido a partir de puntuaciones de estilo ficticias.
- Los controles de entrenamiento y activación del modelo de talla siguen siendo independientes de estos cinco recorridos.

## Verificación operativa

Confirmar en GitHub el éxito de los tres CI, en Railway despliegue SUCCESS y en la web publicada la ruta `/demo-ml`. Después ejecutar la navegación administrador → laboratorio → ficha de producto → sugerencia complementaria → bolsa. No afirmar finalizado el recorrido en la web si no se ha probado desde una sesión real.
