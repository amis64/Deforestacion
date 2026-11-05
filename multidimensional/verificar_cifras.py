# -*- coding: utf-8 -*-
"""
verificar_cifras.py
===================
Comprobación INDEPENDIENTE de las cifras de los conocimientos: las recalcula
directamente desde deforestacion_limpio.csv con pandas (sin pasar por el modelo
estrella ni por olap.py) y las compara con lo que muestra la aplicación.

Uso (requiere pandas; es una herramienta de verificación, no de ejecución):

    python multidimensional/verificar_cifras.py
"""

import os
import sys

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from multidimensional import cifras  # noqa: E402
from multidimensional.cargar_modelo import DEPTO_A_REGION  # noqa: E402

P1, P2 = "2001–2012", "2013–2024"


def a_num(txt):
    return float(str(txt).replace(".", "").replace(",", "."))


def main():
    d = pd.read_csv(os.path.join(RAIZ, "deforestacion_limpio.csv"), low_memory=False)
    d = d[d.nivel_analisis == "Regional"].copy()
    d["region"] = d.departamento.map(DEPTO_A_REGION)
    g = d.groupby(["departamento", "municipio", "anio"], as_index=False, dropna=False).agg(
        area=("area_perdida_bosque_ha", "first"), emis=("emisiones_co2_mg", "mean"),
        focos=("num_focos_calor", "first"), driver=("driver_dominante", "first"),
        clase=("clase_transformacion_dominante", "first"), fuente=("fuente_origen", "first"),
        region=("region", "first"), n=("id_registro", "count"))
    g["periodo"] = g.anio.map(lambda a: P1 if a <= 2012 else P2)
    g["nfu"] = g.fuente.fillna("").map(lambda s: len([x for x in s.split("+") if x]))
    c = cifras.calcular()
    tot = g.area.sum()
    ap = g[g.driver == "Agricultura permanente"].area.sum()
    choco = g[(g.departamento == "Chocó") & (g.driver == "Incendios forestales")]
    inc = g[g.driver == "Incendios forestales"].area.sum()
    pa = g.groupby("periodo").area.sum() / 12
    amaz = g[g.region == "Amazonía"].groupby("periodo").area.sum() / 12
    pos = g[g.area > 0]
    inten = lambda x: x.emis.sum() / x.area.sum()  # noqa: E731
    sinclase = g[g.clase.isna()].area.sum()
    focos = g.focos.sum()
    r = g[(g.region == "Orinoquía") & g.focos.notna()]
    tres = g.groupby(["periodo", "nfu"]).area.sum()
    dp = g.groupby(["departamento", "periodo"]).area.sum().unstack().fillna(0) / 12
    camb = dp[P2] - dp[P1]
    cuatro = camb[["Caquetá", "Guaviare", "Putumayo", "Meta"]].sum()
    pruebas = [
        ("Registros del dataset (Regional)", len(d), None, None),
        ("Área total municipal (ha)", tot, c["area_total"], None),
        ("% agricultura permanente nacional", ap / tot * 100, c["ap_nacional"], 1),
        ("Incendios forestales, país (ha)", inc, c["inc_pais"], None),
        ("Incendios Chocó 2016 (ha)", choco[choco.anio == 2016].area.sum(), c["inc_choco_2016"], None),
        ("Promedio anual 2001–2012 (ha/año)", pa[P1], c["nac_p1"], None),
        ("Promedio anual 2013–2024 (ha/año)", pa[P2], c["nac_p2"], None),
        ("Variación entre periodos (%)", (pa[P2] / pa[P1] - 1) * 100, c["nac_var"], 1),
        ("Aporte neto Amazonía (ha/año)", amaz[P2] - amaz[P1], c["r_amaz_dif"], None),
        ("Intensidad nacional (Mg CO₂e/ha)", inten(pos), c["int_nac"], None),
        ("Intensidad Amazonía", inten(pos[pos.region == "Amazonía"]), c["int_amaz"], None),
        ("Intensidad Caribe", inten(pos[pos.region == "Caribe"]), c["int_caribe"], None),
        ("Pérdida sin clase de transformación (ha)", sinclase, c["sc_ha"], None),
        ("Focos de calor (total)", focos, c["focos_total"], None),
        ("Focos/100 ha Orinoquía", r.focos.sum() * 100 / r.area.sum(), c["f100_orin"], 1),
        ("Cuatro departamentos: % del aumento neto", cuatro / camb.sum() * 100, c["cuatro_dep_aporte"], 1),
        ("Cuatro departamentos: % de los aumentos brutos", cuatro / camb[camb > 0].sum() * 100, c["cuatro_pct_bruto"], 1),
        ("% pérdida con 3 fuentes en 2013–2024", tres[(P2, 3)] / tres[P2].sum() * 100, c["tres_p2"], 1),
    ]
    fallas = 0
    print("%-46s %18s %18s  %s" % ("Cifra", "Independiente", "Aplicación", "Resultado"))
    for nombre, indep, app, dec in pruebas:
        if app is None:
            print("%-46s %18s %18s  %s" % (nombre, "{:,.0f}".format(indep), "—", "(referencia)"))
            continue
        a = a_num(app)
        ok = abs(indep - a) <= (0.05 if dec == 1 else 1.0)
        fallas += not ok
        print("%-46s %18s %18s  %s" % (nombre, "{:,.2f}".format(indep), app, "OK" if ok else "DIFIERE"))
    print("\n%d cifras comprobadas, %d diferencias." % (len([p for p in pruebas if p[2] is not None]), fallas))
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
