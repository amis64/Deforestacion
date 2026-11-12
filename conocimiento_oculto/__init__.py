# -*- coding: utf-8 -*-
"""
Blueprint «Conocimiento Oculto» (Etapa 6).

Se registra en app.py con:

    from conocimiento_oculto import bp as oculto_bp
    app.register_blueprint(oculto_bp)

Rutas (bajo /conocimiento-oculto):
    /                 síntesis de hallazgos, informe técnico, video de sustentación y recursos
    /supervisado      pregunta, variables, tres modelos, comparación, matriz de confusión y modelo elegido (pérdida alta sí/no)
    /clustering       pregunta, variables, elección de k, perfiles de los grupos y su descripción
    /comentarios      comentarios de YouTube: videos, limpieza, temas, grupos, evidencias y límites
    /conclusiones     relación entre los tres análisis, hallazgos con evidencia e hipótesis por validar
Las cifras se leen de conocimiento_oculto/resultados/*.json (generados por referencia.py y
youtube/analizar_comentarios.py con los mismos datos que se cargan en Orange).
"""
import json
import os
import re
from functools import lru_cache

from flask import Blueprint, render_template

try:
    import contenido as _contenido
except ImportError:  # pragma: no cover
    _contenido = None

from . import config
from multidimensional import graficos as g
from . import graficos_oculto as go

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
RES = os.path.join(AQUI, "resultados")

bp = Blueprint("oculto", __name__, url_prefix="/conocimiento-oculto")

SECCIONES = [
    ("oculto.indice", "Resumen"),
    ("oculto.supervisado", "Modelos supervisados"),
    ("oculto.clustering", "Clustering"),
    ("oculto.comentarios", "Comentarios de YouTube"),
    ("oculto.conclusiones", "Conclusiones integradas"),
]


def _json(nombre):
    ruta = os.path.join(RES, nombre)
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return None


@lru_cache(maxsize=1)
def _datos():
    return dict(sup=_json("supervisado.json"), clu=_json("clustering.json"), com=_json("comentarios.json"), ora=_json("orange.json"))


def _video_embed(url):
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url or "")
    return "https://www.youtube.com/embed/" + m.group(1) if m else None


def _num(v, dec=0):
    return g._num(v, dec)


@bp.app_template_filter("n")
def _filtro_n(v, dec=0):
    return _num(v, dec)


@bp.context_processor
def _contexto():
    proy = dict(getattr(_contenido, "PROYECTO", {}) or {}, etapa="Etapa 6 · Conocimiento Oculto")
    e4 = getattr(_contenido, "CONOCIMIENTO_EVIDENTE", {}) or {}
    repo = config.REPO_URL or e4.get("repositorio_url")
    app = (config.APP_URL or e4.get("app_publicada_url") or "").rstrip("/")
    informe = config.INFORME_PDF if os.path.exists(os.path.join(RAIZ, "static", config.INFORME_PDF)) else None
    return dict(activo="oculto", secciones=SECCIONES, proyecto=proy, repo_url=repo, app_url=app, informe_pdf=informe,
                video_url=config.VIDEO_URL, video_embed=_video_embed(config.VIDEO_URL), d=_datos())


@bp.route("/", endpoint="indice")
def indice():
    return render_template("conocimiento_oculto/indice.html", seccion="oculto.indice")


@bp.route("/supervisado", endpoint="supervisado")
def pagina_supervisado():
    s = _datos()["sup"]
    graf = {}
    if s:
        nombres = list(s["modelos"])
        graf["f1"] = g.barras_h([(n, s["modelos"][n]["f1"] * 100) for n in nombres] +
                                [("Regla de persistencia", s["baseline_persistencia"]["f1"] * 100)], unidad=" %", dec=1)
        graf["acc"] = g.barras_h([(n, s["modelos"][n]["accuracy"] * 100) for n in nombres] +
                                 [("Regla de persistencia", s["baseline_persistencia"]["accuracy"] * 100)], unidad=" %", dec=1,
                                 referencia=s["baseline_mayoritaria"] * 100, etiqueta_ref="Predecir siempre «No alta»")
        graf["imp"] = g.barras_h([(k, v * 100) for k, v in s["importancia_variables"].items()], unidad=" %", dec=1)
        graf["roc"] = go.curvas_roc({n: s["modelos"][n]["roc"] for n in nombres})
        graf["anio"] = g.lineas([str(a) for a in s["modelos"][s["elegido"]]["por_anio"]],
                                {"Exactitud": [v["accuracy"] * 100 for v in s["modelos"][s["elegido"]]["por_anio"].values()],
                                 "Recall de la clase Alta": [v["recall"] * 100 for v in s["modelos"][s["elegido"]]["por_anio"].values()]}, unidad=" %", dec=0)
    return render_template("conocimiento_oculto/supervisado.html", seccion="oculto.supervisado", graf=graf)


@bp.route("/clustering", endpoint="clustering")
def pagina_clustering():
    c = _datos()["clu"]
    graf = {}
    if c:
        graf["sil"] = g.lineas([str(x["k"]) for x in c["comparacion"]], {"Silueta": [x["silueta"] for x in c["comparacion"]]}, dec=2)
        graf["tam"] = g.barras_h([(p["nombre"], p["municipios"]) for p in c["perfil"]], dec=0)
        graf["mapa"] = go.mapa_grupos(c["mapa"], {p["grupo"]: "%d · %s" % (p["grupo"], p["nombre"]) for p in c["perfil"]})
    return render_template("conocimiento_oculto/clustering.html", seccion="oculto.clustering", graf=graf)


@bp.route("/comentarios", endpoint="comentarios")
def pagina_comentarios():
    y = _datos()["com"]
    graf = {}
    if y:
        graf["terminos"] = g.barras_h([(t["termino"], t["comentarios"]) for t in y["terminos"][:15]], dec=0)
        graf["familias"] = g.barras_h([(f["nombre"], f["comentarios"]) for f in sorted(y["familias"], key=lambda f: -f["comentarios"])], dec=0)
        graf["anio"] = g.barras_h([(k, v) for k, v in y["resumen"]["por_anio"].items()], dec=0)
    return render_template("conocimiento_oculto/comentarios.html", seccion="oculto.comentarios", graf=graf)


@bp.route("/conclusiones", endpoint="conclusiones")
def pagina_conclusiones():
    return render_template("conocimiento_oculto/conclusiones.html", seccion="oculto.conclusiones")
