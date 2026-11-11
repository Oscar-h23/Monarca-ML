# Integración con Monarka

El pipeline procesa un CSV exportado del catálogo y produce `resultados/outfits.json`.
La implementación de este repositorio termina en ese contrato. Los cambios en Java y Angular
se describen aquí para implementarlos en sus respectivos repositorios.

## Exportar catálogo real

Ejecuta esta consulta desde un canal administrativo de tu base de datos y exporta el resultado
como CSV. La consulta solo lee productos y variantes. No requiere datos de clientes.

```sql
SELECT p.id_producto, p.nombre, c.nombre AS categoria, v.color,
       MIN(v.precio) AS precio
FROM monarca.productos p
JOIN monarca.categorias c ON c.id_categoria = p.id_categoria
JOIN monarca.variantes_producto v ON v.id_producto = p.id_producto
WHERE p.activo AND c.activo AND v.activo
GROUP BY p.id_producto, p.nombre, c.nombre, v.color
ORDER BY p.id_producto, v.color;
```

Añade una columna `estilo` con una anotación consistente del equipo, por ejemplo casual,
formal o deportivo. Las tallas de un producto y color se agrupan en una fila.
El precio mínimo es una característica representativa; el precio que verá el cliente
se obtiene siempre del backend al seleccionar una variante.

Guarda el archivo como `data/reales/catalogo.csv` y las etiquetas como
`data/reales/valoraciones.csv`. Esa carpeta está excluida de Git.
Los pares deben cubrir categorías distintas, ambas clases y los productos reservados.
Usa el mismo texto de color en ambos CSV. Las puntuaciones deben provenir de evaluadores.
Cada fila de valoraciones necesita estas columnas.

```csv
id_producto_a,color_a,id_producto_b,color_b,valoracion
42,negro,17,azul,5
```

Se admiten varias valoraciones de un par y pares invertidos. Se promedian antes de dividir.
Se considera recomendable un promedio de al menos 4 sobre 5.

## Contrato de outfits

`versionContrato=1`. Todos los IDs son strings para conservar enteros grandes sin pérdida en JS.
Cada elemento de `recomendaciones` identifica un producto y color de origen y contiene
`outfits`, una lista ordenada de conjuntos de tres piezas. Cada conjunto contiene
`prendas` con `idProducto` y `color`, incluida la prenda de origen, y `puntuacion`
entre 1 y 5. La puntuación es un promedio de predicciones, no una probabilidad.
El archivo identifica si es demo, fecha UTC, modelo, límites DFS y hash del catálogo.
Una lista vacía es una respuesta válida. No se inventan combinaciones de respaldo.

La generación examina los 20 mejores vecinos de cada origen y conserva hasta 10 conjuntos.
Estos límites mantienen la demo manejable, pero pueden descartar conjuntos fuera del corte.
La construcción de pares es cuadrática; usar catálogos pequeños para esta versión educativa.

## Spring Boot

Endpoint propuesto `GET /api/productos/{id}/outfits?color=negro`.

1. Cargar el JSON validando su versión y esquema. Publicar cada archivo con un reemplazo atómico.
2. Buscar la entrada por ID y color exactos. Devolver una lista vacía si falta la entrada.
3. Para cada conjunto comprobar que todos los productos estén activos y que existan variantes
   activas con el color sugerido y stock mayor que cero. Comprobar también la categoría activa.
4. Si el cliente elige talla, validar esa talla en la variante correspondiente.
5. Hidratar nombres, fotos, precios y stock desde el catálogo actual. Filtrar conjuntos incompletos.
6. Respetar autenticación y validación de stock actuales al agregar al carrito y registrar el pedido.

Regenerar al cambiar colores, categorías, estilos o precios y después de añadir valoraciones.
El stock se valida en cada consulta. Al cambiar atributos de un producto, invalidar sus outfits
hasta regenerar o desplegar la nueva versión junto al catálogo actualizado.

## Angular

Añadir el método HTTP al servicio API existente. En la ficha, consultar cuando cambie el producto
o color seleccionado y descartar respuestas de una selección anterior, por ejemplo con switchMap.
Mostrar hasta tres outfits válidos con sus fotos y enlaces. Cada prenda permite seleccionar talla
antes de agregarla al carrito. Si no hay resultados, mostrar un estado vacío discreto.
