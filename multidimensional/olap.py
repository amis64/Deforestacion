# -*- coding: utf-8 -*-
"""
olap.py
=======
Motor de consultas multidimensionales de la Etapa 5.

Toda cifra que muestra la aplicación sale de una consulta SQL sobre el modelo
estrella (vista vw_cubo = hechos + 5 dimensiones). Este módulo traduce una
"selección" (nivel de cada jerarquía, filtros, ejes de la matriz) en SQL con
parámetros ligados y devuelve la matriz con sus totales RECALCULADOS en cada
nivel (los porcentajes y razones nunca se obtienen sumando celdas).

Operaciones que soporta:
  * drill-down / roll-up : cambiar el nivel de una jerarquía (parámetro nivel)
                           o entrar a un miembro (filtro + nivel inferior).
  * slice                : filtro con un valor sobre UNA dimensión.
  * dice                 : filtros combinados sobre DOS o más dimensiones.
  * pivot                : intercambiar los ejes de la matriz.
"""

import os
import sqlite3
from collections import OrderedDict

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(AQUI, "modelo_estrella.db")

# Escala analítica por defecto: Colombia, municipal (nivel "Regional" de la
# fuente). Las otras dos escalas contienen la MISMA pérdida ya agregada
# (departamento y país), por eso nunca se mezclan en una misma consulta.
ESCALA_BASE = "Regional"

# ---------------------------------------------------------------------------
# Dimensiones, jerarquías y niveles  ->  expresión SQL sobre vw_cubo
# ---------------------------------------------------------------------------
DIMENSIONES = OrderedDict([
    ("territorio", dict(nombre="Territorio", niveles=OrderedDict([
        ("region", ("Región natural", "region_natural")),
        ("departamento", ("Departamento", "departamento")),
        ("municipio", ("Municipio", "municipio || ' (' || departamento || ')'")),
    ]))),
    ("tiempo", dict(nombre="Tiempo", niveles=OrderedDict([
        ("periodo", ("Periodo (12 años)", "periodo")),
        ("trienio", ("Trienio", "trienio")),
        ("anio", ("Año", "CAST(anio AS TEXT)")),
    ]))),
    ("causa", dict(nombre="Causa", niveles=OrderedDict([
        ("grupo", ("Grupo de causa", "grupo_causa")),
        ("causa", ("Causa (driver dominante)", "driver_dominante")),
    ]))),
    ("transformacion", dict(nombre="Transformación del suelo", niveles=OrderedDict([
        ("clase", ("Clase de transformación", "clase_transformacion")),
    ]))),
    ("fuente", dict(nombre="Fuente", niveles=OrderedDict([
        ("n_fuentes", ("Número de fuentes", "CAST(n_fuentes AS TEXT) || ' fuente(s)'")),
        ("fuente", ("Combinación de fuentes", "fuente_origen")),
    ]))),
])

# Orden de presentación de los miembros que tienen un orden natural.
ORDEN_FIJO = {
    "region": ["Amazonía", "Andina", "Caribe", "Orinoquía", "Pacífica", "Insular", "Sin región informada"],
    "periodo": ["2001–2012", "2013–2024"],
    "clase": ["Área agropecuaria", "Área sin vegetación", "Sin clase informada", "No aplica"],
    "grupo": ["Agropecuaria", "Forestal (plantaciones)", "Natural", "Infraestructura y minería",
              "Sin causa informada", "No aplica"],
}

