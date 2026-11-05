# -*- coding: utf-8 -*-
"""Vista 2 · ¿Dónde y cuándo cambió la pérdida entre 2001–2012 y 2013–2024? (Tiempo × Territorio)."""

from .. import graficos, olap
from . import comun

ID = "cambio-en-el-tiempo"
TITULO = "Cambio de la pérdida entre periodos y territorios"
PREGUNTA = ("¿En qué regiones y departamentos se concentró el cambio de la pérdida anual entre 2001–2012 y "
            "2013–2024, y en qué trienios ocurrió?")

CFG = dict(
    niveles_base={"territorio": "region", "tiempo": "periodo", "causa": "grupo"},
    filtros_ui=[("grupo", "Grupo de causa (dimensión Causa)"), ("region", "Región natural (dimensión Territorio)")],
    ejes_permitidos=["territorio", "tiempo", "causa"], eje_f="territorio", eje_c="tiempo",
    medida="promedio_anual", top=15,
)

META = dict(
    dimensiones=["Tiempo", "Territorio", "Causa (como filtro)"],
    medidas=["Pérdida promedio anual (ha/año)", "Área perdida de bosque (ha)"],
    jerarquias=["Tiempo: periodo (12 años) → trienio → año", "Territorio: región natural → departamento → municipio"],
    profundiza=("La Etapa 4 (página temporal) mostró que 2013–2024 pierde más bosque por año que 2001–2012 y que el "
                "salto más fuerte está en 2016–2018, y advirtió que «la evolución cambia según el departamento». "
                "Aquí se descompone ese aumento nacional por territorio y por trienio para saber QUIÉN lo "
                "explica y si el aumento es parejo o es un cambio de composición."),
)

P1, P2 = "2001–2012", "2013–2024"


def construir(args):
    est = comun.Estado(args, CFG)
    nf, nc = est.niveles[est.dim_filas], est.niveles[est.dim_cols]
    res = olap.consultar("promedio_anual", nf, nc, est.filtros, top=est.top)
    sqls = [res["sql"]]

    extras = None
    if nc == "periodo" and est.dim_cols == "tiempo":
        def delta(f, r):
            a, b = r["celdas"].get((f, P1)), r["celdas"].get((f, P2))
            return olap.formato(b - a, decimales=0) if a is not None and b is not None else "—"

        def delta_pct(f, r):
            a, b = r["celdas"].get((f, P1)), r["celdas"].get((f, P2))
            return olap.formato((b / a - 1) * 100, decimales=1) + " %" if a and b is not None else "—"
        extras = [("Cambio (ha/año)", delta), ("Cambio (%)", delta_pct)]
    matriz = comun.armar_matriz(est, res, columnas_extra=extras,
                                titulo="Pérdida promedio anual (ha/año) por %s y %s" % (olap.etiqueta(nf).lower(), olap.etiqueta(nc).lower()))

    # Indicadores: comparan SIEMPRE los dos periodos (ignoran filtros de tiempo)
    base = est.sin_filtros_de("periodo", "trienio")
    a, s1 = olap.escalar("promedio_anual", dict(base, periodo=[P1]))
    b, s2 = olap.escalar("promedio_anual", dict(base, periodo=[P2]))
    var = (b / a - 1) * 100 if a else None
    ind = [
        dict(etiqueta="Promedio anual 2001–2012", valor=olap.formato(a, "promedio_anual"), unidad="ha/año",
             nota="Total del periodo ÷ 12 años."),
        dict(etiqueta="Promedio anual 2013–2024", valor=olap.formato(b, "promedio_anual"), unidad="ha/año",
             nota="Total del periodo ÷ 12 años (periodos equivalentes)."),
        dict(etiqueta="Variación entre periodos", valor=("+" if var and var > 0 else "") + olap.formato(var, decimales=1),
             unidad="% (denominador: promedio 2001–2012)", nota="Se recalcula con los filtros de causa y región."),
    ]
    sqls += [s1, s2]

    # Gráfica 1: líneas por territorio
    nivel_t = "trienio" if est.niveles["tiempo"] == "periodo" else est.niveles["tiempo"]
    nt = est.niveles["territorio"]
    ser = olap.consultar("promedio_anual", nt, nivel_t, est.filtros, top=6)
    xs = ser["columnas"]
    series = {f: [ser["celdas"].get((f, x)) for x in xs] for f in ser["filas"]
              if f not in ("Insular", "Sin región informada")}
    g1 = graficos.lineas(xs, series, "ha/año", 0)
    sqls.append(ser["sql"])

    # Gráfica 2: cambio absoluto por territorio
    d1 = olap.consultar("promedio_anual", nt, None, dict(base, periodo=[P1]))
    d2 = olap.consultar("promedio_anual", nt, None, dict(base, periodo=[P2]))
    sqls += [d1["sql"], d2["sql"]]
    cambios = [(t, (d2["tot_fila"].get(t) or 0) - (d1["tot_fila"].get(t) or 0))
               for t in set(d1["tot_fila"]) | set(d2["tot_fila"]) if t not in ("Insular", "Sin región informada")]
    cambios = sorted(sorted(cambios, key=lambda x: -abs(x[1]))[:12], key=lambda x: -x[1])
    g2 = graficos.barras_divergentes(cambios, "ha/año")
    graficas = [
        dict(titulo="Pérdida promedio anual (ha/año) por %s y %s" % (olap.etiqueta(nt).lower(), olap.etiqueta(nivel_t).lower()),
             svg=g1, nota="Hasta 6 territorios con mayor pérdida; el promedio anual permite comparar trienios y periodos."),
        dict(titulo="Cambio de la pérdida anual 2013–2024 frente a 2001–2012 (ha/año)", svg=g2,
             nota="Barras ámbar: aumento; verdes: disminución. Hasta 12 territorios con mayor cambio absoluto (la región Insular, con menos de 50 ha/año, no se grafica)."),
    ]
    interp = comun.interpretacion_matriz(res, "del total")
    return dict(est=est, res=res, matriz=matriz, indicadores=ind, graficas=graficas, interpretacion=interp, sqls=sqls)
