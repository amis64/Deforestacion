# -*- coding: utf-8 -*-
"""Genera docs/modelo_estrella/*.md a partir de documentacion.py y olap.py (python multidimensional/generar_docs.py)."""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from multidimensional import documentacion as d  # noqa: E402

SALIDA = os.path.join(RAIZ, "docs", "modelo_estrella")


def tabla(encabezados, filas):
    out = ["| " + " | ".join(encabezados) + " |", "|" + "|".join("---" for _ in encabezados) + "|"]
    for f in filas:
        out.append("| " + " | ".join(str(x).replace("|", "/") for x in f) + " |")
    return "\n".join(out)


def diccionario():
    t = ["# Diccionario de datos del modelo estrella", "",
         "**Hecho:** %s · **Granularidad:** %s" % (d.HECHOS["nombre"], d.HECHOS["granularidad"]), ""]
    for tb in d.TABLAS:
        t += ["## %s (%s)" % (tb["nombre"], tb["rol"]), "", "Clave primaria: `%s`. Jerarquía: %s." % (tb["pk"], tb["jerarquia"]), "",
              tabla(["Campo", "Tipo", "Clave", "Descripción", "Origen", "Transformación"], tb["campos"]), ""]
    t += ["## Relaciones", "", tabla(["Clave foránea", "Referencia", "Cardinalidad"], d.RELACIONES), "",
          "## Medidas de análisis", "",
          tabla(["Medida", "Unidad", "Fórmula", "Agregación", "Cuándo se suma"],
                [(m["nombre"], m["unidad"], "`%s`" % m["formula"], m["agregacion"], m["suma"]) for m in d.medidas()]), ""]
    return "\n".join(t)


def mapeo():
    t = ["# Correspondencia entre variables originales y campos del modelo", "",
         "Origen: `deforestacion_limpio.csv` (dataset tratado en las etapas anteriores).", ""]
    filas = []
    for tb in d.TABLAS:
        for campo, tipo, clave, desc, origen, trans in tb["campos"]:
            filas.append((origen, "%s.%s" % (tb["nombre"], campo), trans))
    t += [tabla(["Variable original", "Campo del modelo", "Transformación"], filas), "",
          "## Procedimiento de carga", ""] + ["%d. %s" % (i, p) for i, p in enumerate(d.ETL_PASOS, 1)] + [""]
    return "\n".join(t)


def jerarquias():
    t = ["# Dimensiones y jerarquías", "",
         tabla(["Dimensión", "Perspectiva", "Jerarquía", "Justificación"], d.DIMENSIONES), "",
         tabla(["Jerarquía", "Niveles", "Relación de agrupación"], d.JERARQUIAS), ""]
    return "\n".join(t)


def main():
    os.makedirs(SALIDA, exist_ok=True)
    for nombre, f in (("diccionario_datos.md", diccionario), ("mapeo_variables.md", mapeo), ("dimensiones_jerarquias.md", jerarquias)):
        with open(os.path.join(SALIDA, nombre), "w", encoding="utf-8") as fh:
            fh.write(f())
        print("escrito", os.path.join("docs", "modelo_estrella", nombre))


if __name__ == "__main__":
    main()
