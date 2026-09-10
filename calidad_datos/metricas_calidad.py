# -*- coding: utf-8 -*-
"""
metricas_calidad.py
====================
Calcula una metrica verificable para cada una de las seis dimensiones de
calidad evaluadas en la Etapa 2: completitud, exactitud, consistencia,
unicidad, validez y actualidad. Usa como entrada dataset_consolidado.csv
(salida de la Etapa 1) y complementa el perfilamiento de
perfilamiento.py.

El resultado se guarda en calidad_datos/reporte_metricas.json y alimenta
la seccion "Dimensiones y metricas" de la aplicacion Flask.
"""
import json

import pandas as pd

ENTRADA = "dataset_consolidado.csv"
SALIDA = "calidad_datos/reporte_metricas.json"

AGREGADOS_REGIONALES = {
    "Africa", "Americas", "Asia", "Europe", "High-income countries",
    "Land Locked Developing Countries (LLDCs)", "Least Developed Countries (LDCs)",
    "Low-income countries", "Lower-middle-income countries", "North America",
    "Oceania", "Small Island Developing States (SIDS)", "South America",
    "Sub-Saharan Africa", "Upper-middle-income countries", "World",
}


def metrica_completitud(df):
    variables_nucleo = ["id_registro", "nivel_analisis", "fuente_origen", "pais", "anio"]
    nulos_nucleo = int(df[variables_nucleo].isna().sum().sum())
    total_celdas = df.shape[0] * df.shape[1]
    nulos_totales = int(df.isna().sum().sum())
    return {
        "formula": "1 - (nulos / (filas x variables)), calculado sobre el total de celdas y sobre las variables nucleo",
        "completitud_variables_nucleo_pct": round((1 - nulos_nucleo / (len(df) * len(variables_nucleo))) * 100, 2),
        "completitud_global_celdas_pct": round((1 - nulos_totales / total_celdas) * 100, 2),
        "nota": (
            "La completitud global es baja porque incluye variables que solo "
            "aplican a un nivel de analisis o a una ventana temporal por diseño "
            "(num_focos_calor, porcentaje_area_forestal, area_forestal_ha, "
            "deforestacion_anual_ha_owid); la completitud de las variables "
            "nucleo, en cambio, es del 100%."
        ),
    }


def metrica_unicidad(df):
    columnas_sin_id = [c for c in df.columns if c != "id_registro"]
    duplicados = int(df.duplicated(subset=columnas_sin_id).sum())
    return {
        "formula": "1 - (registros_duplicados / total_registros), ignorando el id generado",
        "duplicados": duplicados,
        "porcentaje_duplicados": round(duplicados / len(df) * 100, 2),
        "unicidad_pct": round((1 - duplicados / len(df)) * 100, 2),
    }


def metrica_consistencia(df):
    deptos_no_nulos = df["departamento"].dropna()
    variantes_depto = int(
        deptos_no_nulos.apply(
            lambda s: s.isupper() or s in ("Bogotá, D.C.", "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA")
        ).sum()
    )
    municipios_no_nulos = df["municipio"].dropna()
    variantes_municipio = int(municipios_no_nulos.apply(lambda s: s.isupper()).sum())

    clase_no_nula = df["clase_transformacion_dominante"].dropna()
    con_prefijo_numerico = int(clase_no_nula.str.match(r"^\d+\.").sum())

    driver_no_nulo = df["driver_dominante"].dropna()
    categorias_espanol_documentadas = {"Agricultura", "Incendios", "Silvicultura", "Urbanización", "Minería"}
    en_ingles = int((~driver_no_nulo.isin(categorias_espanol_documentadas)).sum())

    return {
        "formula": "1 - (valores_con_formato_no_homologado / valores_no_nulos), por variable categorica",
        "departamento": {
            "valores_no_nulos": int(len(deptos_no_nulos)),
            "con_variante_de_formato": variantes_depto,
            "consistencia_pct": round((1 - variantes_depto / len(deptos_no_nulos)) * 100, 2),
        },
        "municipio": {
            "valores_no_nulos": int(len(municipios_no_nulos)),
            "con_variante_de_formato": variantes_municipio,
            "consistencia_pct": round((1 - variantes_municipio / len(municipios_no_nulos)) * 100, 2),
        },
        "clase_transformacion_dominante": {
            "valores_no_nulos": int(len(clase_no_nula)),
            "con_prefijo_numerico_de_leyenda": con_prefijo_numerico,
            "consistencia_pct": round((1 - con_prefijo_numerico / len(clase_no_nula)) * 100, 2),
        },
        "driver_dominante_vs_diccionario_de_datos": {
            "valores_no_nulos": int(len(driver_no_nulo)),
            "en_ingles_no_coincide_con_diccionario": en_ingles,
            "consistencia_pct": round((1 - en_ingles / len(driver_no_nulo)) * 100, 2),
        },
    }


