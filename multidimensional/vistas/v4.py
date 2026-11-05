# -*- coding: utf-8 -*-
"""Vista 4 · Focos de calor y cobertura de fuentes (Fuente × Tiempo × Territorio)."""

from .. import graficos, olap
from . import comun

ID = "focos-y-fuentes"
TITULO = "Focos de calor y cobertura de las fuentes"
PREGUNTA = ("¿Cuántos focos de calor acompañan cada 100 ha perdidas en cada región y trienio, y cuánta de la "
            "pérdida está realmente cubierta por la fuente de focos (FIRMS, 2012–2022)?")

CFG = dict(
    niveles_base={"territorio": "region", "tiempo": "trienio", "fuente": "fuente"},
    filtros_ui=[("fuente", "Combinación de fuentes (dimensión Fuente)"),
                ("region", "Región natural (dimensión Territorio)")],
    ejes_permitidos=["territorio", "tiempo", "fuente"], eje_f="territorio", eje_c="tiempo",
    medida="focos_100ha", medidas_matriz=["focos_100ha", "focos", "area_con_focos", "area"], top=15,
    filtros_extra=[("anio", "Año")],   # solo por URL (ventana 2012–2022 de los conocimientos)
)

META = dict(
    dimensiones=["Fuente", "Tiempo", "Territorio"],
    medidas=["Focos por 100 ha perdidas (focos/100 ha)", "Focos de calor (conteo)",
             "Pérdida en territorio-año con focos registrados (ha)"],
    jerarquias=["Fuente: número de fuentes → combinación de fuentes", "Tiempo: periodo → trienio → año",
                "Territorio: región natural → departamento → municipio"],
    profundiza=("La Etapa 4 (página multivariada) halló que los focos de calor se relacionan con la pérdida menos que "
                "la transformación del suelo (r = 0,48). Aquí se pregunta si esa relación débil es pareja o si "
                "depende de la región, del año y de qué fuentes cubren cada territorio: la fuente de focos solo "
                "existe en 2012–2022, así que comparar periodos con ella exige cuidado."),
)

VENTANA_FIRMS = "anio BETWEEN 2012 AND 2022"


def construir(args):
    est = comun.Estado(args, CFG)
    nf, nc = est.niveles[est.dim_filas], est.niveles[est.dim_cols]
    medida = est.medida
    res = olap.consultar(medida, nf, nc, est.filtros, top=est.top)
    sqls = [res["sql"]]
    sub = None
    if medida == "focos_100ha":
        base = olap.consultar("area_con_focos", nf, nc, est.filtros, top=est.top)
        sqls.append(base["sql"])

        def sub(f, c, v, r):
            a = base["celdas"].get((f, c))
            return "" if a is None else ("base: %s ha%s" % (olap.formato(a), " · base pequeña" if a < 1000 else ""))
    matriz = comun.armar_matriz(est, res, sub=sub, titulo="%s (%s) por %s y %s" % (
        olap.MEDIDAS[medida]["nombre"], olap.MEDIDAS[medida]["unidad"], olap.etiqueta(nf).lower(), olap.etiqueta(nc).lower()))

    focos, s1 = olap.escalar("focos", est.filtros)
    r100, s2 = olap.escalar("focos_100ha", est.filtros)
    ac, s3 = olap.escalar("area_con_focos", est.filtros, extra=VENTANA_FIRMS)
    at, s4 = olap.escalar("area", est.filtros, extra=VENTANA_FIRMS)
    ind = [
        dict(etiqueta="Focos de calor registrados", valor=olap.formato(focos, "focos"), unidad="focos (FIRMS, 2012–2022)",
             nota="Solo los territorio-año con dato de focos; un faltante NO equivale a cero focos."),
        dict(etiqueta="Focos por 100 ha perdidas", valor=olap.formato(r100, "focos_100ha"), unidad="focos/100 ha",
             nota="Denominador: pérdida de los territorio-año que sí tienen focos registrados."),
        dict(etiqueta="Pérdida 2012–2022 con focos registrados", valor=comun.pct(ac, at), unidad="de la pérdida 2012–2022",
             nota="Cobertura de la fuente FIRMS; denominador: toda la pérdida de la selección en 2012–2022."),
    ]
    sqls += [s1, s2, s3, s4]

    por_t = olap.consultar("focos_100ha", est.niveles["territorio"], None, est.filtros, top=12)
    sqls.append(por_t["sql"])
    items = sorted([(f, por_t["tot_fila"][f]) for f in por_t["filas"]
                    if por_t["tot_fila"].get(f) is not None and f not in ("Insular", "Sin región informada")],
                   key=lambda x: -x[1])
    g1 = graficos.barras_h(items, "focos/100 ha", 1)

    ser = olap.consultar("focos_100ha", "region", "anio", est.filtros, extra=VENTANA_FIRMS)
    sqls.append(ser["sql"])
    series = {f: [ser["celdas"].get((f, x)) for x in ser["columnas"]] for f in ser["filas"]
              if f not in ("Insular", "Sin región informada")}
    g2 = graficos.lineas(ser["columnas"], series, "focos/100 ha", 0)
    graficas = [
        dict(titulo="Focos por 100 ha perdidas por %s" % olap.etiqueta(est.niveles["territorio"]).lower(), svg=g1,
             nota="Razón de sumas dentro de la ventana con dato de focos (2012–2022). La región Insular no se grafica: su base es de pocas hectáreas."),
        dict(titulo="Focos por 100 ha perdidas, por año y región (2012–2022)", svg=g2,
             nota="Fuera de 2012–2022 la fuente no trae focos; la región Insular se omite por tener casi 0 ha."),
    ]
    return dict(est=est, res=res, matriz=matriz, indicadores=ind, graficas=graficas,
                interpretacion=comun.interpretacion_matriz(res, "de la selección"), sqls=sqls)
