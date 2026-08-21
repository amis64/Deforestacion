from flask import Flask, render_template

app = Flask(__name__)

# Nombre del proyecto
TITULO_PROYECTO = "Deforestación y Transformación del Territorio en Colombia"

# Integrantes del grupo
INTEGRANTES = [
    "Amy Tatiana Gelves Espinosa",
    "Danna Valentina Gonzalez Aldana",
    "Nicolas Suarez Rativa"
]

# Introducción corta (placeholder, se puede editar más adelante)
INTRODUCCION = (
    "Este proyecto de minería de datos busca analizar los patrones de "
    "deforestación y la transformación del territorio en Colombia, "
    "con el fin de identificar tendencias, causas y posibles zonas de riesgo "
    "a partir del análisis de datos geoespaciales y ambientales."
)


@app.route("/")
def index():
    return render_template(
        "index.html",
        titulo=TITULO_PROYECTO,
        introduccion=INTRODUCCION,
        integrantes=INTEGRANTES
    )


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