# ---------------------------------------------------------------------------
# Medidas: definición única (se reutiliza en la documentación de la página)
# ---------------------------------------------------------------------------
MEDIDAS = OrderedDict([
    ("area", dict(
        nombre="Área perdida de bosque", unidad="ha", decimales=0,
        sql="SUM(area_perdida_bosque_ha)", agregacion="SUM",
        formula="SUM(area_perdida_bosque_ha)",
        suma="Aditiva: se suma entre territorios y entre años (dentro de una misma escala).")),
    ("emisiones", dict(
        nombre="Emisiones de CO₂e", unidad="Mg CO₂e", decimales=0,
        sql="SUM(emisiones_co2_mg)", agregacion="SUM",
        formula="SUM(emisiones_co2_mg)",
        suma="Aditiva. Si un municipio-año tenía copias, se usó el promedio de ellas.")),
    ("intensidad", dict(
        nombre="Intensidad de emisiones", unidad="Mg CO₂e/ha", decimales=0,
        sql="SUM(CASE WHEN area_perdida_bosque_ha > 0 THEN emisiones_co2_mg END) * 1.0 / "
            "NULLIF(SUM(CASE WHEN area_perdida_bosque_ha > 0 THEN area_perdida_bosque_ha END), 0)",
        agregacion="RAZÓN",
        formula="SUM(emisiones_co2_mg | área > 0) / SUM(area_perdida_bosque_ha | área > 0)",
        suma="NO aditiva: es una razón; se recalcula como cociente de sumas en cada nivel. Solo usa filas con "
             "área > 0 porque el área está redondeada a hectárea entera (las filas con 0 ha tienen emisiones "
             "pequeñas por pérdidas menores a 1 ha y distorsionarían el cociente).")),
    ("promedio_anual", dict(
        nombre="Pérdida promedio anual", unidad="ha/año", decimales=0,
        sql="SUM(area_perdida_bosque_ha) * 1.0 / NULLIF(COUNT(DISTINCT anio), 0)", agregacion="PROMEDIO",
        formula="SUM(area_perdida_bosque_ha) / COUNT(DISTINCT anio)",
        suma="NO se suma entre periodos: se divide entre los años presentes en cada grupo, para comparar "
             "periodos de igual duración (12 años).")),
    ("focos", dict(
        nombre="Focos de calor", unidad="focos", decimales=0,
        sql="SUM(num_focos_calor)", agregacion="SUM", formula="SUM(num_focos_calor)",
        suma="Aditiva, pero solo existe donde la fuente FIRMS aporta datos (2012–2022).")),
    ("focos_100ha", dict(
        nombre="Focos por 100 ha perdidas", unidad="focos/100 ha", decimales=1,
        sql="SUM(num_focos_calor) * 100.0 / NULLIF(SUM(CASE WHEN num_focos_calor IS NOT NULL THEN area_perdida_bosque_ha END), 0)",
        agregacion="RAZÓN", formula="100 · SUM(num_focos_calor) / SUM(area_perdida_bosque_ha | con focos registrados)",
        suma="NO aditiva: razón; el denominador solo incluye la pérdida de los territorio-año que tienen focos registrados.")),
    ("territorios", dict(
        nombre="Territorios con pérdida", unidad="territorios", decimales=0,
        sql="COUNT(DISTINCT CASE WHEN area_perdida_bosque_ha > 0 THEN territorio_key END)",
        agregacion="CONTEO DISTINTO", formula="COUNT(DISTINCT territorio_key | área > 0)",
        suma="NO aditiva: cuenta entidades únicas; un mismo municipio aparece en varios años y no debe contarse varias veces.")),
    ("registros", dict(
        nombre="Registros de origen", unidad="registros", decimales=0,
        sql="SUM(n_registros_origen)", agregacion="SUM", formula="SUM(n_registros_origen)",
        suma="Aditiva: reconstruye el conteo de filas del dataset tratado (no es conteo de territorios).")),
    ("hechos", dict(
        nombre="Territorio-año", unidad="filas", decimales=0,
        sql="COUNT(*)", agregacion="CONTEO", formula="COUNT(*)",
        suma="Conteo de filas de la tabla de hechos (una por territorio y año).")),
    ("area_con_focos", dict(
        nombre="Pérdida en territorio-año con focos registrados", unidad="ha", decimales=0,
        sql="SUM(CASE WHEN num_focos_calor IS NOT NULL THEN area_perdida_bosque_ha END)", agregacion="SUM",
        formula="SUM(area_perdida_bosque_ha | num_focos_calor no nulo)", suma="Aditiva.")),
    ("area_sin_clase", dict(
        nombre="Pérdida sin clase de transformación informada", unidad="ha", decimales=0,
        sql="SUM(CASE WHEN clase_transformacion = 'Sin clase informada' THEN area_perdida_bosque_ha END)",
        agregacion="SUM", formula="SUM(area_perdida_bosque_ha | clase = 'Sin clase informada')", suma="Aditiva.")),
])


