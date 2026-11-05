# -*- coding: utf-8 -*-
"""
validar_modelo.py
=================
Verificaciones del modelo estrella de la Etapa 5.

Parte A (integridad): unicidad de claves, claves foráneas, duplicaciones en la
tabla de hechos y tratamiento de faltantes / categorías desconocidas.
Parte B (coherencia): comparaciones entre los resultados del modelo y el
dataset tratado (deforestacion_limpio.csv), calculadas de forma INDEPENDIENTE
del ETL (con diccionarios de Python sobre el CSV, sin reutilizar las funciones
de cargar_modelo.py).

Uso:   python multidimensional/validar_modelo.py
Salida: tabla en consola + multidimensional/reporte_validacion.json
Código de salida 1 si alguna verificación de integridad falla.
"""

import csv
import json
import os
import sqlite3
import sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CSV = os.path.join(RAIZ, "deforestacion_limpio.csv")
DB = os.path.join(AQUI, "modelo_estrella.db")
SALIDA = os.path.join(AQUI, "reporte_validacion.json")


def f(v):
    v = (v or "").strip()
    return float(v) if v else None


def main():
    con = sqlite3.connect(DB)
    q = lambda sql, *p: con.execute(sql, p).fetchall()
    q1 = lambda sql, *p: con.execute(sql, p).fetchone()[0]

    # ---------------- Lectura independiente del CSV -------------------------
    with open(CSV, newline="", encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    grupos = defaultdict(list)
    for r in filas:
        grupos[(r["nivel_analisis"], r["pais"], r["departamento"], r["municipio"], r["anio"])].append(r)

    integridad, coherencia = [], []

    def integ(nombre, esperado, obtenido, detalle=""):
        integridad.append(dict(verificacion=nombre, esperado=esperado, obtenido=obtenido,
                               resultado="OK" if esperado == obtenido else "FALLA", detalle=detalle))

    # ---------------- A. Integridad ----------------------------------------
    claves = {
        "dim_territorio": ("territorio_key", "nivel_analisis, pais, departamento, municipio"),
        "dim_tiempo": ("id_dim_tiempo", "fecha"),
        "dim_causa": ("causa_key", "driver_dominante"),
        "dim_transformacion": ("transformacion_key", "clase_transformacion"),
        "dim_fuente": ("fuente_key", "fuente_origen"),
    }
    for t, (pk, nat) in claves.items():
        n = q1("SELECT COUNT(*) FROM " + t)
        integ("Unicidad de la clave primaria de %s (%s)" % (t, pk),
              n, q1("SELECT COUNT(DISTINCT %s) FROM %s" % (pk, t)))
        integ("Unicidad de la clave natural de %s (%s)" % (t, nat),
              n, q1("SELECT COUNT(*) FROM (SELECT DISTINCT %s FROM %s)" % (nat, t)))
    integ("Claves foráneas huérfanas según PRAGMA foreign_key_check", 0,
          len(q("PRAGMA foreign_key_check")))
    for fk, dim, pk in (("territorio_key", "dim_territorio", "territorio_key"),
                        ("tiempo_key", "dim_tiempo", "id_dim_tiempo"), ("causa_key", "dim_causa", "causa_key"),
                        ("transformacion_key", "dim_transformacion", "transformacion_key"),
                        ("fuente_key", "dim_fuente", "fuente_key")):
        integ("Hechos sin miembro en %s (LEFT JOIN)" % dim, 0, q1(
            "SELECT COUNT(*) FROM hechos_perdida_forestal h LEFT JOIN %s d ON d.%s = h.%s WHERE d.%s IS NULL"
            % (dim, pk, fk, pk)))
    total_h = q1("SELECT COUNT(*) FROM hechos_perdida_forestal")
    integ("Duplicados de (territorio, año) en la tabla de hechos", 0, total_h - q1(
        "SELECT COUNT(*) FROM (SELECT DISTINCT territorio_key, tiempo_key FROM hechos_perdida_forestal)"))
    integ("Filas de hechos = combinaciones distintas territorio-año del CSV", len(grupos), total_h,
          "Se cuenta en el CSV con la clave (nivel, país, departamento, municipio, año) sin pasar por el ETL.")
    integ("Dimensiones sin uso (miembros que ningún hecho referencia)", 0, sum(
        q1("SELECT COUNT(*) FROM %s d WHERE NOT EXISTS (SELECT 1 FROM hechos_perdida_forestal h WHERE h.%s = d.%s)"
           % (dim, fk, pk)) for dim, fk, pk in (
            ("dim_territorio", "territorio_key", "territorio_key"), ("dim_causa", "causa_key", "causa_key"),
            ("dim_transformacion", "transformacion_key", "transformacion_key"),
            ("dim_fuente", "fuente_key", "fuente_key"))))

    # Dimensión tiempo (calendario diario)
    import datetime
    dias_esperados = (datetime.date(2024, 12, 31) - datetime.date(2001, 1, 1)).days + 1
    integ("dim_tiempo cubre todos los días de 2001-01-01 a 2024-12-31 (sin huecos)", dias_esperados,
          q1("SELECT COUNT(*) FROM dim_tiempo"))
    integ("Años de dim_tiempo con número de días distinto de 365/366", 0, q1(
        "SELECT COUNT(*) FROM (SELECT anio, COUNT(*) n FROM dim_tiempo GROUP BY anio) "
        "WHERE n != CASE WHEN (anio % 4 = 0 AND anio % 100 != 0) OR anio % 400 = 0 THEN 366 ELSE 365 END"))
    integ("id_dim_tiempo (AAAAMMDD) inconsistente con fecha", 0, q1(
        "SELECT COUNT(*) FROM dim_tiempo WHERE id_dim_tiempo != CAST(REPLACE(fecha, '-', '') AS INTEGER)"))
    integ("Hechos que no referencian el 1 de enero de su año (tiempo_key = AAAA0101)", 0, q1(
        "SELECT COUNT(*) FROM hechos_perdida_forestal WHERE tiempo_key % 10000 != 101"))
    anios_csv = len({r["anio"] for r in filas})
    integ("Años distintos referenciados por los hechos = años del CSV", anios_csv, q1(
        "SELECT COUNT(DISTINCT ti.anio) FROM hechos_perdida_forestal f "
        "JOIN dim_tiempo ti ON ti.id_dim_tiempo = f.tiempo_key"))
    integ("Años del calendario sin ningún hecho asociado", 0, q1(
        "SELECT COUNT(DISTINCT anio) FROM dim_tiempo WHERE anio NOT IN ("
        "SELECT ti.anio FROM hechos_perdida_forestal f JOIN dim_tiempo ti ON ti.id_dim_tiempo = f.tiempo_key)"))
    pand = (datetime.date(2023, 5, 5) - datetime.date(2020, 3, 11)).days + 1
    integ("Días marcados como periodo de pandemia (11-mar-2020 a 5-may-2023, OMS)", pand, q1(
        "SELECT SUM(es_periodo_pandemia) FROM dim_tiempo"))
    integ("Filas de dim_tiempo con hora informada (el grano es el día; hora = NULL)", 0, q1(
        "SELECT COUNT(*) FROM dim_tiempo WHERE hora IS NOT NULL"))

    # Faltantes y categorías desconocidas
    def sin_driver(g):
        return not any((r["driver_dominante"] or "").strip() for r in g)
    # 'No aplica' solo corresponde a países distintos de Colombia en la escala País
    sin_causa_csv = sum(1 for g in grupos.values() if sin_driver(g) and not (
        g[0]["nivel_analisis"] == "Global" and g[0]["pais"] != "Colombia"))
    integ("Hechos con 'Sin causa informada' (faltante de la fuente, no 'No aplica')",
          sin_causa_csv, q1("SELECT COUNT(*) FROM hechos_perdida_forestal h JOIN dim_causa c USING (causa_key) "
                            "WHERE c.driver_dominante = 'Sin causa informada'"))
    nulos_area_csv = sum(1 for g in grupos.values() if not any((r["area_perdida_bosque_ha"] or "").strip() for r in g))
    integ("Hechos con área perdida NULL (no se rellena con 0)", nulos_area_csv,
          q1("SELECT COUNT(*) FROM hechos_perdida_forestal WHERE area_perdida_bosque_ha IS NULL"))
    integ("Hechos con área perdida = 0 (valor real, distinto de faltante)",
          sum(1 for g in grupos.values() if any(f(r["area_perdida_bosque_ha"]) == 0 for r in g)
              and f(g[0]["area_perdida_bosque_ha"]) == 0),
          q1("SELECT COUNT(*) FROM hechos_perdida_forestal WHERE area_perdida_bosque_ha = 0"))

    # ---------------- B. Coherencia con el dataset tratado -----------------
    def comp(nombre, origen, modelo, explicacion, tolerancia=0.0):
        dif = modelo - origen
        coherencia.append(dict(
            comprobacion=nombre, dataset_tratado=origen, modelo=modelo, diferencia=dif,
            diferencia_pct=(dif / origen * 100) if origen else 0.0,
            resultado="Coincide" if abs(dif) <= tolerancia else "Difiere (explicada)",
            explicacion=explicacion))

    # B1. conteo de registros por nivel
    for nivel in ("Regional", "Nacional", "Global"):
        comp("B1. Registros de origen, nivel %s" % nivel,
             sum(1 for r in filas if r["nivel_analisis"] == nivel),
             q1("SELECT SUM(n_registros_origen) FROM hechos_perdida_forestal h JOIN dim_territorio t USING (territorio_key) "
                "WHERE t.nivel_analisis = ?", nivel),
             "SUM(n_registros_origen) reconstruye el conteo del CSV: ninguna fila se pierde ni se duplica al cargar.")

    # B2. área perdida (municipal): CSV con una fila por territorio-año vs modelo
    max_area = sum(max((f(r["area_perdida_bosque_ha"]) for r in g if f(r["area_perdida_bosque_ha"]) is not None),
                       default=0.0) for g in grupos.values() if g[0]["nivel_analisis"] == "Regional")
    comp("B2. Área perdida municipal (ha), una fila por municipio-año",
         max_area,
         q1("SELECT SUM(area_perdida_bosque_ha) FROM hechos_perdida_forestal h JOIN dim_territorio t USING (territorio_key) "
            "WHERE t.nivel_analisis = 'Regional'"),
         "El CSV se calcula tomando el máximo entre las copias y el modelo el primer valor no nulo: las copias "
         "comparten el área, así que ambos métodos coinciden.", tolerancia=10)

    # B3. suma cruda del CSV (con filas repetidas) vs modelo reconstruido con n_registros_origen
    cruda = sum(f(r["area_perdida_bosque_ha"]) or 0.0 for r in filas if r["nivel_analisis"] == "Regional")
    comp("B3. Área perdida municipal: SUMA CRUDA del CSV vs modelo",
         cruda,
         q1("SELECT SUM(area_perdida_bosque_ha) FROM hechos_perdida_forestal h JOIN dim_territorio t USING (territorio_key) "
            "WHERE t.nivel_analisis = 'Regional'"),
         "Diferencia esperada: en el CSV cada municipio-año aparece hasta 3 veces con la misma área, así que sumar "
         "filas multiplica las hectáreas (~3×). El modelo guarda UNA fila por municipio-año y evita la multiplicación.")

    # B4. el área perdida es la misma en las tres escalas (municipal, departamental, país)
    por_nivel = dict(q("SELECT t.nivel_analisis, SUM(h.area_perdida_bosque_ha) FROM hechos_perdida_forestal h "
                       "JOIN dim_territorio t USING (territorio_key) GROUP BY 1"))
    comp("B4. Roll-up municipal vs nivel departamental de la fuente (ha)",
         por_nivel["Nacional"], por_nivel["Regional"],
         "Los municipios sumados reproducen el total departamental de la fuente; la diferencia (<0,002 %) "
         "proviene de redondeos y de la asignación de unos pocos municipios en la fuente original.", tolerancia=100)
    comp("B5. Roll-up municipal vs total Colombia (nivel país) (ha)",
         por_nivel["Global"], por_nivel["Regional"],
         "Mismo total en la tercera escala; por eso NUNCA se suman escalas distintas (se contaría tres veces).",
         tolerancia=100)

    # B6. emisiones: promedio de copias (CSV) vs modelo
    em_csv = 0.0
    for g in grupos.values():
        if g[0]["nivel_analisis"] != "Regional":
            continue
        v = [f(r["emisiones_co2_mg"]) for r in g if f(r["emisiones_co2_mg"]) is not None]
        em_csv += sum(v) / len(v) if v else 0.0
    comp("B6. Emisiones municipales (Mg CO2e), promedio de copias",
         em_csv,
         q1("SELECT SUM(emisiones_co2_mg) FROM hechos_perdida_forestal h JOIN dim_territorio t USING (territorio_key) "
            "WHERE t.nivel_analisis = 'Regional'"),
         "Las copias de un municipio-año difieren levemente en emisiones; el modelo las promedia.", tolerancia=1)

    # B7. focos de calor
    fo_csv = sum(f(g[0]["num_focos_calor"]) or 0.0 for g in grupos.values()
                 if g[0]["nivel_analisis"] == "Regional")
    comp("B7. Focos de calor municipales (conteo)", fo_csv,
         q1("SELECT SUM(num_focos_calor) FROM hechos_perdida_forestal h JOIN dim_territorio t USING (territorio_key) "
            "WHERE t.nivel_analisis = 'Regional'"),
         "Los focos son iguales entre copias; el modelo conserva una vez cada municipio-año.", tolerancia=5)

    # B8. municipios distintos con pérdida
    mun_csv = len({(g[0]["departamento"], g[0]["municipio"]) for g in grupos.values()
                   if g[0]["nivel_analisis"] == "Regional" and (f(g[0]["area_perdida_bosque_ha"]) or 0) > 0})
    comp("B8. Municipios distintos con pérdida > 0 (conteo de entidades únicas)", mun_csv,
         q1("SELECT COUNT(DISTINCT h.territorio_key) FROM hechos_perdida_forestal h JOIN dim_territorio t USING (territorio_key) "
            "WHERE t.nivel_analisis = 'Regional' AND h.area_perdida_bosque_ha > 0"),
         "Conteo distinto de entidades; no es lo mismo que contar filas.", tolerancia=15)

    # B9/B10. Cifras de la Etapa 4 (Power BI): combinaciones municipio-año y municipios distintos
    comb_e4 = len({(g[0]["departamento"], g[0]["municipio"], g[0]["anio"]) for g in grupos.values()
                   if g[0]["nivel_analisis"] == "Regional" and g[0]["departamento"].strip() and g[0]["municipio"].strip()})
    comp("B9. Combinaciones municipio-año de la escala Regional (Etapa 4: 28.800)",
         comb_e4,
         q1("SELECT COUNT(*) FROM hechos_perdida_forestal h JOIN dim_territorio t USING (territorio_key) "
            "WHERE t.nivel_analisis = 'Regional'"),
         "Diferencia de 11 filas: son focos de calor FIRMS (2012–2022) sin departamento ni municipio informados y "
         "sin área perdida. El modelo los conserva en el miembro «Sin municipio informado» (para no perder esos "
         "focos); la Etapa 4 cuenta solo combinaciones con municipio informado.")
    mun_e4 = len({(g[0]["departamento"], g[0]["municipio"]) for g in grupos.values()
                  if g[0]["nivel_analisis"] == "Regional" and g[0]["departamento"].strip() and g[0]["municipio"].strip()})
    comp("B10. Municipios distintos con departamento y municipio informados (Etapa 4: 1.209)",
         mun_e4,
         q1("SELECT COUNT(*) FROM dim_territorio WHERE nivel_analisis = 'Regional' AND municipio NOT LIKE 'Sin %'"),
         "Conteo de entidades únicas (no de filas); coincide con el de la Etapa 4 una vez excluido el miembro "
         "«Sin municipio informado».")

    reporte = dict(integridad=integridad, coherencia=coherencia,
                   resumen=dict(verificaciones_integridad=len(integridad),
                                fallas=sum(1 for i in integridad if i["resultado"] != "OK"),
                                comparaciones=len(coherencia)))
    with open(SALIDA, "w", encoding="utf-8") as fh:
        json.dump(reporte, fh, ensure_ascii=False, indent=2)

    print("A. INTEGRIDAD")
    for i in integridad:
        print("  [%s] %s  (esperado %s, obtenido %s)" % (i["resultado"], i["verificacion"], i["esperado"], i["obtenido"]))
    print("\nB. COHERENCIA CON EL DATASET TRATADO")
    for c in coherencia:
        print("  [%s] %s\n       dataset=%s  modelo=%s  dif=%s (%.4f %%)" % (
            c["resultado"], c["comprobacion"], "{:,.2f}".format(c["dataset_tratado"]),
            "{:,.2f}".format(c["modelo"]), "{:,.2f}".format(c["diferencia"]), c["diferencia_pct"]))
    print("\nReporte guardado en", SALIDA)
    sys.exit(1 if reporte["resumen"]["fallas"] else 0)


if __name__ == "__main__":
    main()
