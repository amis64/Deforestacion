# -*- coding: utf-8 -*-
"""Vista 1 · ¿Qué causas explican la pérdida de bosque en cada territorio? (Territorio × Causa)."""

from .. import graficos, olap
from . import comun

ID = "causas-por-territorio"
TITULO = "Causas de la pérdida de bosque por territorio"
PREGUNTA = ("¿Qué causas explican la pérdida de bosque en cada región natural, y cambia el patrón al bajar "
            "al nivel de departamento o de municipio y al comparar los dos periodos?")

CFG = dict(
    niveles_base={"territorio": "region", "causa": "grupo", "tiempo": "periodo"},
    filtros_ui=[("periodo", "Periodo (dimensión Tiempo)"), ("region", "Región natural (dimensión Territorio)")],
    ejes_permitidos=["territorio", "causa", "tiempo"], eje_f="territorio", eje_c="causa",
    medida="area", top=15,
    filtros_extra=[("causa", "Causa"), ("grupo", "Grupo de causa")],   # solo por URL (enlaces de los conocimientos)
)

META = dict(
    dimensiones=["Territorio", "Causa", "Tiempo (como filtro)"],
    medidas=["Área perdida de bosque (ha)", "Territorios con pérdida (conteo distinto)"],
    jerarquias=["Territorio: región natural → departamento → municipio", "Causa: grupo de causa → causa"],
    profundiza=("En la Etapa 4 (página poblacional y territorial) se vio que la agricultura permanente explica la "
                "mayor parte de los registros y que cinco departamentos concentran más de la mitad de la pérdida, "
                "pero cada hallazgo se miró por separado. Aquí se CRUZAN territorio y causa, y se baja por la "
                "jerarquía para ver si el patrón «nacional» se sostiene en cada región, departamento y periodo."),
)


def construir(args):
    est = comun.Estado(args, CFG)
    nf, nc = est.niveles[est.dim_filas], est.niveles[est.dim_cols]
    res = olap.consultar("area", nf, nc, est.filtros, top=est.top)
    sqls = [res["sql"]]

    def sub(f, c, v, r):
        return comun.pct(v, r["tot_fila"].get(f))

    matriz = comun.armar_matriz(est, res, sub=sub,
                                titulo="Área perdida (ha) y, bajo cada valor, %% del total de la fila (denominador) por %s y %s" % (olap.etiqueta(nf).lower(), olap.etiqueta(nc).lower()))

    total, s1 = olap.escalar("area", est.filtros)
    por_causa = olap.consultar("area", "causa", None, est.filtros)
    sqls.append(por_causa["sql"])
    causas = [(c, por_causa["tot_fila"][c]) for c in por_causa["filas"]
              if c not in ("Sin causa informada", "No aplica") and (por_causa["tot_fila"][c] or 0) > 0]
    causas.sort(key=lambda x: -x[1])
    n_terr, s3 = olap.escalar("territorios", est.filtros)
    principal = causas[0] if causas else ("—", 0)
    ind = [
        dict(etiqueta="Área perdida en la selección", valor=olap.formato(total, "area"), unidad="ha",
             nota="Suma de hectáreas, una fila por municipio-año."),
        dict(etiqueta="Causa principal", valor=principal[0], unidad=comun.pct(principal[1], total) + " de la pérdida",
             nota="Denominador: pérdida total de la selección."),
        dict(etiqueta="Municipios con pérdida", valor=olap.formato(n_terr, "territorios"), unidad="municipios distintos",
             nota="Conteo de entidades únicas (no de filas)."),
    ]
    sqls += [s1, s3]

    g1 = graficos.barras_apiladas(
        res["filas"][:10], res["columnas"], res["celdas"], porcentaje=True,
        colores={c: comun.COLORES.get(c) for c in res["columnas"] if comun.COLORES.get(c)})
    g2 = graficos.barras_h([(c, v) for c, v in causas[:8]], "ha", colores=comun.COLORES)
    graficas = [
        dict(titulo="Composición de la pérdida por %s (100 %% = pérdida de cada fila)" % olap.etiqueta(nc).lower(), svg=g1,
             nota="Cada barra suma 100 % de la pérdida de su fila; pasa el cursor sobre un tramo para ver las hectáreas."),
        dict(titulo="Área perdida (ha) por causa en la selección", svg=g2,
             nota="Se excluyen 'Sin causa informada' y 'No aplica'; no hay pérdida asociada a esas categorías en la selección."),
    ]
    return dict(est=est, res=res, matriz=matriz, indicadores=ind, graficas=graficas,
                interpretacion=comun.interpretacion_matriz(res, "de la pérdida"), sqls=sqls)
