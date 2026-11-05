# -*- coding: utf-8 -*-
"""
operaciones.py
==============
Un ejemplo aplicado por cada operación multidimensional (drill-down, roll-up,
slice, dice, pivot). Cada ejemplo se EJECUTA contra el modelo al abrir la
página: las tablas, las cifras de la interpretación y el SQL salen de la
consulta, no están escritos a mano. Cada uno trae un enlace que lo reproduce
en la vista interactiva correspondiente.
"""

from urllib.parse import urlencode

from . import olap
from .olap import consultar, formato

P1, P2 = "2001–2012", "2013–2024"


def _qs(*pares):
    return "?" + urlencode(pares)


def _tabla(cab, filas):
    return dict(cabecera=cab, filas=filas)


def ejemplos():
    out = []

    # ---------------------------------------------------------------- Drill-down
    reg = consultar("area", "region", "causa")
    dep = consultar("area", "departamento", "causa", {"region": ["Pacífica"]})
    ap = "Agricultura permanente"

    def fila(r, f):
        t = r["tot_fila"][f]
        a = r["celdas"].get((f, ap), 0) or 0
        return [f, formato(t), formato(a), formato(a / t * 100, decimales=1) + " %"]
    cab = ["Territorio", "Pérdida total (ha)", "Agricultura permanente (ha)", "% agr. permanente (denominador: total de la fila)"]
    tb1 = _tabla(cab, [fila(reg, f) for f in ("Amazonía", "Andina", "Caribe", "Orinoquía", "Pacífica")])
    tb2 = _tabla(cab, [fila(dep, f) for f in sorted(dep["filas"], key=lambda x: -dep["tot_fila"][x])])
    ch = dep["celdas"][("Chocó", ap)] / dep["tot_fila"]["Chocó"] * 100
    out.append(dict(
        clave="drill-down", nombre="Drill-down", vista="causas-por-territorio",
        definicion="Explorar un resultado desde un nivel general hacia uno más detallado dentro de una jerarquía.",
        dimensiones="Territorio (región → departamento) × Causa (causa dominante). Medida: área perdida (ha).",
        nivel="Territorio: región natural → departamento. Filtro: Región = Pacífica.",
        procedimiento="En la vista 1, con Territorio en «Región natural», se pulsa «Bajar a Departamento» (o se hace clic en la fila «Pacífica»). El motor reagrupa por departamento y recalcula los porcentajes con el total de cada departamento como denominador.",
        tablas=[("Nivel general: región natural", tb1), ("Nivel detallado: departamentos de la región Pacífica", tb2)],
        interpretacion="En el nivel región, la Pacífica tiene la agricultura permanente más baja (%s %%) del país. Al bajar a departamento se ve que el resultado lo produce el Chocó (%s %%), no la región completa: Nariño y Cauca se parecen al resto del país." % (
            formato(reg["celdas"][("Pacífica", ap)] / reg["tot_fila"]["Pacífica"] * 100, decimales=1), formato(ch, decimales=1)),
        sql=dep["sql"], enlace=("causas-por-territorio", _qs(("n_territorio", "departamento"), ("n_causa", "causa"), ("f_region", "Pacífica")))))

    # ---------------------------------------------------------------- Roll-up
    dp = consultar("intensidad", "departamento", None, {"region": ["Amazonía"]})
    rg = consultar("intensidad", "region", None, {"region": ["Amazonía"]})
    ha = consultar("area", "departamento", None, {"region": ["Amazonía"]})
    filas = [[f, formato(ha["tot_fila"][f]), formato(dp["tot_fila"][f])] for f in sorted(dp["filas"], key=lambda x: -ha["tot_fila"][x])]
    simple = sum(dp["tot_fila"][f] for f in dp["filas"] if dp["tot_fila"][f] is not None) / len([f for f in dp["filas"] if dp["tot_fila"][f] is not None])
    filas.append(["Amazonía (roll-up recalculado: ΣMg CO₂e ÷ Σha)", formato(rg["total"] and ha["total"]), formato(rg["total"])])
    filas.append(["Amazonía si se promediaran las intensidades de los departamentos (INCORRECTO)", "—", formato(simple)])
    pa = consultar("promedio_anual", "departamento", "periodo", {"region": ["Amazonía"]})
    pr = consultar("promedio_anual", "region", "periodo", {"region": ["Amazonía"]})
    out.append(dict(
        clave="roll-up", nombre="Roll-up", vista="intensidad-de-emisiones",
        definicion="Agrupar los resultados en un nivel superior de la jerarquía.",
        dimensiones="Territorio (departamento → región natural). Medida: intensidad de emisiones (Mg CO₂e/ha), que es una razón.",
        nivel="Territorio: departamento → región natural. Filtro: Región = Amazonía.",
        procedimiento="En la vista 3, con Territorio en «Departamento», se pulsa «Subir a Región natural». La intensidad NO se obtiene promediando las de los departamentos: se recalcula como SUM(emisiones)/SUM(área) sobre todos los territorios-año del nivel superior. Para una medida aditiva (área, promedio anual como suma entre departamentos) el roll-up coincide con la suma: el promedio anual de la Amazonía en 2013–2024 es %s ha/año y la suma de sus departamentos es %s." % (
            formato(pr["celdas"][("Amazonía", P2)]), formato(sum(pa["celdas"].get((f, P2), 0) or 0 for f in pa["filas"]))),
        tablas=[("Intensidad por departamento y su roll-up a región", _tabla(["Territorio", "Pérdida (ha)", "Intensidad (Mg CO₂e/ha)"], filas))],
        interpretacion="La intensidad de la región (%s) es un cociente de sumas y pondera cada departamento por su área; promediar las intensidades departamentales daría %s, un valor distinto. Por eso el motor recalcula las razones en cada nivel." % (
            formato(rg["total"]), formato(simple)),
        sql=dp["sql"], enlace=("intensidad-de-emisiones", _qs(("n_territorio", "departamento"), ("eje_f", "territorio"), ("eje_c", "causa"), ("medida", "intensidad"), ("f_region", "Amazonía")))))

    # ---------------------------------------------------------------- Slice
    s = consultar("focos_100ha", "departamento", None, {"region": ["Orinoquía"]})
    sf = consultar("focos", "departamento", None, {"region": ["Orinoquía"]})
    sa = consultar("area_con_focos", "departamento", None, {"region": ["Orinoquía"]})
    filas = [[f, formato(sf["tot_fila"][f]), formato(sa["tot_fila"][f]), formato(s["tot_fila"][f], decimales=1)] for f in s["filas"]]
    filas.append(["Orinoquía (total recalculado)", formato(sf["total"]), formato(sa["total"]), formato(s["total"], decimales=1)])
    nac = consultar("focos_100ha", "region", None)
    out.append(dict(
        clave="slice", nombre="Slice", vista="focos-y-fuentes",
        definicion="Seleccionar un valor de una dimensión para estudiar un subconjunto.",
        dimensiones="Territorio (filtro) × Territorio (departamento). Medidas: focos, pérdida con focos registrados, focos por 100 ha.",
        nivel="Filtro sobre UNA dimensión: Región = Orinoquía. Nivel: departamento.",
        procedimiento="En la vista 4 se elige «Orinoquía» en el filtro de región (una sola dimensión filtrada) y se baja a departamento. Todas las medidas se recalculan solo con los territorio-año de la Orinoquía.",
        tablas=[("Focos por 100 ha en los departamentos de la Orinoquía", _tabla(["Departamento", "Focos", "Pérdida con focos registrados (ha)", "Focos por 100 ha"], filas))],
        interpretacion="En el subconjunto de la Orinoquía la razón es %s focos por 100 ha, frente a %s en todo el país. Dentro del corte la razón va de %s (departamento con la razón más baja) a %s (la más alta) focos por 100 ha, una diferencia que el promedio regional oculta." % (
            formato(s["total"], decimales=1), formato(nac["total"], decimales=1),
            formato(min(s["tot_fila"].values()), decimales=1), formato(max(s["tot_fila"].values()), decimales=1)),
        sql=s["sql"], enlace=("focos-y-fuentes", _qs(("n_territorio", "departamento"), ("f_region", "Orinoquía")))))

    # ---------------------------------------------------------------- Dice
    d = consultar("area", "departamento", "anio", {"region": ["Pacífica"], "causa": ["Incendios forestales"]})
    anios = [a for a in d["columnas"] if (d["tot_col"].get(a) or 0) >= 1000]
    filas = [[f] + [formato(d["celdas"].get((f, a))) for a in anios] + [formato(d["tot_fila"][f])] for f in d["filas"]]
    filas.append(["Total"] + [formato(d["tot_col"][a]) for a in anios] + [formato(d["total"])])
    pais = consultar("area", "causa", None, {"causa": ["Incendios forestales"]})
    out.append(dict(
        clave="dice", nombre="Dice", vista="causas-por-territorio",
        definicion="Seleccionar un subconjunto mediante la combinación de filtros sobre dos o más dimensiones.",
        dimensiones="Territorio × Causa (filtros) × Tiempo (año). Medida: área perdida (ha).",
        nivel="Filtros sobre dos dimensiones: Región = Pacífica (Territorio) y Causa = Incendios forestales (Causa). Nivel: departamento × año.",
        procedimiento="En la vista 1 se combinan el filtro de Región (dimensión Territorio) con el filtro de Causa (dimensión Causa) y se baja Tiempo a «Año». Solo cuentan los territorio-año que cumplen ambas condiciones. Se muestran los años con 1.000 ha o más.",
        tablas=[("Pérdida por incendios forestales en la región Pacífica (ha)", _tabla(["Departamento"] + anios + ["Total 2001–2024"], filas))],
        interpretacion="El dice aísla un subconjunto de %s ha, de las %s ha que dejan los incendios forestales en todo el país. La mayor parte está en el Chocó y en un solo año (2016)." % (
            formato(d["total"]), formato(pais["total"])),
        sql=d["sql"], enlace=("causas-por-territorio", _qs(("n_territorio", "departamento"), ("n_tiempo", "anio"), ("eje_c", "tiempo"), ("f_region", "Pacífica"), ("f_causa", "Incendios forestales")))))

    # ---------------------------------------------------------------- Pivot
    a = consultar("promedio_anual", "region", "periodo")
    b = consultar("promedio_anual", "periodo", "region")
    regs = [r for r in a["filas"] if r not in ("Insular", "Sin región informada")]
    t1 = _tabla(["Región \\ Periodo"] + a["columnas"], [[r] + [formato(a["celdas"].get((r, p))) for p in a["columnas"]] for r in regs])
    t2 = _tabla(["Periodo \\ Región"] + regs, [[p] + [formato(b["celdas"].get((p, r))) for r in regs] for p in b["filas"]])
    out.append(dict(
        clave="pivot", nombre="Pivot", vista="cambio-en-el-tiempo",
        definicion="Cambiar la disposición de las dimensiones en una matriz para observar los resultados desde otra perspectiva.",
        dimensiones="Territorio (región) × Tiempo (periodo). Medida: pérdida promedio anual (ha/año).",
        nivel="Sin filtros. Niveles: región × periodo; con pivot, periodo × región.",
        procedimiento="En la vista 2 se pulsa «Pivotar ejes». Los mismos datos pasan de tener regiones en las filas a tener periodos en las filas; los valores no cambian, cambia qué comparación es más fácil de leer.",
        tablas=[("Antes del pivot: regiones en filas", t1), ("Después del pivot: periodos en filas", t2)],
        interpretacion="Con las regiones en filas se lee el cambio de cada región entre periodos; con los periodos en filas se compara qué regiones pesan más dentro de cada periodo (la Amazonía pasa de %s a %s ha/año y supera a la Andina en 2013–2024)." % (
            formato(a["celdas"][("Amazonía", P1)]), formato(a["celdas"][("Amazonía", P2)])),
        sql=a["sql"], enlace=("cambio-en-el-tiempo", _qs(("pivot", "1")))))
    return out
