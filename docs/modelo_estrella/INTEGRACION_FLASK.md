# Integración de la sección «Análisis multidimensional» en la aplicación Flask

La sección es un Blueprint independiente (`multidimensional/`). No modifica las rutas de las etapas anteriores.
Sobre el repositorio de la Etapa 4, solo se necesitan estos cambios en los archivos existentes:

## 1. `app.py`

```python
import contenido as c
from multidimensional import bp as multidimensional_bp      # Etapa 5 · Análisis multidimensional

app = Flask(__name__)
app.register_blueprint(multidimensional_bp)                  # Etapa 5
```

## 2. `templates/base.html`

En el `<head>`, después de la hoja de estilos principal, para que las plantillas de la sección puedan agregar su CSS:

```html
{% block head %}{% endblock %}
```

En la lista del menú principal (después de «Etapa 4», que enlaza los tableros de Power BI):

```html
<li{% if activo == 'multidimensional' %} class="activo"{% endif %}><a href="{{ url_for('multidim.indice') }}">Análisis multidimensional</a></li>
```

## 3. Archivos nuevos

`multidimensional/`, `templates/multidimensional/`, `static/css/multidimensional.css`, `static/img/etapa5/`,
`sql/05_…07_` y `docs/modelo_estrella/`. El dataset `deforestacion_limpio.csv` y la carpeta `powerbi/` ya están en el repositorio desde la Etapa 4: el ETL lee ese mismo CSV, y la página de resumen enlaza la sección «Etapa 4».

No hay dependencias nuevas: el ETL y las consultas usan `csv` y `sqlite3` de la biblioteca estándar de Python.
En Render no hace falta ningún paso de compilación adicional: `modelo_estrella.db` está versionado y, si faltara,
la aplicación lo reconstruye al arrancar.
