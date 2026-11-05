# -*- coding: utf-8 -*-
"""
cifras.py
=========
Calcula, con consultas al modelo estrella, todas las cifras que citan los
textos de conocimientos, limitaciones y conclusiones. Así el texto nunca se
desalinea de los datos: si el modelo se recarga, las cifras se recalculan.
"""

from functools import lru_cache

from . import olap
from .olap import consultar, escalar, formato

P1, P2 = "2001–2012", "2013–2024"
VENTANA = "anio BETWEEN 2012 AND 2022"


def f0(v):
    return formato(v, decimales=0)


def f1(v):
    return formato(v, decimales=1)


def pc(parte, total, d=1):
    return formato(parte / total * 100, decimales=d)


@lru_cache(maxsize=1)
def calcular():
    c = {}
    con = olap.conectar()
    meta = con.execute("SELECT registros_origen, filas_hechos FROM meta_carga").fetchone()
    con.close()
    c["n_registros"], c["n_hechos"] = f0(meta[0]), f0(meta[1])
    total = escalar("area")[0]
    c["area_total"] = f0(total)
    c["n_municipios"] = f0(escalar("territorios")[0])

    # ---------------- Vista 1: causa × territorio -------------------------
    t = consultar("area", "region", "causa")
    cel, tf = t["celdas"], t["tot_fila"]
    ap_total = sum(v for (r, k), v in cel.items() if k == "Agricultura permanente" and v)
    c["ap_nacional"] = pc(ap_total, total)
    for clave, reg in (("amaz", "Amazonía"), ("andina", "Andina"), ("caribe", "Caribe"),
                       ("orin", "Orinoquía"), ("pac", "Pacífica")):
        c["ap_" + clave] = pc(cel[(reg, "Agricultura permanente")], tf[reg])
    c["mig_amaz"] = pc(cel[("Amazonía", "Agricultura migratoria")], tf["Amazonía"])
    c["mig_pac"] = pc(cel[("Pacífica", "Agricultura migratoria")], tf["Pacífica"])
    g = consultar("area", "region", "grupo")
    c["agro_pac"] = pc(g["celdas"][("Pacífica", "Agropecuaria")], g["tot_fila"]["Pacífica"])
    c["agro_min_otras"] = pc(min(g["celdas"][(r, "Agropecuaria")] / g["tot_fila"][r]
                                 for r in ("Amazonía", "Andina", "Caribe", "Orinoquía")) * 100, 100)
    c["agro_max_otras"] = pc(max(g["celdas"][(r, "Agropecuaria")] / g["tot_fila"][r]
                                 for r in ("Amazonía", "Andina", "Caribe", "Orinoquía")) * 100, 100)
    d = consultar("area", "departamento", "causa", {"region": ["Pacífica"]})
    for clave, dep in (("choco", "Chocó"), ("narino", "Nariño"), ("cauca", "Cauca"), ("valle", "Valle del Cauca")):
        c["dep_%s_total" % clave] = f0(d["tot_fila"][dep])
    c["choco_ap"] = pc(d["celdas"][("Chocó", "Agricultura permanente")], d["tot_fila"]["Chocó"])
    c["choco_mig"] = pc(d["celdas"][("Chocó", "Agricultura migratoria")], d["tot_fila"]["Chocó"])
    c["choco_inc"] = pc(d["celdas"][("Chocó", "Incendios forestales")], d["tot_fila"]["Chocó"])
    c["choco_min"] = pc(d["celdas"][("Chocó", "Mineria y otras materias primas")], d["tot_fila"]["Chocó"])
    c["narino_ap"] = pc(d["celdas"][("Nariño", "Agricultura permanente")], d["tot_fila"]["Nariño"])
    c["valle_silv"] = pc(d["celdas"][("Valle del Cauca", "Silvicultura")], d["tot_fila"]["Valle del Cauca"])
    # incendios en Chocó 2016
    inc = consultar("area", "departamento", "anio", {"region": ["Pacífica"], "causa": ["Incendios forestales"]})
    inc_total_pais = escalar("area", {"causa": ["Incendios forestales"]})[0]
    c["inc_pais"] = f0(inc_total_pais)
    c["inc_pais_pct"] = pc(inc_total_pais, total, 2)
    c["inc_choco"] = f0(inc["tot_fila"]["Chocó"])
    c["inc_choco_2016"] = f0(inc["celdas"][("Chocó", "2016")])
    c["inc_choco_2019"] = f0(inc["celdas"][("Chocó", "2019")])
    c["inc_choco_2016_pct_pais"] = pc(inc["celdas"][("Chocó", "2016")], inc_total_pais)
    c["inc_choco_2016_pct_choco"] = pc(inc["celdas"][("Chocó", "2016")], d["tot_fila"]["Chocó"])
    gp = consultar("area", "region", "grupo", {"periodo": [P1]})
    gq = consultar("area", "region", "grupo", {"periodo": [P2]})
    c["nat_pac_p1"] = pc(gp["celdas"].get(("Pacífica", "Natural"), 0), gp["tot_fila"]["Pacífica"])
    c["nat_pac_p2"] = pc(gq["celdas"][("Pacífica", "Natural")], gq["tot_fila"]["Pacífica"])
    c["agro_pac_p1"] = pc(gp["celdas"][("Pacífica", "Agropecuaria")], gp["tot_fila"]["Pacífica"])
    c["agro_pac_p2"] = pc(gq["celdas"][("Pacífica", "Agropecuaria")], gq["tot_fila"]["Pacífica"])
    ip2 = consultar("area", "region", "causa", {"region": ["Pacífica"], "periodo": [P2]})
    c["inc_pac_p2"] = f0(ip2["celdas"][("Pacífica", "Incendios forestales")])
    c["inc_choco_2016_pct_pac_p2"] = pc(inc["celdas"][("Chocó", "2016")], ip2["celdas"][("Pacífica", "Incendios forestales")])
    # Etapa 4 (suma cruda de las tres escalas) frente al modelo (una escala)
    c["var_modelo"] = f1((escalar("promedio_anual", {"periodo": [P2]})[0] / escalar("promedio_anual", {"periodo": [P1]})[0] - 1) * 100)
    for esc, clave in (("Nacional", "dep"), ("Global", "pais")):
        a = escalar("promedio_anual", {"periodo": [P1]}, escala=esc)[0]
        b = escalar("promedio_anual", {"periodo": [P2]}, escala=esc)[0]
        c["var_" + clave] = formato((b / a - 1) * 100, decimales=2)
    c["sin_causa_ha"] = f0(escalar("area", {"causa": ["Sin causa informada"]})[0])

    # ---------------- Vista 2: tiempo × territorio ------------------------
    pa = consultar("promedio_anual", "region", "periodo")
    c["nac_p1"] = f0(pa["tot_col"][P1])
    c["nac_p2"] = f0(pa["tot_col"][P2])
    c["nac_var"] = f1((pa["tot_col"][P2] / pa["tot_col"][P1] - 1) * 100)
    neto = pa["tot_col"][P2] - pa["tot_col"][P1]
    c["nac_neto"] = f0(neto)
    for clave, reg in (("amaz", "Amazonía"), ("orin", "Orinoquía"), ("caribe", "Caribe"),
                       ("andina", "Andina"), ("pac", "Pacífica")):
        a, b = pa["celdas"][(reg, P1)], pa["celdas"][(reg, P2)]
        c["r_%s_p1" % clave], c["r_%s_p2" % clave] = f0(a), f0(b)
        c["r_%s_dif" % clave] = f0(abs(b - a))
        c["r_%s_var" % clave] = f1(abs((b / a - 1) * 100))
    c["amaz_aporte"] = pc(pa["celdas"][("Amazonía", P2)] - pa["celdas"][("Amazonía", P1)], neto)
    dp = consultar("promedio_anual", "departamento", "periodo", {"region": ["Amazonía"]})
    for clave, dep in (("caq", "Caquetá"), ("guav", "Guaviare"), ("put", "Putumayo")):
        a, b = dp["celdas"][(dep, P1)], dp["celdas"][(dep, P2)]
        c["d_%s_dif" % clave] = f0(b - a)
        c["d_%s_var" % clave] = f1((b / a - 1) * 100)
    dm = consultar("promedio_anual", "departamento", "periodo", {"region": ["Orinoquía"]})
    c["d_meta_dif"] = f0(dm["celdas"][("Meta", P2)] - dm["celdas"][("Meta", P1)])
    suma4 = ((dp["celdas"][("Caquetá", P2)] - dp["celdas"][("Caquetá", P1)])
             + (dp["celdas"][("Guaviare", P2)] - dp["celdas"][("Guaviare", P1)])
             + (dp["celdas"][("Putumayo", P2)] - dp["celdas"][("Putumayo", P1)])
             + (dm["celdas"][("Meta", P2)] - dm["celdas"][("Meta", P1)]))
    c["cuatro_dep_aporte"] = pc(suma4, neto)
    dd = consultar("promedio_anual", "departamento", "periodo")
    camb = {f: (dd["celdas"].get((f, P2)) or 0) - (dd["celdas"].get((f, P1)) or 0) for f in dd["filas"]}
    sube = sum(v for v in camb.values() if v > 0)
    c["n_dep_suben"], c["n_dep"] = str(sum(1 for v in camb.values() if v > 0)), str(len(camb))
    c["bruto_sube"], c["bruto_baja"] = f0(sube), f0(-sum(v for v in camb.values() if v < 0))
    c["cuatro_pct_bruto"] = pc(suma4, sube)
    tr = consultar("promedio_anual", "region", "trienio")
    tt = tr["tot_col"]
    c["tri_1315"], c["tri_1618"] = f0(tt["2013–2015"]), f0(tt["2016–2018"])
    c["tri_salto"] = formato(tt["2016–2018"] / tt["2013–2015"], decimales=1)
    sal = [tr["celdas"][(r, "2016–2018")] / tr["celdas"][(r, "2013–2015")] for r in ("Amazonía", "Andina", "Caribe", "Orinoquía", "Pacífica")]
    c["sal_min"], c["sal_max"] = formato(min(sal), decimales=1), formato(max(sal), decimales=1)
    for clave, reg in (("amaz", "Amazonía"), ("orin", "Orinoquía"), ("caribe", "Caribe"),
                       ("andina", "Andina"), ("pac", "Pacífica")):
        a, b = tr["celdas"][(reg, "2010–2012")], tr["celdas"][(reg, "2022–2024")]
        c["t_%s_a" % clave], c["t_%s_b" % clave] = f0(a), f0(b)
        c["t_%s_var" % clave] = f1(abs((b / a - 1) * 100))

    # ---------------- Vista 3: causa × transformación × territorio --------
    c["emis_total"] = f0(escalar("emisiones")[0])
    it = consultar("intensidad", "region", "causa")
    c["int_nac"] = f0(it["total"])
    c["int_amaz"] = f0(it["tot_fila"]["Amazonía"])
    c["int_caribe"] = f0(it["tot_fila"]["Caribe"])
    c["int_amaz_vs_caribe"] = f0((it["tot_fila"]["Amazonía"] / it["tot_fila"]["Caribe"] - 1) * 100)
    c["int_ap_amaz"] = f0(it["celdas"][("Amazonía", "Agricultura permanente")])
    c["int_ap_caribe"] = f0(it["celdas"][("Caribe", "Agricultura permanente")])
    c["int_ap_dif"] = f0((it["celdas"][("Amazonía", "Agricultura permanente")] / it["celdas"][("Caribe", "Agricultura permanente")] - 1) * 100)
    c["int_mig_amaz"] = f0(it["celdas"][("Amazonía", "Agricultura migratoria")])
    c["int_mig_vs_ap"] = f0((it["celdas"][("Amazonía", "Agricultura migratoria")] / it["celdas"][("Amazonía", "Agricultura permanente")] - 1) * 100)
    ip = consultar("intensidad", "region", "periodo")
    c["int_p1"], c["int_p2"] = f0(ip["tot_col"][P1]), f0(ip["tot_col"][P2])
    c["int_var"] = f1((ip["tot_col"][P2] / ip["tot_col"][P1] - 1) * 100)
    c["int_caribe_p1"], c["int_caribe_p2"] = f0(ip["celdas"][("Caribe", P1)]), f0(ip["celdas"][("Caribe", P2)])
    c["int_caribe_var"] = f1((ip["celdas"][("Caribe", P2)] / ip["celdas"][("Caribe", P1)] - 1) * 100)
    cl = consultar("area", "region", "clase")
    sc = cl["tot_col"]["Sin clase informada"]
    c["sc_ha"], c["sc_pct"] = f0(sc), pc(sc, cl["total"])
    for clave, reg in (("orin", "Orinoquía"), ("amaz", "Amazonía"), ("andina", "Andina"),
                       ("caribe", "Caribe"), ("pac", "Pacífica")):
        c["sc_" + clave] = pc(cl["celdas"].get((reg, "Sin clase informada"), 0), cl["tot_fila"][reg])
    c["sc_amaz_orin_pct"] = pc(cl["celdas"][("Amazonía", "Sin clase informada")]
                               + cl["celdas"][("Orinoquía", "Sin clase informada")], sc)
    fc = consultar("area", "fuente", "clase")
    sin_mapbiomas = sum(v for (f, k), v in fc["celdas"].items()
                        if k == "Sin clase informada" and "MapBiomas" not in f)
    c["sc_sin_mapbiomas"] = f0(sin_mapbiomas)

    # ---------------- Vista 4: fuente × tiempo × territorio ---------------
    fr = consultar("focos_100ha", "region", None)
    c["f100_nac"] = f1(fr["total"])
    for clave, reg in (("orin", "Orinoquía"), ("caribe", "Caribe"), ("andina", "Andina"),
                       ("pac", "Pacífica"), ("amaz", "Amazonía")):
        c["f100_" + clave] = f1(fr["tot_fila"][reg])
    c["f100_orin_vs_amaz"] = formato(fr["tot_fila"]["Orinoquía"] / fr["tot_fila"]["Amazonía"], decimales=1)
    fd = consultar("focos_100ha", "departamento", None, extra=VENTANA)
    c["f100_vichada"] = f0(fd["tot_fila"]["Vichada"])
    c["f100_putumayo"] = f0(fd["tot_fila"]["Putumayo"])
    fo = consultar("focos", "region", None)
    c["focos_total"] = f0(fo["total"])
    c["focos_orin_caribe_pct"] = pc(fo["tot_fila"]["Orinoquía"] + fo["tot_fila"]["Caribe"], fo["total"])
    ac = consultar("area_con_focos", "region", None, extra=VENTANA)
    ar = consultar("area", "region", None, extra=VENTANA)
    c["cob_firms_nac"] = pc(ac["total"], ar["total"])
    for clave, reg in (("pac", "Pacífica"), ("amaz", "Amazonía"), ("orin", "Orinoquía"),
                       ("caribe", "Caribe"), ("andina", "Andina")):
        c["cob_" + clave] = pc(ac["tot_fila"][reg], ar["tot_fila"][reg])
    c["orin_caribe_area_pct"] = pc(ar["tot_fila"]["Orinoquía"] + ar["tot_fila"]["Caribe"], ar["total"])
    fa = consultar("focos_100ha", "causa", None, extra=VENTANA)
    c["f100_otras"] = f0(fa["tot_fila"]["Otras alteraciones naturales"])
    c["f100_min"] = f0(fa["tot_fila"]["Mineria y otras materias primas"])
    c["f100_ap"] = f1(fa["tot_fila"]["Agricultura permanente"])
    fy = consultar("focos_100ha", "region", "anio", extra=VENTANA)
    c["f100_2013"], c["f100_2017"] = f0(fy["tot_col"]["2013"]), f0(fy["tot_col"]["2017"])
    nf = consultar("area", "n_fuentes", "periodo")
    c["tres_p1"] = pc(nf["celdas"][("3 fuente(s)", P1)], nf["tot_col"][P1])
    c["tres_p2"] = pc(nf["celdas"][("3 fuente(s)", P2)], nf["tot_col"][P2])
    c["tres_ha_p1"], c["tres_ha_p2"] = f0(nf["celdas"][("3 fuente(s)", P1)]), f0(nf["celdas"][("3 fuente(s)", P2)])
    nr = consultar("area", "region", "n_fuentes", extra=VENTANA)
    c["orin_una_fuente"] = pc(nr["celdas"][("Orinoquía", "1 fuente(s)")], nr["tot_fila"]["Orinoquía"])
    c["amaz_tres_fuentes"] = pc(nr["celdas"][("Amazonía", "3 fuente(s)")], nr["tot_fila"]["Amazonía"])
    return c
