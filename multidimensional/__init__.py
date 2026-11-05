# -*- coding: utf-8 -*-
"""
Blueprint «Análisis multidimensional» (Etapa 5).

Se registra en app.py con:

    from multidimensional import bp as multidimensional_bp
    app.register_blueprint(multidimensional_bp)

Rutas (todas bajo /analisis-multidimensional):
    /                    propósito, relación con la Etapa 4, datos y acceso a las vistas
    /modelo              diagrama, dimensiones, medidas, jerarquías, ETL y validaciones
    /operaciones         una consulta ejecutada por cada operación (drill-down, roll-up, slice, dice, pivot)
    /conocimientos       los 8 conocimientos, limitaciones y conclusiones
    /vista/<id>          las cuatro vistas interactivas
"""

import json
import os
from functools import lru_cache

from flask import Blueprint, abort, render_template, request

try:
    import contenido as _contenido
except ImportError:  # pragma: no cover
    _contenido = None

from . import cifras, conocimientos, documentacion, olap, operaciones
from .vistas import POR_ID, VISTAS
from .vistas import comun

AQUI = os.path.dirname(os.path.abspath(__file__))


def _asegurar_modelo():
    """Si la base del modelo no existe (p. ej. no se versionó), la reconstruye desde el dataset tratado."""
    if os.path.exists(olap.DB):
        return
    from . import cargar_modelo
    if os.path.exists(cargar_modelo.CSV_POR_DEFECTO):
        cargar_modelo.construir(cargar_modelo.CSV_POR_DEFECTO, olap.DB)


_asegurar_modelo()

bp = Blueprint("multidim", __name__, url_prefix="/analisis-multidimensional")

SECCIONES = [
    ("multidim.indice", "Resumen"),
    ("multidim.modelo", "Modelo estrella"),
    ("multidim.operaciones", "Operaciones"),
    ("multidim.conocimientos", "Conocimientos"),
]


@lru_cache(maxsize=1)
def _validacion():
    ruta = os.path.join(AQUI, "reporte_validacion.json")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return None


@bp.context_processor
def _contexto():
    proy = dict(getattr(_contenido, "PROYECTO", {}) or {}, etapa="Etapa 5 · Análisis multidimensional")
    e4 = getattr(_contenido, "CONOCIMIENTO_EVIDENTE", {}) or {}
    repo = e4.get("repositorio_url") or (getattr(_contenido, "RECURSOS3", {}) or {}).get("repo_url")
    return dict(activo="multidimensional", secciones=SECCIONES, vistas=VISTAS, cf=cifras.calcular(), proyecto=proy,
                repo_url=repo, app_url=e4.get("app_publicada_url"), relacion_nota=conocimientos.RELACION_NOTA)


@bp.route("/", endpoint="indice")
def indice():
    conoc, por_vista, relacion, limitaciones, conclusiones = conocimientos.todos()
    return render_template("multidimensional/indice.html", relacion=relacion, conocimientos=conoc,
                           por_vista=por_vista, limitaciones=limitaciones, conclusiones=conclusiones,
                           seccion="multidim.indice", dimensiones=documentacion.DIMENSIONES)


@bp.route("/modelo", endpoint="modelo")
def modelo():
    return render_template("multidimensional/modelo.html", seccion="multidim.modelo", doc=documentacion,
                           medidas=documentacion.medidas(), validacion=_validacion())


@bp.route("/operaciones", endpoint="operaciones")
def operaciones_pagina():
    return render_template("multidimensional/operaciones.html", seccion="multidim.operaciones",
                           ejemplos=operaciones.ejemplos())


@bp.route("/conocimientos", endpoint="conocimientos")
def conocimientos_pagina():
    conoc, por_vista, relacion, limitaciones, conclusiones = conocimientos.todos()
    return render_template("multidimensional/conocimientos.html", seccion="multidim.conocimientos",
                           conocimientos=conoc, por_vista=por_vista, limitaciones=limitaciones,
                           conclusiones=conclusiones)


@bp.route("/vista/<vid>")
def vista(vid):
    modulo = POR_ID.get(vid)
    if modulo is None:
        abort(404)
    r = modulo.construir(request.args)
    est = r["est"]
    conoc, por_vista, _, _, _ = conocimientos.todos()
    cfg = modulo.CFG
    filtros = comun.widgets_filtro(est)
    claves_form = {w["param"] for w in filtros} | {"eje_f", "eje_c", "medida", "top"}
    ocultos = [(k, v) for k, v in est.pares() if k not in claves_form]
    dims = [d for d in cfg["niveles_base"] if d in cfg["ejes_permitidos"]]
    controles = [comun.controles_nivel(est, d) for d in dims]
    ops = olap.tipo_operacion(est.filtros, cfg["niveles_base"], est.niveles, est.pivot)
    i = VISTAS.index(modulo)
    return render_template(
        "multidimensional/vista.html", seccion="vista", m=modulo, r=r, est=est, filtros=filtros, ocultos=ocultos,
        controles=controles, ops=ops, quitar=[(olap.etiqueta(n), ", ".join(v), est.url(**{"f_" + n: None}))
                                                for n, v in est.filtros.items()],
        pivot_url=est.url(pivot=None if est.pivot else "1"),
        ejes=[(d, olap.DIMENSIONES[d]["nombre"]) for d in cfg["ejes_permitidos"]],
        medidas=[(k, olap.MEDIDAS[k]["nombre"] + " (" + olap.MEDIDAS[k]["unidad"] + ")")
                 for k in cfg.get("medidas_matriz", [cfg["medida"]])],
        limpiar=request.path, conoc=conoc[vid], extra=por_vista[vid],
        anterior=VISTAS[i - 1] if i > 0 else None, siguiente=VISTAS[i + 1] if i + 1 < len(VISTAS) else None,
        medida_def=olap.MEDIDAS[est.medida])