def conectar():
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    con.row_factory = sqlite3.Row
    return con


def expr(nivel):
    """Expresión SQL de un nivel de jerarquía (clave: region, anio, causa, ...)."""
    for d in DIMENSIONES.values():
        if nivel in d["niveles"]:
            return d["niveles"][nivel][1]
    raise KeyError(nivel)


def dimension_de(nivel):
    for k, d in DIMENSIONES.items():
        if nivel in d["niveles"]:
            return k
    raise KeyError(nivel)


def etiqueta(nivel):
    for d in DIMENSIONES.values():
        if nivel in d["niveles"]:
            return d["niveles"][nivel][0]
    raise KeyError(nivel)


def nivel_siguiente(dim, nivel):
    """Nivel inferior (drill-down) o None si ya es el más detallado."""
    claves = list(DIMENSIONES[dim]["niveles"])
    i = claves.index(nivel)
    return claves[i + 1] if i + 1 < len(claves) else None


def nivel_anterior(dim, nivel):
    """Nivel superior (roll-up) o None si ya es el más general."""
    claves = list(DIMENSIONES[dim]["niveles"])
    i = claves.index(nivel)
    return claves[i - 1] if i > 0 else None


def _where(filtros, escala, extra=None):
    cond, par = ["nivel_analisis = ?"], [escala]
    for nivel, valores in (filtros or {}).items():
        if valores:
            cond.append("%s IN (%s)" % (expr(nivel), ",".join("?" * len(valores))))
            par.extend(valores)
    if extra:
        cond.append(extra)
    return " AND ".join(cond), par


def _sql_visible(sql, par):
    """Sustituye los '?' por los valores, SOLO para mostrar la consulta al usuario."""
    partes = sql.split("?")
    out = partes[0]
    for p, resto in zip(par, partes[1:]):
        out += (repr(p) if isinstance(p, str) else str(p)) + resto
    return out


def valores_de(nivel, escala=ESCALA_BASE, filtros=None):
    """Miembros distintos de un nivel (para llenar los filtros), en orden de presentación."""
    con = conectar()
    donde, par = _where(filtros, escala)
    filas = [r[0] for r in con.execute(
        "SELECT DISTINCT %s FROM vw_cubo WHERE %s" % (expr(nivel), donde), par)]
    con.close()
    return _ordenar(nivel, filas)


def _ordenar(nivel, etiquetas, pesos=None):
    if nivel in ORDEN_FIJO:
        fijo = ORDEN_FIJO[nivel]
        return sorted(etiquetas, key=lambda e: (fijo.index(e) if e in fijo else 99, str(e)))
    if nivel in ("trienio", "anio"):
        return sorted(etiquetas, key=lambda e: str(e))
    if nivel == "n_fuentes":
        return sorted(etiquetas, key=lambda e: -int(str(e).split()[0]))
    if pesos:
        return sorted(etiquetas, key=lambda e: (-(pesos.get(e) or 0), str(e)))
    return sorted(etiquetas, key=str)


