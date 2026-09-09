# -*- coding: utf-8 -*-
"""
perfilamiento.py
================
Perfilamiento del dataset consolidado de la Etapa 1 (dataset_consolidado.csv)
como insumo de la Etapa 2 (calidad de datos).

Calcula, para el conjunto de datos completo:
- cantidad de registros y variables, y tipo de dato de cada variable.
- cantidad de valores unicos y de valores nulos por variable.
- registros duplicados (comparando todas las columnas salvo el id
  generado durante la construccion del dataset).
- minimo, maximo y promedio de las variables numericas.
- una primera deteccion de valores atipicos mediante el metodo del
  rango intercuartilico (IQR).

El resultado se guarda en calidad_datos/reporte_perfilamiento.json y es la
base de la seccion "Perfilamiento" de la aplicacion Flask (ver contenido.py,
diccionario CALIDAD2).
"""
import json

import pandas as pd

ENTRADA = "dataset_consolidado.csv"
SALIDA = "calidad_datos/reporte_perfilamiento.json"

COLUMNAS_NUMERICAS = [
    "area_perdida_bosque_ha",
    "emisiones_co2_mg",
    "area_transformada_ha",
    "num_focos_calor",
    "frp_promedio",
    "confianza_promedio_focos",
    "porcentaje_area_forestal",
    "area_forestal_ha",
    "deforestacion_anual_ha_owid",
]


def perfil_columnas(df):
    filas = []
    for columna in df.columns:
        serie = df[columna]
        nulos = int(serie.isna().sum())
        filas.append(
            {
                "variable": columna,
                "tipo_dato": str(serie.dtype),
                "valores_unicos": int(serie.nunique(dropna=True)),
                "valores_nulos": nulos,
                "porcentaje_nulos": round(nulos / len(df) * 100, 2),
            }
        )
    return filas


def estadisticos_numericos(df):
    resultado = []
    for columna in COLUMNAS_NUMERICAS:
        serie = df[columna].dropna()
        resultado.append(
            {
                "variable": columna,
                "minimo": round(float(serie.min()), 2),
                "maximo": round(float(serie.max()), 2),
                "promedio": round(float(serie.mean()), 2),
                "n": int(serie.shape[0]),
            }
        )
    return resultado


def atipicos_iqr(df):
    resultado = []
    for columna in COLUMNAS_NUMERICAS:
        serie = df[columna].dropna()
        if serie.empty:
            continue
        q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
        iqr = q3 - q1
        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr
        atipicos = ((serie < limite_inferior) | (serie > limite_superior)).sum()
        resultado.append(
            {
                "variable": columna,
                "limite_inferior": round(float(limite_inferior), 2),
                "limite_superior": round(float(limite_superior), 2),
                "atipicos": int(atipicos),
                "porcentaje_atipicos": round(float(atipicos / serie.shape[0] * 100), 2),
            }
        )
    return resultado


def main():
    df = pd.read_csv(ENTRADA)

    duplicados_totales = int(df.duplicated().sum())
    columnas_sin_id = [c for c in df.columns if c != "id_registro"]
    duplicados_sin_id = int(df.duplicated(subset=columnas_sin_id).sum())

    reporte = {
        "registros": int(len(df)),
        "variables": int(df.shape[1]),
        "columnas": perfil_columnas(df),
        "duplicados_incluyendo_id": duplicados_totales,
        "duplicados_ignorando_id_generado": duplicados_sin_id,
        "estadisticos_numericos": estadisticos_numericos(df),
        "atipicos_iqr": atipicos_iqr(df),
    }

    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    print(json.dumps(reporte, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
