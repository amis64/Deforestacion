# -*- coding: utf-8 -*-
"""
Verificación en Python de los tres análisis de la Etapa 6 con los mismos datos que se cargan en Orange.

Uso (desde la raíz del proyecto):
    python conocimiento_oculto/preparar_datos_orange.py deforestacion_limpio.csv   # genera conocimiento_oculto/datos/
    python conocimiento_oculto/referencia.py                                       # genera conocimiento_oculto/resultados/*.json

Las cifras de Orange pueden diferir levemente (su propio árbol, su imputación y su LDA); lo que se publica en el
informe son las de Orange, y estos JSON sirven para comprobarlas y para alimentar las páginas de Flask.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analizar_comentarios  # noqa: E402
import clustering  # noqa: E402
import supervisado  # noqa: E402

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")


def limpio(o):
    if isinstance(o, dict):
        return {str(k): limpio(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [limpio(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return round(float(o), 4)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


def guardar(nombre, obj):
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, nombre), "w", encoding="utf-8") as f:
        json.dump(limpio(obj), f, ensure_ascii=False, indent=1)


def main():
    s = supervisado.calcular()
    guardar("supervisado.json", s)
    c = clustering.calcular(pred_te=s["_te_predicciones"])
    guardar("clustering.json", c)
    guardar("comentarios.json", analizar_comentarios.calcular())
    print("Listo: resultados/supervisado.json, clustering.json y comentarios.json")


if __name__ == "__main__":
    main()
