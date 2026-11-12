"""
Etapa 6 - Conocimiento Oculto
Prepara, a partir del dataset tratado (deforestacion_limpio.csv), los dos
conjuntos que se cargan en Orange Data Mining:

  1. datos_supervisado.csv  -> una fila por municipio y año (2004-2024)
     Pregunta: con lo que se sabe hasta el año anterior, ¿el municipio tendrá
     una pérdida de bosque ALTA este año?
     Variable objetivo: clase_perdida ("Alta" / "No alta")
     Predictoras: solo información del pasado (rezagos t-1, t-2, media de 3 años)
     + características fijas (ubicación, driver dominante).

  2. datos_clustering.csv   -> una fila por municipio (perfil histórico)
     Pregunta: ¿qué perfiles de municipios existen según la magnitud,
     tendencia, fuego y transformación del suelo?

Transformaciones adicionales (documentar en el informe):
  * Solo nivel Regional (municipios de Colombia) y sin agregados regionales.
  * El dataset tratado trae hasta 3 filas casi idénticas por municipio-año
    (misma pérdida, emisiones que difieren levemente). Se colapsan a una fila
    (mismo criterio del modelo estrella: primer valor; emisiones = promedio).
    Si no se hace, la validación cruzada tendría filas "gemelas" en
    entrenamiento y prueba y las métricas saldrían infladas.
  * Se excluyen las emisiones de CO2 como predictoras: se calculan a partir
    de la pérdida del mismo año (correlación 0,99), sería fuga de información.
  * El umbral de "Alta" es el percentil 75 de la pérdida en el periodo de
    entrenamiento (2004-2018), para no usar información del periodo de prueba.

Uso:
    python conocimiento_oculto/preparar_datos_orange.py deforestacion_limpio.csv
"""
import json
import sys
from pathlib import Path

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=RuntimeWarning)

ANIO_CORTE = 2018  # entrenamiento <= 2018, prueba >= 2019
SALIDA = Path(__file__).resolve().parent / "datos"


def cargar_municipio_anio(ruta):
    d = pd.read_csv(ruta, low_memory=False)
    m = d[(d["nivel_analisis"] == "Regional") & (~d["es_agregado_regional"].astype(bool))]
    m = m[m["municipio"].notna() & m["departamento"].notna()]
    filas_antes = len(m)
    g = (
        m.groupby(["departamento", "municipio", "anio"])
        .agg(
            perdida_ha=("area_perdida_bosque_ha", "first"),
            emisiones_co2_mg=("emisiones_co2_mg", "mean"),
            area_transformada_ha=("area_transformada_ha", "first"),
            focos_calor=("num_focos_calor", "first"),
            frp_promedio=("frp_promedio", "first"),
            driver_dominante=("driver_dominante", "first"),
            latitud=("latitud", "first"),
            longitud=("longitud", "first"),
        )
        .reset_index()
        .sort_values(["departamento", "municipio", "anio"])
    )
    return g, filas_antes


def construir_supervisado(g):
    g = g.copy()
    k = g.groupby(["departamento", "municipio"])
    g["perdida_t1"] = k["perdida_ha"].shift(1)
    g["perdida_t2"] = k["perdida_ha"].shift(2)
    g["perdida_media_3a"] = k["perdida_ha"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=2).mean()
    )
    g["tendencia_perdida_t1"] = g["perdida_t1"] - g["perdida_t2"]
    g["area_transformada_t1"] = k["area_transformada_ha"].shift(1)
    g["var_transformada_t1"] = g["area_transformada_t1"] - k["area_transformada_ha"].shift(2)
    g["focos_t1"] = k["focos_calor"].shift(1)  # FIRMS solo cubre 2012-2022 -> nulos esperados

    g = g[(g["anio"] >= 2004) & g["perdida_ha"].notna() & g["perdida_t1"].notna()]
    umbral = float(g.loc[g["anio"] <= ANIO_CORTE, "perdida_ha"].quantile(0.75))
    g["clase_perdida"] = np.where(g["perdida_ha"] >= umbral, "Alta", "No alta")
    g["particion"] = np.where(g["anio"] <= ANIO_CORTE, "Entrenamiento", "Prueba")

    columnas = [
        # metas (identificación, no entran al modelo)
        "departamento", "municipio", "anio", "particion", "perdida_ha",
        # predictoras
        "perdida_t1", "perdida_t2", "perdida_media_3a", "tendencia_perdida_t1",
        "area_transformada_t1", "var_transformada_t1", "focos_t1",
        "driver_dominante", "latitud", "longitud",
        # objetivo
        "clase_perdida",
    ]
    return g[columnas].round(4), umbral


def pendiente(anios, valores):
    ok = ~np.isnan(valores)
    if ok.sum() < 5:
        return np.nan
    return float(np.polyfit(anios[ok], valores[ok], 1)[0])


def construir_clustering(g):
    filas = []
    for (dep, mun), x in g.groupby(["departamento", "municipio"]):
        x = x.sort_values("anio")
        p = x["perdida_ha"].to_numpy(dtype=float)
        a = x["anio"].to_numpy(dtype=float)
        total = np.nansum(p)
        reciente = np.nansum(x.loc[x["anio"] >= 2015, "perdida_ha"])
        t = x["area_transformada_ha"].dropna()
        f = x.loc[x["anio"].between(2012, 2022), "focos_calor"]
        filas.append({
            "departamento": dep,
            "municipio": mun,
            "latitud": x["latitud"].dropna().iloc[0] if x["latitud"].notna().any() else np.nan,
            "longitud": x["longitud"].dropna().iloc[0] if x["longitud"].notna().any() else np.nan,
            "driver_dominante": x["driver_dominante"].mode().iat[0] if x["driver_dominante"].notna().any() else None,
            # variables de agrupamiento
            "log_perdida_media_anual": np.log1p(np.nanmean(p)),
            "proporcion_perdida_reciente": reciente / total if total > 0 else np.nan,
            "pendiente_perdida_rel": pendiente(a, p) / (np.nanmean(p) + 1),
            "variabilidad_perdida_cv": np.nanstd(p) / (np.nanmean(p) + 1),
            "log_focos_medios": np.log1p(f.mean()) if f.notna().any() else 0.0,
            "log_area_transformada_media": np.log1p(t.mean()) if len(t) else np.nan,
            "crecimiento_transformada_pct": ((t.iloc[-1] - t.iloc[0]) / t.iloc[0] * 100) if len(t) > 1 and t.iloc[0] > 0 else np.nan,
            "anios_con_datos": int(np.sum(~np.isnan(p))),
        })
    c = pd.DataFrame(filas)
    c = c[c["anios_con_datos"] >= 10]
    return c.round(4)


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "deforestacion_limpio.csv"
    SALIDA.mkdir(parents=True, exist_ok=True)
    g, filas_antes = cargar_municipio_anio(ruta)
    sup, umbral = construir_supervisado(g)
    clu = construir_clustering(g)
    sup.to_csv(SALIDA / "datos_supervisado.csv", index=False)
    clu.to_csv(SALIDA / "datos_clustering.csv", index=False)
    reporte = {
        "filas_regionales_originales": int(filas_antes),
        "filas_municipio_anio": int(len(g)),
        "supervisado": {
            "filas": int(len(sup)),
            "umbral_alta_ha_p75_2004_2018": umbral,
            "distribucion_clase": sup["clase_perdida"].value_counts().to_dict(),
            "filas_por_particion": sup["particion"].value_counts().to_dict(),
        },
        "clustering": {"municipios": int(len(clu))},
    }
    (SALIDA / "reporte_preparacion.json").write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(reporte, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
