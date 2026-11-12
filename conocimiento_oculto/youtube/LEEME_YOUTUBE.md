# Comentarios de YouTube (Etapa 6)

## Qué hay en esta carpeta
| Archivo | Contenido | ¿Se publica? |
|---|---|---|
| `videos.csv` | Videos consultados: id, título, canal, fecha, enlace, comentarios en el video y comentarios extraídos | Sí |
| `comentarios_limpios.csv` | Comentarios útiles (sin duplicados, vacíos ni ruido) que se cargan en Orange (columna `texto`) | Sí |
| `reporte_extraccion.json` | Fecha de extracción, consultas, filtros, conteos por motivo de descarte y cuota usada | Sí |
| `comentarios_crudos.csv` | Todo lo extraído antes de limpiar | **No** (`.gitignore`) |

No se guardan nombres, canales ni identificadores de los autores: `id_comentario` es un código (hash).

## Última extracción
- Fecha: 12-11-2026 (UTC). 25 videos encontrados, **3 usados** (los que cumplieron los filtros), 170 comentarios crudos, **117 útiles**.
- Descartes: 31 muy cortos, 21 solo emojis o símbolos, 1 duplicado. Cuota usada: 504 de 10.000 unidades.
- Criterios y filtros completos: `reporte_extraccion.json`.

El corpus es **pequeño** y no representa a la población: 22 % de los comentarios son uso escolar del video y hay comentarios de otros países. Para un análisis más sólido conviene ampliarlo (ver abajo) y volver a correr todo.

## Cómo repetir o ampliar la extracción
1. En [Google Cloud Console](https://console.cloud.google.com/) cree un proyecto, habilite **YouTube Data API v3** y cree una **clave de API**.
2. Defina la clave como variable de entorno (**nunca** en el código ni en el repositorio):
   - Linux/Mac: `export YOUTUBE_API_KEY="su_clave"`
   - Windows (PowerShell): `$env:YOUTUBE_API_KEY="su_clave"`
3. Desde la raíz del repositorio:
   ```bash
   python conocimiento_oculto/extraer_comentarios_youtube.py --videos-por-busqueda 10 --max-comentarios 500
   ```
   Para ampliar el corpus: más `--videos-por-busqueda`, más consultas en la lista `BUSQUEDAS` del script o menos `MIN_COMENTARIOS_VIDEO`. Cada búsqueda cuesta 100 unidades de la cuota diaria.
4. Revise `videos.csv` (que los videos traten la deforestación en Colombia) y, si cambia el corpus, regenere los resultados que lee la aplicación:
   ```bash
   python conocimiento_oculto/referencia.py
   ```
5. En Orange, vuelva a cargar `comentarios_limpios.csv` en el widget File y actualice las capturas.

## Restricciones y cuidados
- Solo se leen comentarios principales (sin respuestas); orden por relevancia (favorece lo más votado).
- Los videos con comentarios desactivados no se pueden leer.
- El idioma se detecta con una heurística de palabras funcionales; quedan comentarios fuera de tema.
- No publique la clave ni `comentarios_crudos.csv`.
