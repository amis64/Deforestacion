# -*- coding: utf-8 -*-
"""Vista 3 · Intensidad de emisiones según causa y transformación (Causa × Transformación × Territorio)."""

from .. import graficos, olap
from . import comun

ID = "intensidad-de-emisiones"
TITULO = "Intensidad de emisiones según causa, transformación del suelo y región"
PREGUNTA = ("¿Cuántas emisiones de CO₂e acompañan cada hectárea perdida según la causa, la clase de "
            "transformación del suelo y la región, y qué combinaciones están peor documentadas?")

CFG = dict(
    niveles_base={"territorio": "region", "causa": "causa", "transformacion": "clase", "tiempo": "periodo"},
    filtros_ui=[("region", "Región natural (dimensión Territorio)"),
                ("clase", "Clase de transformación (dimensión Transformación)")],
    ejes_permitidos=["causa", "transformacion", "territorio"], eje_f="causa", eje_c="transformacion",
    medida="intensidad", medidas_matriz=["intensidad", "emisiones", "area"], top=15,
)

META = dict(
    dimensiones=["Causa", "Transformación del suelo", "Territorio"],
    medidas=["Intensidad de emisiones (Mg CO₂e/ha)", "Emisiones de CO₂e (Mg CO₂e)", "Área perdida de bosque (ha)"],
    jerarquias=["Causa: grupo de causa → causa", "Territorio: región natural → departamento → municipio"],
    profundiza=("La Etapa 4 (página multivariada) encontró que área perdida y emisiones se mueven casi igual "
                "(r = 0,998) y que la transformación del suelo acompaña a la pérdida. Una correlación tan alta "
                "no dice si cada hectárea emite lo mismo en todas partes. Aquí se descompone la RELACIÓN "
                "(emisiones por hectárea) según causa, clase de transformación y región."),
)


def construir(args):
    est = comun.Estado(args, CFG)
    nf, nc = est.niveles[est.dim_filas], est.niveles[est.dim_cols]
    medida = est.medida
    res = olap.consultar(medida, nf, nc, est.filtros, top=est.top)
    base = olap.consultar("area", nf, nc, est.filtros, top=est.top)
    sqls = [res["sql"], base["sql"]]

    def sub(f, c, v, r):
        a = base["celdas"].get((f, c))
        if a is None:
            return ""
        return "base: %s ha%s" % (olap.formato(a), " · base pequeña" if a < 1000 else "")

    matriz = comun.armar_matriz(est, res, sub=sub,
                                titulo="%s (%s) por %s y %s" % (olap.MEDIDAS[medida]["nombre"], olap.MEDIDAS[medida]["unidad"],
                                                              olap.etiqueta(nf).lower(), olap.etiqueta(nc).lower()))

    em, s1 = olap.escalar("emisiones", est.filtros)
    it, s2 = olap.escalar("intensidad", est.filtros)
    ha, s3 = olap.escalar("area", est.filtros)
    sc, s4 = olap.escalar("area_sin_clase", est.filtros)
    ind = [
        dict(etiqueta="Emisiones de CO₂e en la selección", valor=olap.formato(em, "emisiones"), unidad="Mg CO₂e",
             nota="Suma; en municipio-años con copias se usó el promedio."),
        dict(etiqueta="Intensidad de emisiones", valor=olap.formato(it, "intensidad"), unidad="Mg CO₂e por ha perdida",
             nota="Cociente de sumas (solo filas con área > 0); no es un promedio de promedios."),
        dict(etiqueta="Pérdida sin clase de transformación", valor=comun.pct(sc, ha), unidad="de la pérdida",
             nota="Denominador: pérdida total de la selección. Es faltante de cobertura, no ausencia de transformación."),
    ]
    sqls += [s1, s2, s3, s4]

    por_fila = olap.consultar("intensidad", nf, None, est.filtros, top=12)
    ha_fila = olap.consultar("area", nf, None, est.filtros)
    items = [(f, por_fila["tot_fila"][f]) for f in por_fila["filas"]
             if por_fila["tot_fila"].get(f) is not None and (ha_fila["tot_fila"].get(f) or 0) >= 1000]
    items.sort(key=lambda x: -x[1])
    g1 = graficos.barras_h(items, "Mg CO₂e/ha", 0, colores=comun.COLORES, referencia=it,
                           etiqueta_ref="selección: %s" % olap.formato(it, "intensidad"))
    sqls.append(por_fila["sql"])

    comp = olap.consultar("area", "region", "clase", est.filtros)
    sqls.append(comp["sql"])
    g2 = graficos.barras_apiladas(comp["filas"], comp["columnas"], comp["celdas"], porcentaje=True,
                                  colores={c: comun.COLORES.get(c) for c in comp["columnas"] if comun.COLORES.get(c)})
    graficas = [
        dict(titulo="Intensidad de emisiones (Mg CO₂e/ha) por %s" % olap.etiqueta(nf).lower(), svg=g1,
             nota="Solo categorías con al menos 1.000 ha de pérdida; la línea punteada es la intensidad de toda la selección."),
        dict(titulo="Clase de transformación del suelo en cada región (100 % = pérdida de la región)", svg=g2,
             nota="'Sin clase informada' es la parte de la pérdida que MapBiomas no clasifica."),
    ]
    return dict(est=est, res=res, matriz=matriz, indicadores=ind, graficas=graficas,
                interpretacion=comun.interpretacion_matriz(res, "de la selección"), sqls=sqls)