def consultar(medida, filas, columnas=None, filtros=None, escala=ESCALA_BASE, extra=None, top=None):
    """
    Ejecuta una consulta multidimensional.

    medida   : clave de MEDIDAS.
    filas    : nivel (p. ej. 'region') que va en las filas de la matriz.
    columnas : nivel que va en las columnas (None = una sola columna 'Total').
    filtros  : {nivel: [valores]} -> slice (una dimensión) / dice (varias).
    top      : si se indica, conserva solo las N filas con mayor total.

    Devuelve un dict con las etiquetas, las celdas, los totales por fila,
    por columna y general (todos recalculados con la misma medida) y el SQL.
    """
    m = MEDIDAS[medida]["sql"]
    donde, par = _where(filtros, escala, extra)
    con = conectar()
    sql_fc = "SELECT %s AS f, %s AS c, %s AS v FROM vw_cubo WHERE %s GROUP BY 1, 2" % (
        expr(filas), expr(columnas) if columnas else "'Total'", m, donde)
    celdas = {(r["f"], r["c"]): r["v"] for r in con.execute(sql_fc, par)}
    tot_f = {r["f"]: r["v"] for r in con.execute(
        "SELECT %s AS f, %s AS v FROM vw_cubo WHERE %s GROUP BY 1" % (expr(filas), m, donde), par)}
    tot_c = ({r["c"]: r["v"] for r in con.execute(
        "SELECT %s AS c, %s AS v FROM vw_cubo WHERE %s GROUP BY 1" % (expr(columnas), m, donde), par)}
        if columnas else {"Total": None})
    total = con.execute("SELECT %s FROM vw_cubo WHERE %s" % (m, donde), par).fetchone()[0]
    con.close()

    etiquetas_f = _ordenar(filas, list(tot_f), tot_f)
    omitidas = 0
    if top and len(etiquetas_f) > top:
        etiquetas_f = sorted(tot_f, key=lambda e: -(tot_f[e] or 0))[:top]
        omitidas = len(tot_f) - top
    etiquetas_c = _ordenar(columnas, list(tot_c), tot_c) if columnas else ["Total"]
    if not columnas:
        tot_c = {"Total": total}
    return dict(medida=medida, filas=etiquetas_f, columnas=etiquetas_c, celdas=celdas,
                tot_fila=tot_f, tot_col=tot_c, total=total, omitidas=omitidas,
                nivel_filas=filas, nivel_columnas=columnas, filtros=filtros or {}, escala=escala,
                sql=_sql_visible(sql_fc, par))


def escalar(medida, filtros=None, escala=ESCALA_BASE, extra=None):
    """Valor único de una medida bajo una selección (para indicadores)."""
    donde, par = _where(filtros, escala, extra)
    con = conectar()
    sql = "SELECT %s FROM vw_cubo WHERE %s" % (MEDIDAS[medida]["sql"], donde)
    v = con.execute(sql, par).fetchone()[0]
    con.close()
    return v, _sql_visible(sql, par)


def formato(valor, medida=None, decimales=None):
    """Formato numérico con separador de miles '.' y decimal ',' (estilo es-CO)."""
    if valor is None:
        return "—"
    d = MEDIDAS[medida]["decimales"] if (medida and decimales is None) else (decimales or 0)
    s = "{:,.{d}f}".format(valor, d=d)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def tipo_operacion(filtros, niveles_base, niveles_actuales, pivot=False):
    """Describe qué operaciones multidimensionales hay activas (para mostrarlas al usuario)."""
    ops = []
    for dim, nivel in niveles_actuales.items():
        base = niveles_base.get(dim)
        if base and nivel != base:
            claves = list(DIMENSIONES[dim]["niveles"])
            ops.append(("Drill-down" if claves.index(nivel) > claves.index(base) else "Roll-up",
                        "%s: %s → %s" % (DIMENSIONES[dim]["nombre"], etiqueta(base), etiqueta(nivel))))
    dims_filtradas = {}
    for nivel, vals in (filtros or {}).items():
        if vals:
            dims_filtradas.setdefault(dimension_de(nivel), []).append((nivel, vals))
    if len(dims_filtradas) == 1:
        (dim, lst), = dims_filtradas.items()
        ops.append(("Slice", "; ".join("%s = %s" % (etiqueta(n), ", ".join(v)) for n, v in lst)))
    elif len(dims_filtradas) >= 2:
        ops.append(("Dice", " × ".join("%s ∈ {%s}" % (etiqueta(n), ", ".join(v))
                                       for lst in dims_filtradas.values() for n, v in lst)))
    if pivot:
        ops.append(("Pivot", "filas y columnas intercambiadas"))
    return ops
