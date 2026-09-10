# -*- coding: utf-8 -*-
"""
app.py
======
Aplicación Flask que sirve como bitácora técnica del proyecto de Minería de
Datos "Deforestación y Transformación del Territorio". Etapa 1: del problema
a los datos. Etapa 2: calidad de datos (perfilamiento, dimensiones, plan de
tratamiento).

Cada ruta corresponde a un elemento del submenú de su etapa. El contenido
vive en contenido.py; aquí solo se arma la navegación y se renderizan las
plantillas.
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
    return {"submenu": SUBMENU, "submenu2": c.SUBMENU2, "proyecto": c.PROYECTO}


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


# ---------------------------------------------------------------------------
# Etapa 2 · Calidad de datos
# ---------------------------------------------------------------------------

@app.route("/etapa-2/descripcion")
def descripcion2():
    return render_template("etapa2/descripcion.html", activo="descripcion2", descripcion=c.DESCRIPCION2)


@app.route("/etapa-2/requisitos")
def requisitos2():
    return render_template("etapa2/requisitos.html", activo="requisitos2", requisitos=c.REQUISITOS2)


@app.route("/etapa-2/perfilamiento")
def perfilamiento2():
    return render_template("etapa2/perfilamiento.html", activo="perfilamiento2", perfilamiento=c.PERFILAMIENTO2)


@app.route("/etapa-2/dimensiones")
def dimensiones2():
    return render_template(
        "etapa2/dimensiones.html",
        activo="dimensiones2",
        dimensiones=c.DIMENSIONES2,
        script_metricas=c.SCRIPT_METRICAS2,
    )


@app.route("/etapa-2/problemas")
def problemas2():
    return render_template(
        "etapa2/problemas.html",
        activo="problemas2",
        inventario=c.INVENTARIO_PROBLEMAS2,
        causas=c.CAUSAS2,
        integracion=c.INTEGRACION2,
    )


@app.route("/etapa-2/tratamiento")
def tratamiento2():
    return render_template(
        "etapa2/tratamiento.html",
        activo="tratamiento2",
        plan=c.PLAN_TRATAMIENTO2,
        comparacion=c.COMPARACION_ANTES_DESPUES2,
        script_tratamiento=c.SCRIPT_TRATAMIENTO2,
    )


if __name__ == "__main__":
    # Puerto configurable por variable de entorno para funcionar igual en
    # local y en Render (que inyecta su propio PORT).
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
