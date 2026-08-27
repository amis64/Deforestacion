# -*- coding: utf-8 -*-
"""
app.py
======
Aplicación Flask que sirve como bitácora técnica del proyecto de Minería de
Datos "Deforestación y Transformación del Territorio". Etapa 1: del problema
a los datos.

Cada ruta corresponde a un elemento del submenú "Etapa 1" pedido en la guía
de la actividad. El contenido vive en contenido.py; aquí solo se arma la
navegación y se renderizan las plantillas.
"""

import os
from flask import Flask, render_template

import contenido as c

app = Flask(__name__)

# Estructura del submenú, reutilizada en la plantilla base para construir
# la barra de navegación y resaltar la sección activa.
SUBMENU = [
    ("problema", "1. Problema y contexto"),
    ("preguntas", "2. Pregunta principal y secundarias"),
    ("necesidades", "3. Necesidades de información"),
    ("fuentes", "4. Fuentes de datos"),
    ("dataset", "5. Dataset"),
    ("diccionario", "6. Diccionario de datos"),
    ("calidad", "7. Calidad inicial de los datos"),
    ("limitaciones", "8. Limitaciones y consideraciones"),
]


@app.context_processor
def inject_globals():
    """Disponible en todas las plantillas sin tener que pasarlo en cada return."""
    return {"submenu": SUBMENU, "proyecto": c.PROYECTO}


@app.route("/")
def inicio():
    return render_template("index.html", activo=None)


@app.route("/etapa-1/problema")
def problema():
    return render_template("problema.html", activo="problema", problema=c.PROBLEMA)


@app.route("/etapa-1/preguntas")
def preguntas():
    return render_template(
        "preguntas.html",
        activo="preguntas",
        pregunta_principal=c.PREGUNTA_PRINCIPAL,
        preguntas_secundarias=c.PREGUNTAS_SECUNDARIAS,
    )


@app.route("/etapa-1/necesidades")
def necesidades():
    return render_template("necesidades.html", activo="necesidades", necesidades=c.NECESIDADES)


@app.route("/etapa-1/fuentes")
def fuentes():
    return render_template(
        "fuentes.html",
        activo="fuentes",
        fuentes=c.FUENTES,
        fuentes_pendientes=c.FUENTES_DOCUMENTADAS_PENDIENTES,
    )


@app.route("/etapa-1/dataset")
def dataset():
    return render_template("dataset.html", activo="dataset", dataset=c.DATASET)


@app.route("/etapa-1/diccionario")
def diccionario():
    return render_template("diccionario.html", activo="diccionario", diccionario=c.DICCIONARIO)


@app.route("/etapa-1/calidad")
def calidad():
    return render_template("calidad.html", activo="calidad", calidad=c.CALIDAD)


@app.route("/etapa-1/limitaciones")
def limitaciones():
    return render_template("limitaciones.html", activo="limitaciones", limitaciones=c.LIMITACIONES)


if __name__ == "__main__":
    # Puerto configurable por variable de entorno para funcionar igual en
    # local y en Render (que inyecta su propio PORT).
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
