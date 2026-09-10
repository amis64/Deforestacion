# -*- coding: utf-8 -*-
"""
tratamiento.py
==============
Aplica el plan de tratamiento definido en la Etapa 2 sobre el dataset
consolidado (dataset_consolidado.csv) y genera dataset_tratado.csv junto
con un resumen antes/despues en calidad_datos/reporte_tratamiento.json.

No borra columnas ni filas por sospecha: cada accion corresponde a un
problema documentado en el inventario de la Etapa 2, y las decisiones que
no tienen evidencia suficiente para corregirse de forma segura (por
ejemplo la ambiguedad entre 'cero' y 'sin dato' en area_transformada_ha)
se dejan igual y quedan anotadas como limitacion pendiente.
"""
import json
import unicodedata
import pandas as pd
import numpy as np

ENTRADA = "dataset_consolidado.csv"
SALIDA_DATOS = "dataset_tratado.csv"
SALIDA_REPORTE = "calidad_datos/reporte_tratamiento.json"

AGREGADOS_REGIONALES = {
    "Africa", "Americas", "Asia", "Europe", "High-income countries",
    "Land Locked Developing Countries (LLDCs)", "Least Developed Countries (LDCs)",
    "Low-income countries", "Lower-middle-income countries", "North America",
    "Oceania", "Small Island Developing States (SIDS)", "South America",
    "Sub-Saharan Africa", "Upper-middle-income countries", "World",
}

MAPA_DRIVER = {
    "Permanent agriculture": "Agricultura permanente",
    "Shifting cultivation": "Agricultura migratoria",
    "Logging": "Silvicultura",
    "Other natural disturbances": "Otras alteraciones naturales",
    "Settlements & Infrastructure": "Urbanizacion e infraestructura",
    "Hard commodities": "Mineria y otras materias primas",
    "Wildfire": "Incendios forestales",
}


def normalizar_texto(valor):
    if pd.isna(valor):
        return valor
    texto = valor.strip()
    texto = " ".join(texto.split())
    return texto


def normalizar_departamento(valor):
    if pd.isna(valor):
        return valor
    texto = normalizar_texto(valor)
    equivalencias = {
        "Bogotá, D.C.": "Bogotá D.C.",
        "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA": "San Andrés y Providencia",
    }
    if texto in equivalencias:
        return equivalencias[texto]
    if texto.isupper():
        return texto.title().replace(" De ", " de ").replace(" Del ", " del ").replace(" Y ", " y ")
    return texto


def normalizar_municipio(valor):
    if pd.isna(valor):
        return valor
    texto = normalizar_texto(valor)
    if texto.isupper():
        texto = texto.title().replace(" De ", " de ").replace(" Del ", " del ").replace(" Y ", " y ")
    return texto


def normalizar_clase_transformacion(valor):
    if pd.isna(valor):
        return valor
    texto = normalizar_texto(valor)
    # quita el prefijo numerico heredado de la leyenda de MapBiomas (ej. "3. ")
    partes = texto.split(".", 1)
    if len(partes) == 2 and partes[0].strip().isdigit():
        texto = partes[1].strip()
    return texto


def clave_sin_id(df, columnas):
    return columnas


def perfil_basico(df):
    return {
        "filas": int(len(df)),
        "columnas": int(df.shape[1]),
        "duplicados_exactos_sin_id": int(df.drop(columns=["id_registro"]).duplicated().sum()),
        "variantes_departamento": int(df["departamento"].nunique(dropna=True)),
        "variantes_municipio_mayus": int(df["municipio"].dropna().apply(lambda s: isinstance(s, str) and s.isupper()).sum()),
        "filas_pais_agregado_regional": int(df["pais"].isin(AGREGADOS_REGIONALES).sum()),
        "categorias_driver_dominante": sorted([v for v in df["driver_dominante"].dropna().unique().tolist()]),
        "categorias_clase_transformacion": sorted([v for v in df["clase_transformacion_dominante"].dropna().unique().tolist()]),
    }


