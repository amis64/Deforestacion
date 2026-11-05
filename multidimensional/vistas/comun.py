# -*- coding: utf-8 -*-
"""
comun.py
========
Piezas compartidas por las cuatro vistas: lectura del estado desde la URL
(niveles de jerarquía, filtros, ejes, pivot), construcción de enlaces para
drill-down / roll-up / pivot, y armado de la matriz de resultados.
"""

from functools import lru_cache
from urllib.parse import urlencode

from .. import olap

CLASES_CALOR = 6


@lru_cache(maxsize=None)
def opciones(nivel):
    return olap.valores_de(nivel)


class Estado:
    """Selección activa de una vista, leída de los parámetros de la URL."""

    def __init__(self, args, cfg):
        self.cfg = cfg
        self.niveles = {}
        for dim, base in cfg["niveles_base"].items():
            n = args.get("n_" + dim, base)
            self.niveles[dim] = n if n in olap.DIMENSIONES[dim]["niveles"] else base
        self.filtros = {}
        for nivel, _ in cfg["filtros_ui"] + cfg.get("filtros_extra", []):
            vals = [v for v in args.getlist("f_" + nivel) if v]
            if vals:
                self.filtros[nivel] = vals
        self.pivot = args.get("pivot") == "1"
        self.eje_f = args.get("eje_f") if args.get("eje_f") in cfg["ejes_permitidos"] else cfg["eje_f"]
        self.eje_c = args.get("eje_c") if args.get("eje_c") in cfg["ejes_permitidos"] else cfg["eje_c"]
        if self.eje_c == self.eje_f:
            self.eje_c = next(d for d in cfg["ejes_permitidos"] if d != self.eje_f)
        medidas = cfg.get("medidas_matriz", [cfg["medida"]])
        self.medida = args.get("medida") if args.get("medida") in medidas else cfg["medida"]
        try:
            self.top = max(5, min(50, int(args.get("top", cfg.get("top", 15)))))
        except ValueError:
            self.top = cfg.get("top", 15)

    # ----- ejes efectivos (con pivot) -------------------------------------
    @property
    def dim_filas(self):
        return self.eje_c if self.pivot else self.eje_f

    @property
    def dim_cols(self):
        return self.eje_f if self.pivot else self.eje_c

    def nivel_de(self, dim):
        return self.niveles[dim]

    # ----- enlaces -----------------------------------------------------------
    def pares(self, **cambios):
        """Pares (clave, valor) de la URL con 'cambios' aplicados. valor=None elimina la clave."""
        base = self.cfg
        estado = {}
        for dim, n in self.niveles.items():
            if n != base["niveles_base"][dim]:
                estado["n_" + dim] = n
        for nivel, vals in self.filtros.items():
            estado["f_" + nivel] = list(vals)
        if self.pivot:
            estado["pivot"] = "1"
        if self.eje_f != base["eje_f"]:
            estado["eje_f"] = self.eje_f
        if self.eje_c != base["eje_c"]:
            estado["eje_c"] = self.eje_c
        if self.medida != base["medida"]:
            estado["medida"] = self.medida
        if self.top != base.get("top", 15):
            estado["top"] = self.top
        for k, v in cambios.items():
            k = k.replace("__", "_")
            if v is None:
                estado.pop(k, None)
            else:
                estado[k] = v
        out = []
        for k, v in estado.items():
            if isinstance(v, (list, tuple)):
                out.extend((k, x) for x in v)
            else:
                out.append((k, v))
        return out

    def url(self, **cambios):
        p = self.pares(**cambios)
        return "?" + urlencode(p) if p else "?"

    # ----- consultas -----------------------------------------------------------
    def sin_filtros_de(self, *niveles):
        return {k: v for k, v in self.filtros.items() if k not in niveles}


def controles_nivel(est, dim):
    """Control drill-down / roll-up de una dimensión (devuelve enlaces o None si no aplica)."""
    actual = est.niveles[dim]
    sig = olap.nivel_siguiente(dim, actual)
    ant = olap.nivel_anterior(dim, actual)
    return dict(
        dimension=olap.DIMENSIONES[dim]["nombre"],
        actual=olap.etiqueta(actual),
        niveles=[dict(clave=k, etiqueta=v[0], url=est.url(**{"n_" + dim: k}), activo=(k == actual))
                 for k, v in olap.DIMENSIONES[dim]["niveles"].items()],
        abajo=(dict(etiqueta=olap.etiqueta(sig), url=est.url(**{"n_" + dim: sig})) if sig else None),
        arriba=(dict(etiqueta=olap.etiqueta(ant), url=est.url(**{"n_" + dim: ant, "f_" + ant: None})) if ant else None),
    )


def widgets_filtro(est):
    """Dos (o más) filtros interactivos: opciones y selección activa."""
    out = []
    for nivel, etq in est.cfg["filtros_ui"]:
        out.append(dict(nivel=nivel, param="f_" + nivel, etiqueta=etq, opciones=opciones(nivel),
                        seleccion=est.filtros.get(nivel, []),
                        dimension=olap.DIMENSIONES[olap.dimension_de(nivel)]["nombre"]))
    return out


