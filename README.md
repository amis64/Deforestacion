# Deforestación y Transformación del Territorio — Etapa 1

Aplicación Flask que documenta la Etapa 1 del proyecto de Minería de Datos:
problema, preguntas, necesidades de información, fuentes, dataset,
diccionario de datos, diagnóstico de calidad y limitaciones.

## Estructura del proyecto

```
.
├── app.py                     # Rutas de la aplicación
├── contenido.py                # Todo el texto/datos de la Etapa 1
├── requirements.txt
├── Procfile                    # Para Render (gunicorn)
├── render.yaml                 # Configuración de Render como código (opcional)
├── runtime.txt                 # Versión de Python sugerida
├── static/css/style.css
├── templates/
│   ├── base.html
│   ├── _sidebar.html
│   ├── index.html
│   └── problema.html, preguntas.html, necesidades.html, fuentes.html,
│       dataset.html, diccionario.html, calidad.html, limitaciones.html
└── anexo_construccion_dataset/
    ├── build_dataset.py        # Script que integra las fuentes (no es parte de la app)
    └── README.md
```

## Probarlo en local

**Importante:** este paquete NO incluye una carpeta `venv/` ya creada a
propósito. Un entorno virtual contiene binarios compilados específicos del
sistema operativo y la versión de Python donde se creó — copiar uno de una
máquina a otra casi nunca funciona, y además puede pesar cientos de MB
innecesariamente. Lo correcto es crear el tuyo en un solo paso:

### Windows (PowerShell)

```powershell
cd deforestacion_flask
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

### macOS / Linux

```bash
cd deforestacion_flask
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000` en el navegador. Para salir del entorno virtual
en cualquier momento: `deactivate`.

## Desplegar en Render

1. Sube esta carpeta a un repositorio de GitHub (el `.gitignore` ya excluye
   `venv/` y demás archivos que no deben subirse).
2. En Render: **New + → Web Service**, conecta el repositorio.
3. Render debería detectar automáticamente `render.yaml`. Si prefieres
   configurarlo a mano en vez de usar ese archivo:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3
4. Despliega. Render asigna el puerto automáticamente mediante la variable
   de entorno `PORT`, que `app.py` ya lee (por eso *no* se debe fijar un
   puerto distinto a mano).

## Sobre el anexo de construcción del dataset

`anexo_construccion_dataset/build_dataset.py` es el script que integra las
fuentes de datos reales (GFW, MapBiomas, FIRMS, FAO, OWID) para producir el
dataset consolidado descrito en la sección "Dataset" de la aplicación. No es
necesario para que la app Flask funcione ni para desplegarla — se incluye
solo por trazabilidad. Tiene sus propias dependencias (pandas, geopandas,
etc.), separadas de `requirements.txt` (ver su propio README).
