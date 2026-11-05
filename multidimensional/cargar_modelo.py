# -*- coding: utf-8 -*-
"""
cargar_modelo.py
================
Procedimiento reproducible de transformación y carga (ETL) de la Etapa 5.

Lee el dataset tratado (deforestacion_limpio.csv, salida del tratamiento de
las etapas anteriores) y construye el modelo estrella en una base SQLite
(multidimensional/modelo_estrella.db):

    dim_territorio, dim_tiempo, dim_causa, dim_transformacion, dim_fuente
    hechos_perdida_forestal   (una fila por territorio y año)

Solo usa la biblioteca estándar de Python (csv, sqlite3, hashlib): no hace
falta instalar nada adicional para reconstruir el modelo.

Uso (desde la raíz del repositorio):

    python multidimensional/cargar_modelo.py
    python multidimensional/cargar_modelo.py --csv otra_ruta.csv --db otra.db

La carga es idempotente: borra y recrea la base completa en cada ejecución.
"""

import argparse
import datetime
import csv
import hashlib
import os
import sqlite3
import sys
from collections import OrderedDict

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CSV_POR_DEFECTO = os.path.join(RAIZ, "deforestacion_limpio.csv")
DB_POR_DEFECTO = os.path.join(AQUI, "modelo_estrella.db")
DDL = os.path.join(RAIZ, "sql", "05_modelo_estrella_ddl.sql")

# ---------------------------------------------------------------------------
# Reglas de transformación (se documentan en docs/modelo_estrella/)
# ---------------------------------------------------------------------------

# Región natural a la que se asigna cada departamento (agrupación habitual
# del IGAC; los límites naturales no coinciden exactamente con los límites
# departamentales, por eso es una convención analítica y se declara así).
REGION_NATURAL = {
    "Amazonía": ["Amazonas", "Caquetá", "Guainía", "Guaviare", "Putumayo", "Vaupés"],
    "Andina": ["Antioquia", "Boyacá", "Caldas", "Cundinamarca", "Bogotá D.C.", "Huila",
               "Norte de Santander", "Quindío", "Risaralda", "Santander", "Tolima"],
    "Caribe": ["Atlántico", "Bolívar", "Cesar", "Córdoba", "La Guajira", "Magdalena", "Sucre"],
    "Orinoquía": ["Arauca", "Casanare", "Meta", "Vichada"],
    "Pacífica": ["Chocó", "Valle del Cauca", "Cauca", "Nariño"],
    "Insular": ["San Andrés y Providencia"],
}
DEPTO_A_REGION = {d: r for r, ds in REGION_NATURAL.items() for d in ds}

# Agrupación de las causas (driver_dominante) en cuatro grupos.
GRUPO_CAUSA = {
    "Agricultura permanente": "Agropecuaria",
    "Agricultura migratoria": "Agropecuaria",
    "Silvicultura": "Forestal (plantaciones)",
    "Incendios forestales": "Natural",
    "Otras alteraciones naturales": "Natural",
    "Urbanizacion e infraestructura": "Infraestructura y minería",
    "Mineria y otras materias primas": "Infraestructura y minería",
}
# Escala de cada nivel de análisis de la fuente.
ESCALA = {"Regional": "Municipal", "Nacional": "Departamental", "Global": "País"}

NO_APLICA = "No aplica"
SIN_CAUSA = "Sin causa informada"
SIN_CLASE = "Sin clase informada"
SIN_DEPTO = "Sin departamento informado"
SIN_MUNICIPIO = "Sin municipio informado"
TOTAL_DEPTO = "(total del departamento)"
SIN_REGION = "Sin región informada"

PERIODOS = (("2001–2012", 2001, 2012), ("2013–2024", 2013, 2024))
FUENTES_SIMPLES = ("GFW", "MapBiomas", "FIRMS", "FAO_SDG", "OWID")

MEDIDAS_NUM = ("area_perdida_bosque_ha", "emisiones_co2_mg", "area_transformada_ha",
               "num_focos_calor", "frp_promedio", "confianza_promedio_focos",
               "porcentaje_area_forestal", "area_forestal_ha", "deforestacion_anual_ha_owid")


def num(valor):
    valor = (valor or "").strip()
    return float(valor) if valor != "" else None


def texto(valor):
    valor = " ".join((valor or "").split())  # normaliza espacios repetidos
    return valor if valor else None


def booleano(valor):
    return 1 if (valor or "").strip().lower() == "true" else 0


def primero(valores):
    for v in valores:
        if v is not None:
            return v
    return None


def promedio(valores):
    vs = [v for v in valores if v is not None]
    return sum(vs) / len(vs) if vs else None


def leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for fila in filas:
        fila["id_registro"] = int(fila["id_registro"])
        fila["anio"] = int(fila["anio"])
    filas.sort(key=lambda r: r["id_registro"])
    return filas