def migas(est):
    """Ruta de navegación: qué filtros y niveles hay activos."""
    partes = []
    for nivel, vals in est.filtros.items():
        partes.append("%s: %s" % (olap.etiqueta(nivel), ", ".join(vals)))
    return partes


def clase_calor(v, mx):
    if v is None or not mx or v <= 0:
        return ""
    return "calor-%d" % max(1, min(CLASES_CALOR, int(round(v / mx * CLASES_CALOR))))


def armar_matriz(est, res, sub=None, columnas_extra=None, titulo=""):
    """
    Convierte el resultado de olap.consultar en la estructura que pinta la plantilla.

    sub(f, c, valor, res) -> texto pequeño bajo el valor de la celda (p. ej. % de la fila).
    columnas_extra: [(encabezado, funcion(f, res) -> texto)] columnas calculadas al final.
    """
    medida = res["medida"]
    todos = [v for v in res["celdas"].values() if v is not None]
    mx = max(todos) if todos else 0
    dim_f = olap.dimension_de(res["nivel_filas"])
    sig = olap.nivel_siguiente(dim_f, res["nivel_filas"])
    filas = []
    for f in res["filas"]:
        celdas = []
        for c in res["columnas"]:
            v = res["celdas"].get((f, c))
            celdas.append(dict(txt=olap.formato(v, medida), sub=(sub(f, c, v, res) if sub and v is not None else ""),
                               clase=clase_calor(v, mx)))
        fila = dict(etiqueta=f, celdas=celdas, total=olap.formato(res["tot_fila"].get(f), medida),
                    extras=[fn(f, res) for _, fn in (columnas_extra or [])])
        # drill-down al hacer clic en un miembro de la fila (solo si el eje de filas es la dimensión pivotada)
        if sig and dim_f == est.dim_filas:
            fila["url"] = est.url(**{"f_" + res["nivel_filas"]: [f], "n_" + dim_f: sig})
            fila["destino"] = olap.etiqueta(sig)
        filas.append(fila)
    return dict(
        titulo=titulo, nivel_filas=olap.etiqueta(res["nivel_filas"]),
        nivel_columnas=olap.etiqueta(res["nivel_columnas"]) if res["nivel_columnas"] else "",
        cabecera=list(res["columnas"]), extras=[h for h, _ in (columnas_extra or [])],
        filas=filas, pie=[olap.formato(res["tot_col"].get(c), medida) for c in res["columnas"]],
        pie_total=olap.formato(res["total"], medida), omitidas=res["omitidas"],
        medida=olap.MEDIDAS[medida]["nombre"], unidad=olap.MEDIDAS[medida]["unidad"])


def pct(parte, total, dec=1):
    if not total:
        return "—"
    return olap.formato(parte / total * 100, decimales=dec) + " %"


# Colores fijos por causa / grupo / clase para que cada categoría tenga el mismo color en todas las gráficas.
COLORES = {
    "Agropecuaria": "#1f3a2e", "Forestal (plantaciones)": "#6aa27b", "Natural": "#c98a3a",
    "Infraestructura y minería": "#7a4f2b", "Sin causa informada": "#b9b6ab", "No aplica": "#d8d5cb",
    "Agricultura permanente": "#1f3a2e", "Agricultura migratoria": "#3f6b4f", "Silvicultura": "#6aa27b",
    "Incendios forestales": "#c98a3a", "Otras alteraciones naturales": "#e0b66a",
    "Urbanizacion e infraestructura": "#7a4f2b", "Mineria y otras materias primas": "#a65a5a",
    "Área agropecuaria": "#1f3a2e", "Área sin vegetación": "#c98a3a", "Sin clase informada": "#b9b6ab",
}


def interpretacion_matriz(res, unidad_total="del total"):
    """Frase de lectura generada con los números de la selección activa (denominadores explícitos)."""
    med = res["medida"]
    if not res["filas"] or not res["total"]:
        return "La selección actual no tiene datos."
    tf = res["tot_fila"]
    mejor = max(res["filas"], key=lambda f: tf.get(f) or 0)
    txt = "%s es la fila con el valor más alto (%s %s)" % (
        mejor, olap.formato(tf.get(mejor), med), olap.MEDIDAS[med]["unidad"])
    if olap.MEDIDAS[med]["agregacion"] in ("SUM", "CONTEO"):
        txt += ", es decir %s %s de la selección" % (pct(tf.get(mejor), res["total"]), unidad_total)
    txt += "."
    if res["nivel_columnas"] and len(res["columnas"]) > 1:
        col = max(res["columnas"], key=lambda c: res["celdas"].get((mejor, c)) or 0)
        v = res["celdas"].get((mejor, col))
        if v is not None and tf.get(mejor):
            if olap.MEDIDAS[med]["agregacion"] in ("SUM", "CONTEO"):
                txt += " Dentro de %s, la columna que más pesa es «%s» (%s de la fila; denominador: total de la fila)." % (
                    mejor, col, pct(v, tf.get(mejor)))
            else:
                txt += " Dentro de %s, el valor más alto está en «%s» (%s %s)." % (
                    mejor, col, olap.formato(v, med), olap.MEDIDAS[med]["unidad"])
    return txt
