# Anexo técnico: construcción del dataset

Este script (`build_dataset.py`) no forma parte de la aplicación Flask ni es
necesario para desplegarla — se incluye únicamente como evidencia de
trazabilidad y reproducibilidad, y para que el proceso de consolidación
descrito en la sección "Dataset" de la aplicación pueda ejecutarse de nuevo.

## Requisitos (independientes de los de la app Flask)

```
pip install pandas numpy openpyxl geopandas shapely
```

## Uso

1. Ajusta las rutas en el bloque `CONFIG` al inicio del archivo para que
   apunten a tus archivos fuente reales (GFW, MapBiomas, FIRMS, FAO, OWID,
   y opcionalmente un shapefile de límites municipales de Colombia).
2. Ejecuta:

   ```
   python build_dataset.py
   ```

3. El resultado (`dataset_consolidado.csv`) y el reporte de validación en
   consola son la base de las cifras documentadas en la sección "Dataset" y
   "Calidad inicial de los datos" de la aplicación.

Los archivos fuente originales (varios GB entre todos) no se incluyen en
este paquete por su tamaño; deben descargarse directamente de las fuentes
documentadas en la sección "Fuentes de datos" de la aplicación.