def main():
    df = pd.read_csv(ENTRADA)
    antes = perfil_basico(df)

    tratado = df.copy()

    # 1) Eliminacion de duplicados exactos (ignorando el id generado)
    columnas_sin_id = [c for c in tratado.columns if c != "id_registro"]
    tratado = tratado.drop_duplicates(subset=columnas_sin_id, keep="first").reset_index(drop=True)
    tratado["id_registro"] = range(1, len(tratado) + 1)

    # 2) Homologacion de nombres de lugar (departamento y municipio)
    tratado["departamento"] = tratado["departamento"].map(normalizar_departamento)
    tratado["municipio"] = tratado["municipio"].map(normalizar_municipio)

    # 3) Correccion de formato en clase_transformacion_dominante
    tratado["clase_transformacion_dominante"] = tratado["clase_transformacion_dominante"].map(
        normalizar_clase_transformacion
    )

    # 4) Homologacion de driver_dominante a las categorias en espanol documentadas
    #    en el diccionario de datos de la Etapa 1 (estaban en ingles en la fuente).
    tratado["driver_dominante"] = tratado["driver_dominante"].map(
        lambda v: MAPA_DRIVER.get(v, v) if pd.notna(v) else v
    )

    # 5) Marcado (no eliminacion) de agregados regionales dentro de "pais",
    #    para que el analisis por pais pueda excluirlos sin perder la fila.
    tratado["es_agregado_regional"] = tratado["pais"].isin(AGREGADOS_REGIONALES)

    # 6) Validacion de rangos (0-100 en porcentajes, anio dentro de ventana,
    #    valores no negativos en variables de area/conteo). No se encontraron
    #    violaciones, se deja como verificacion automatica documentada.
    columnas_no_negativas = [
        "area_perdida_bosque_ha", "emisiones_co2_mg", "area_transformada_ha",
        "num_focos_calor", "frp_promedio", "area_forestal_ha", "deforestacion_anual_ha_owid",
    ]
    violaciones_rango = int((tratado[columnas_no_negativas] < 0).sum().sum())
    violaciones_rango += int(((tratado["porcentaje_area_forestal"] < 0) | (tratado["porcentaje_area_forestal"] > 100)).sum())
    violaciones_rango += int(((tratado["confianza_promedio_focos"] < 0) | (tratado["confianza_promedio_focos"] > 100)).sum())
    violaciones_rango += int(((tratado["anio"] < 2001) | (tratado["anio"] > 2024)).sum())

    # 7) Valores atipicos: se marcan con un indicador por variable en vez de
    #    eliminarse, porque corresponden a eventos reales de perdida o quema
    #    extrema documentados en las fuentes, no a errores de captura.
    columnas_atipicos = ["area_perdida_bosque_ha", "emisiones_co2_mg", "area_transformada_ha", "num_focos_calor"]
    resumen_atipicos = {}
    for columna in columnas_atipicos:
        serie = tratado[columna].dropna()
        q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
        iqr = q3 - q1
        limite_superior = q3 + 1.5 * iqr
        bandera = columna + "_atipico"
        tratado[bandera] = (tratado[columna] > limite_superior).fillna(False)
        resumen_atipicos[columna] = {
            "limite_superior": round(float(limite_superior), 2),
            "marcados": int(tratado[bandera].sum()),
        }

    despues = perfil_basico(tratado)

    tratado.to_csv(SALIDA_DATOS, index=False)

    reporte = {
        "antes": antes,
        "despues": despues,
        "violaciones_rango_encontradas": violaciones_rango,
        "atipicos_marcados_no_eliminados": resumen_atipicos,
        "filas_eliminadas_por_duplicado": antes["filas"] - despues["filas"],
    }
    with open(SALIDA_REPORTE, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    print(json.dumps(reporte, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