def clave_territorio(f):
    """Clave natural del territorio según el nivel de análisis de la fila."""
    nivel = f["nivel_analisis"]
    pais = texto(f["pais"])
    depto = texto(f["departamento"])
    muni = texto(f["municipio"])
    if nivel == "Regional":
        return (nivel, pais, depto or SIN_DEPTO, muni or SIN_MUNICIPIO)
    if nivel == "Nacional":
        return (nivel, pais, depto or SIN_DEPTO, TOTAL_DEPTO)
    return (nivel, pais, NO_APLICA, NO_APLICA)


def clave_fuente(valor):
    partes = [p for p in (valor or "").split("+") if p]
    return "+".join(partes)


MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
         "Octubre", "Noviembre", "Diciembre"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
# Periodo de pandemia de COVID-19 según la OMS: declaración (11-mar-2020) y fin de la
# emergencia de salud pública internacional (5-may-2023). Es una bandera de contexto.
PANDEMIA = (datetime.date(2020, 3, 11), datetime.date(2023, 5, 5))


def calendario(anio_ini, anio_fin):
    """Filas de dim_tiempo: un día por fila desde el 1-ene de anio_ini hasta el 31-dic de anio_fin."""
    filas, dia = [], datetime.date(anio_ini, 1, 1)
    fin = datetime.date(anio_fin, 12, 31)
    while dia <= fin:
        a, m = dia.year, dia.month
        per = next(p for p in PERIODOS if p[1] <= a <= p[2])
        ini = per[1] + ((a - per[1]) // 3) * 3
        sem = dia.isocalendar()[1]
        en_pand = int(PANDEMIA[0] <= dia <= PANDEMIA[1])
        anio_pand = int(PANDEMIA[0].year <= a <= PANDEMIA[1].year)
        filas.append((
            a * 10000 + m * 100 + dia.day, dia.isoformat(), a, "FY%d" % a,
            "Semestre %d" % ((m - 1) // 6 + 1), "Cuatrimestre %d" % ((m - 1) // 4 + 1),
            "Trimestre %d" % ((m - 1) // 3 + 1), "Bimestre %d" % ((m - 1) // 2 + 1),
            m, MESES[m - 1], MESES[m - 1][:3], sem, "Semana %d" % sem,
            dia.day, dia.timetuple().tm_yday, dia.isoweekday(), DIAS[dia.weekday()], DIAS[dia.weekday()][:3],
            None, en_pand, anio_pand,
            "%d–%d" % (ini, ini + 2), (ini - 2001) // 3 + 1, per[0], PERIODOS.index(per) + 1))
        dia += datetime.timedelta(days=1)
    return filas


def construir(ruta_csv, ruta_db):
    filas = leer_csv(ruta_csv)
    sha = hashlib.sha256(open(ruta_csv, "rb").read()).hexdigest()

    # --- 1. Agrupar las filas de origen por clave natural del hecho --------
    grupos = OrderedDict()
    for f in filas:
        grupos.setdefault((clave_territorio(f), f["anio"]), []).append(f)

    # --- 2. Dimensiones -----------------------------------------------------
    territorios = OrderedDict()   # clave natural -> (key, atributos)
    causas = OrderedDict()
    clases = OrderedDict()
    fuentes = OrderedDict()

    def llave(dic, clave, atributos):
        if clave not in dic:
            dic[clave] = (len(dic) + 1, atributos)
        return dic[clave][0]

    hechos = []
    for (terr, anio), copias in grupos.items():
        nivel, pais, depto, muni = terr
        f0 = copias[0]
        region = (NO_APLICA if nivel == "Global"
                  else DEPTO_A_REGION.get(depto, SIN_REGION))
        lat = primero(num(c["latitud"]) for c in copias)
        lon = primero(num(c["longitud"]) for c in copias)
        es_agr = max(booleano(c["es_agregado_regional"]) for c in copias)
        tk = llave(territorios, terr, dict(
            nivel_analisis=nivel, escala=ESCALA[nivel], pais=pais,
            region_natural=region, departamento=depto, municipio=muni,
            es_agregado_regional=es_agr, latitud=lat, longitud=lon))

        driver = primero(texto(c["driver_dominante"]) for c in copias)
        tiene_perdida = any(num(c["area_perdida_bosque_ha"]) is not None for c in copias)
        if driver:
            clave = driver
            attrs = dict(driver_dominante=driver, grupo_causa=GRUPO_CAUSA.get(driver, "Otra"),
                         tipo_valor="Informada")
        elif nivel == "Global" and pais != "Colombia":
            clave = NO_APLICA
            attrs = dict(driver_dominante=NO_APLICA, grupo_causa=NO_APLICA, tipo_valor="No aplica")
        else:
            clave = SIN_CAUSA
            attrs = dict(driver_dominante=SIN_CAUSA, grupo_causa=SIN_CAUSA, tipo_valor="Sin informar")
        ck = llave(causas, clave, attrs)

        clase = primero(texto(c["clase_transformacion_dominante"]) for c in copias)
        if clase:
            tr_clave, tr_attrs = clase, dict(clase_transformacion=clase, tipo_valor="Informada")
        elif nivel == "Global" and pais != "Colombia":
            tr_clave, tr_attrs = NO_APLICA, dict(clase_transformacion=NO_APLICA, tipo_valor="No aplica")
        else:
            tr_clave, tr_attrs = SIN_CLASE, dict(clase_transformacion=SIN_CLASE, tipo_valor="Sin informar")
        trk = llave(clases, tr_clave, tr_attrs)

        fuente = clave_fuente(primero(texto(c["fuente_origen"]) for c in copias))
        comp = set(fuente.replace("FAO_SDG", "FAO").split("+"))
        fk = llave(fuentes, fuente, dict(
            fuente_origen=fuente, n_fuentes=len(fuente.split("+")),
            incluye_gfw=int("GFW" in comp), incluye_mapbiomas=int("MapBiomas" in comp),
            incluye_firms=int("FIRMS" in comp), incluye_fao=int("FAO" in comp),
            incluye_owid=int("OWID" in comp)))

        h = dict(territorio_key=tk, anio=anio, tiempo_key=anio * 10000 + 101, causa_key=ck, transformacion_key=trk,
                 fuente_key=fk, n_registros_origen=len(copias),
                 id_registro_min=min(c["id_registro"] for c in copias))
        # Regla de colapso: el área y las demás medidas comparten valor entre
        # las copias (primer valor no nulo); las emisiones difieren
        # levemente entre copias y se promedian.
        for m in MEDIDAS_NUM:
            vals = [num(c[m]) for c in copias]
            h[m] = promedio(vals) if m == "emisiones_co2_mg" else primero(vals)
        h["area_perdida_atipica"] = max(booleano(c["area_perdida_bosque_ha_atipico"]) for c in copias)
        h["emisiones_atipicas"] = max(booleano(c["emisiones_co2_mg_atipico"]) for c in copias)
        hechos.append(h)

    # --- 3. Crear base y cargar --------------------------------------------
    if os.path.exists(ruta_db):
        os.remove(ruta_db)
    con = sqlite3.connect(ruta_db)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(open(DDL, encoding="utf-8").read())

    con.executemany(
        "INSERT INTO dim_territorio VALUES (?,?,?,?,?,?,?,?,?,?)",
        [(k, a["nivel_analisis"], a["escala"], a["pais"], a["region_natural"], a["departamento"],
          a["municipio"], a["es_agregado_regional"], a["latitud"], a["longitud"])
         for k, a in territorios.values()])

    anios = sorted({h["anio"] for h in hechos})
    con.executemany("INSERT INTO dim_tiempo VALUES (%s)" % ",".join("?" * 25),
                    calendario(min(anios), max(anios)))

    con.executemany(
        "INSERT INTO dim_causa VALUES (?,?,?,?)",
        [(k, a["driver_dominante"], a["grupo_causa"], a["tipo_valor"]) for k, a in causas.values()])
    con.executemany(
        "INSERT INTO dim_transformacion VALUES (?,?,?)",
        [(k, a["clase_transformacion"], a["tipo_valor"]) for k, a in clases.values()])
    con.executemany(
        "INSERT INTO dim_fuente VALUES (?,?,?,?,?,?,?,?)",
        [(k, a["fuente_origen"], a["n_fuentes"], a["incluye_gfw"], a["incluye_mapbiomas"],
          a["incluye_firms"], a["incluye_fao"], a["incluye_owid"]) for k, a in fuentes.values()])

    cols = ["territorio_key", "tiempo_key", "causa_key", "transformacion_key", "fuente_key",
            "n_registros_origen", "id_registro_min", *MEDIDAS_NUM,
            "area_perdida_atipica", "emisiones_atipicas"]
    con.executemany(
        "INSERT INTO hechos_perdida_forestal (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))),
        [tuple(h[c] for c in cols) for h in hechos])

    con.execute("INSERT INTO meta_carga VALUES (?,?,?,?)",
                (os.path.basename(ruta_csv), sha, len(filas), len(hechos)))
    con.commit()
    resumen = OrderedDict()
    for t in ("dim_territorio", "dim_tiempo", "dim_causa", "dim_transformacion", "dim_fuente",
              "hechos_perdida_forestal"):
        resumen[t] = con.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
    con.close()
    return len(filas), resumen


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--csv", default=CSV_POR_DEFECTO)
    ap.add_argument("--db", default=DB_POR_DEFECTO)
    args = ap.parse_args()
    if not os.path.exists(args.csv):
        sys.exit("No se encontró %s. Copia deforestacion_limpio.csv a la raíz del repositorio." % args.csv)
    n, resumen = construir(args.csv, args.db)
    print("Registros leídos del dataset tratado: %d" % n)
    for t, c in resumen.items():
        print("  %-26s %7d filas" % (t, c))
    print("Base creada en", args.db)


if __name__ == "__main__":
    main()