def metrica_validez(df):
    agregados = int(df["pais"].isin(AGREGADOS_REGIONALES).sum())
    porcentaje_fuera_rango = int(
        ((df["porcentaje_area_forestal"] < 0) | (df["porcentaje_area_forestal"] > 100)).sum()
    )
    confianza_fuera_rango = int(
        ((df["confianza_promedio_focos"] < 0) | (df["confianza_promedio_focos"] > 100)).sum()
    )
    anio_fuera_rango = int(((df["anio"] < 2001) | (df["anio"] > 2024)).sum())
    negativos = int((df[["area_perdida_bosque_ha", "emisiones_co2_mg", "area_transformada_ha"]] < 0).sum().sum())

    violaciones_totales = porcentaje_fuera_rango + confianza_fuera_rango + anio_fuera_rango + negativos
    return {
        "formula": "1 - (registros_fuera_del_dominio_valido / total_registros)",
        "pais_como_agregado_regional_no_pais": {
            "filas_afectadas": agregados,
            "porcentaje": round(agregados / len(df) * 100, 2),
        },
        "violaciones_de_rango_numerico": violaciones_totales,
        "validez_de_rango_pct": round((1 - violaciones_totales / len(df)) * 100, 2),
        "validez_de_pais_pct": round((1 - agregados / len(df)) * 100, 2),
    }


def metrica_exactitud(df):
    ambas = df[df["area_perdida_bosque_ha"].notna() & df["deforestacion_anual_ha_owid"].notna()].copy()
    if len(ambas):
        ambas["diferencia_pct"] = (
            (ambas["area_perdida_bosque_ha"] - ambas["deforestacion_anual_ha_owid"]).abs()
            / ambas["deforestacion_anual_ha_owid"].replace(0, pd.NA)
            * 100
        )
        diferencia_promedio = round(float(ambas["diferencia_pct"].mean()), 2)
        diferencia_min = round(float(ambas["diferencia_pct"].min()), 2)
        diferencia_max = round(float(ambas["diferencia_pct"].max()), 2)
    else:
        diferencia_promedio = diferencia_min = diferencia_max = None

    return {
        "formula": (
            "diferencia relativa promedio entre dos fuentes independientes que "
            "miden el mismo fenomeno para la misma unidad geografica-año "
            "(GFW vs. Our World in Data, a nivel pais-año)"
        ),
        "casos_comparables": int(len(ambas)),
        "diferencia_relativa_promedio_pct": diferencia_promedio,
        "diferencia_relativa_minima_pct": diferencia_min,
        "diferencia_relativa_maxima_pct": diferencia_max,
        "interpretacion": (
            "La magnitud de la diferencia confirma, con un caso verificable, la "
            "limitacion metodologica ya documentada en la Etapa 1: GFW y OWID no "
            "son intercambiables porque usan definiciones y algoritmos distintos "
            "de perdida de bosque."
        ),
    }


def metrica_actualidad(df):
    anio_maximo = int(df["anio"].max())
    anio_actual_referencia = 2026
    antiguedad_anios = anio_actual_referencia - anio_maximo
    recientes = int((df["anio"] >= anio_maximo - 4).sum())
    return {
        "formula": "anio_de_referencia - anio_maximo_observado; y proporcion de filas en los ultimos 5 anios de la serie",
        "anio_maximo_observado": anio_maximo,
        "anio_de_referencia_consulta": anio_actual_referencia,
        "antiguedad_del_dato_mas_reciente_anios": antiguedad_anios,
        "filas_en_ultimos_5_anios_de_la_serie": recientes,
        "porcentaje_filas_ultimos_5_anios": round(recientes / len(df) * 100, 2),
    }


def main():
    df = pd.read_csv(ENTRADA)

    reporte = {
        "completitud": metrica_completitud(df),
        "unicidad": metrica_unicidad(df),
        "consistencia": metrica_consistencia(df),
        "validez": metrica_validez(df),
        "exactitud": metrica_exactitud(df),
        "actualidad": metrica_actualidad(df),
    }

    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    print(json.dumps(reporte, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
