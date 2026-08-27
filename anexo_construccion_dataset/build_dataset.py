"""
build_dataset.py (v2)
======================
Construye el dataset inicial consolidado para "Deforestación y Transformación
del Territorio" (Etapa 1 - punto 4), adaptado a los formatos reales de archivo:

  - GFW:        1 archivo xlsx (COL.xlsx) con varias hojas (la 1a es README)
  - MapBiomas:  1 archivo xlsx (Statistics-for-Website-MB-Cobertura-col3.xlsx)
                con varias hojas (la 1a es READ_ME)
  - FIRMS:      varios csv, uno por año, viirs-snpp_AAAA_Colombia.csv
  - FAO SDG:    1 archivo xlsx (DF_SDG_15_1_1.xlsx)
  - OWID:       1 archivo csv (annual-deforestation.csv), ya en formato largo

Como no conocemos los nombres EXACTOS de cada hoja dentro de los xlsx, el
script las detecta automáticamente por palabras clave en el nombre de hoja
(ver _find_sheet). Al correrlo, imprime qué hoja asignó a cada pieza para
que puedas verificar. Si algo no calza, ajusta las palabras clave en
_find_sheet() o pásale el nombre de hoja exacto a mano en CONFIG.

USO
---
1. Ajusta las rutas en CONFIG.
2. pip install pandas numpy openpyxl
3. python build_dataset.py
4. Revisa la consola: primero la "Detección de hojas", luego el reporte de
   validación contra los requisitos del punto 4.
"""

import os
import re
import glob
import numpy as np
import pandas as pd

try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEOPANDAS_DISPONIBLE = True
except ImportError:
    GEOPANDAS_DISPONIBLE = False

# =============================================================================
# CONFIG
# =============================================================================
CONFIG = {
    "gfw_xlsx": "data/COL.xlsx",
    "mapbiomas_xlsx": "data/Statistics-for-Website-MB-Cobertura-col3.xlsx",
    "firms_dir": "data/firms",              # carpeta con viirs-snpp_AAAA_Colombia.csv
    "firms_shapefile": None,                # ej: "data/MGN_ADM_MPIO_GRAFICO.shp" (DANE) o "data/gadm41_COL_2.shp" (GADM)
                                             # si se deja en None, FIRMS se agrega por grilla lat/lon aproximada
    "firms_shapefile_col_departamento": None,  # opcional: fuerza el nombre exacto de columna si la auto-detección falla
    "firms_shapefile_col_municipio": None,     # ej: "dpto_cnmbr" / "mpio_cnmbr" (nombres, NO "dpto_ccdgo"/"mpio_ccdgo" que son códigos)
    "fao_xlsx": "data/DF_SDG_15_1_1.xlsx",
    "owid_csv": "data/annual-deforestation.csv",

    "anio_min": 2001,
    "anio_max": 2024,
    "umbral_dosel_gfw": 30,   # threshold de canopy cover a usar (30/50/75)
    "salida_csv": "dataset_consolidado.csv",
}

CENTROIDES_DEPARTAMENTOS_CO = {
    "amazonas": (-3.99, -70.25), "antioquia": (6.55, -75.68),
    "arauca": (7.09, -70.76), "atlantico": (10.70, -74.90),
    "bolivar": (8.68, -74.02), "boyaca": (5.70, -73.15),
    "caldas": (5.30, -75.50), "caqueta": (0.85, -73.90),
    "casanare": (5.75, -71.60), "cauca": (2.45, -76.60),
    "cesar": (9.70, -73.60), "choco": (5.70, -76.65),
    "cordoba": (8.30, -75.80), "cundinamarca": (5.00, -74.00),
    "guainia": (2.58, -68.55), "guaviare": (2.05, -72.65),
    "huila": (2.55, -75.55), "la guajira": (11.35, -72.50),
    "magdalena": (10.30, -74.30), "meta": (3.40, -73.20),
    "narino": (1.30, -77.35), "norte de santander": (7.90, -72.90),
    "putumayo": (0.45, -76.60), "quindio": (4.45, -75.68),
    "risaralda": (5.10, -75.95), "san andres y providencia": (12.55, -81.70),
    "santander": (6.90, -73.20), "sucre": (9.05, -75.30),
    "tolima": (4.10, -75.20), "valle del cauca": (3.90, -76.60),
    "vaupes": (0.85, -70.80), "vichada": (5.00, -69.00),
}


def _norm(s):
    if pd.isna(s):
        return s
    s = str(s).strip().lower()
    for a, b in {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}.items():
        s = s.replace(a, b)
    return s


def _find_col(columns, keywords):
    """Busca una columna cuyo nombre contenga alguna de las palabras clave."""
    for c in columns:
        cl = c.lower()
        if any(k in cl for k in keywords):
            return c
    return None


def _find_geo_name_col(columns, prefijos):
    """
    Busca la columna de NOMBRE (texto) de departamento/municipio en un
    shapefile, evitando quedarse con la de CÓDIGO por error. DANE suele
    traer ambas (p.ej. 'dpto_ccdgo' = código, 'dpto_cnmbr' = nombre) y
    ambas contienen el prefijo 'dpto', así que hay que priorizar
    explícitamente las que digan 'cnmbr'/'nombre'/'name' antes de aceptar
    cualquier otra que solo tenga el prefijo (que podría ser el código).
    """
    cols_lower = {c: c.lower() for c in columns}

    # 1. Columnas de nombre explícitas (DANE: *_CNMBR; genérico: *nombre*)
    candidatas = [c for c in columns if any(p in cols_lower[c] for p in prefijos)
                  and any(n in cols_lower[c] for n in ["cnmbr", "nombre"])]
    if candidatas:
        return candidatas[0], "nombre (detectada por 'cnmbr'/'nombre')"

    # 2. GADM: name_1 (departamento), name_2 (municipio) -- ya vienen en 'prefijos'
    candidatas = [c for c in columns if cols_lower[c] in prefijos]
    if candidatas:
        return candidatas[0], "nombre (GADM name_1/name_2)"

    # 3. Cualquier columna con el prefijo, EXCLUYENDO las que parezcan código
    candidatas = [c for c in columns if any(p in cols_lower[c] for p in prefijos)
                  and not any(k in cols_lower[c] for k in ["cdgo", "cod", "_id", "ccnct"])]
    if candidatas:
        return candidatas[0], "nombre (heurística: prefijo sin patrón de código)"

    # 4. Último recurso: cualquier columna con el prefijo (puede ser código)
    candidatas = [c for c in columns if any(p in cols_lower[c] for p in prefijos)]
    if candidatas:
        return candidatas[0], "ADVERTENCIA: puede ser columna de CÓDIGO, no de nombre"

    return None, None


def _advertir_si_parece_codigo(df, col, etiqueta):
    """Revisa una muestra de valores; si lucen puramente numéricos, avisa
    que probablemente se tomó una columna de código en vez de nombre."""
    muestra = df[col].dropna().astype(str).head(50)
    if len(muestra) and muestra.str.match(r"^\d+\.?0*$").mean() > 0.8:
        print(f"[AVISO] La columna '{col}' detectada para {etiqueta} contiene valores "
              f"que parecen CÓDIGOS numéricos (ej: {muestra.iloc[0]}), no nombres de texto. "
              f"Verifica el shapefile y, si hace falta, indica la columna correcta a mano "
              f"en CONFIG['firms_shapefile_col_departamento']/['firms_shapefile_col_municipio'].")


# =============================================================================
# Lectura de Excel multi-hoja con descarte de README y detección por keywords
# =============================================================================
def _leer_hojas_excel(path, patrones_readme=("read", "léame", "leeme", "acerca")):
    if path is None or not os.path.exists(path):
        print(f"[AVISO] No encontrado, se omite: {path}")
        return {}
    print(f"[OK] Abriendo: {path}")
    hojas = pd.read_excel(path, sheet_name=None)
    hojas = {k: v for k, v in hojas.items()
             if not any(p in k.lower() for p in patrones_readme)}
    print(f"     Hojas útiles detectadas: {list(hojas.keys())}")
    return hojas


def _find_sheet(hojas_dict, must_include, must_exclude=None):
    must_exclude = must_exclude or []
    for nombre in hojas_dict:
        nl = nombre.lower()
        if all(k in nl for k in must_include) and not any(k in nl for k in must_exclude):
            return nombre
    return None


# =============================================================================
# GFW: pérdida de cobertura arbórea (wide -> long)
# =============================================================================
def load_gfw_loss(df, geo_cols, nivel):
    if df is None or df.empty:
        return pd.DataFrame()
    if "threshold" in df.columns:
        df = df[df["threshold"] == CONFIG["umbral_dosel_gfw"]]

    year_cols = [c for c in df.columns if re.match(r"tc_loss_ha_\d{4}$", str(c))]
    df_long = df.melt(id_vars=geo_cols, value_vars=year_cols,
                       var_name="anio_col", value_name="area_perdida_bosque_ha")
    df_long["anio"] = df_long["anio_col"].str.extract(r"(\d{4})").astype(int)
    df_long = df_long.drop(columns=["anio_col"])
    df_long["nivel_analisis"] = nivel
    df_long["fuente_origen"] = "GFW"
    return df_long


def load_gfw_carbon(df, geo_cols):
    if df is None or df.empty:
        return pd.DataFrame()
    year_cols = [c for c in df.columns
                 if re.match(r"gfw_forest_carbon_gross_emissions_\d{4}__Mg_CO2e$", str(c))]
    if not year_cols:
        print("[AVISO] Hoja de carbono cargada pero sin columnas de emisiones por año reconocibles.")
        return pd.DataFrame()
    df_long = df.melt(id_vars=geo_cols, value_vars=year_cols,
                       var_name="anio_col", value_name="emisiones_co2_mg")
    df_long["anio"] = df_long["anio_col"].str.extract(r"(\d{4})").astype(int)
    return df_long.drop(columns=["anio_col"])


def load_gfw_drivers(df, geo_cols):
    if df is None or df.empty:
        return pd.DataFrame()
    if "threshold" in df.columns:
        df = df[df["threshold"] == CONFIG["umbral_dosel_gfw"]]
    if not {"year", "driver", "tc_loss_ha"}.issubset(df.columns):
        print("[AVISO] Hoja de drivers cargada pero faltan columnas esperadas (year/driver/tc_loss_ha).")
        return pd.DataFrame()
    idx = df.groupby(geo_cols + ["year"])["tc_loss_ha"].idxmax()
    dominante = df.loc[idx, geo_cols + ["year", "driver"]].rename(
        columns={"year": "anio", "driver": "driver_dominante"})
    return dominante


# =============================================================================
# MapBiomas: cobertura / transformación del territorio (wide -> long)
# =============================================================================
def load_mapbiomas(df, geo_cols):
    if df is None or df.empty:
        return pd.DataFrame()

    year_cols = [c for c in df.columns if re.match(r"^(19|20)\d{2}$", str(c))]
    if not year_cols or not {"class_level_0", "class_level_1"}.issubset(df.columns):
        print("[AVISO] Hoja MapBiomas cargada pero no tiene el formato esperado "
              "(columnas class_level_0/1 y años). Revisa nombres de columnas.")
        return pd.DataFrame()

    df_long = df.melt(id_vars=geo_cols + ["class_level_0", "class_level_1"],
                       value_vars=year_cols, var_name="anio", value_name="area_ha")
    df_long["anio"] = df_long["anio"].astype(int)
    df_long = df_long[(df_long["anio"] >= CONFIG["anio_min"]) &
                       (df_long["anio"] <= CONFIG["anio_max"])]

    # FIX: en la fuente, esta columna puede venir formateada como texto
    # (números como string), lo que hace que sum() concatene en vez de sumar
    # y termine clasificada como categórica en vez de numérica. Se fuerza
    # la conversión explícita antes de agregar.
    df_long["area_ha"] = pd.to_numeric(df_long["area_ha"], errors="coerce")

    agg = df_long.groupby(geo_cols + ["class_level_0", "class_level_1", "anio"],
                           as_index=False)["area_ha"].sum()

    antropico = agg[agg["class_level_0"].str.contains("Antr", case=False, na=False)]
    area_transformada = antropico.groupby(geo_cols + ["anio"], as_index=False)[
        "area_ha"].sum().rename(columns={"area_ha": "area_transformada_ha"})

    idx = antropico.groupby(geo_cols + ["anio"])["area_ha"].idxmax()
    clase_dom = antropico.loc[idx, geo_cols + ["anio", "class_level_1"]].rename(
        columns={"class_level_1": "clase_transformacion_dominante"})

    return area_transformada.merge(clase_dom, on=geo_cols + ["anio"], how="outer")


# =============================================================================
# NASA FIRMS: varios csv (uno por año) -> agregado espacio-temporal
# =============================================================================
def _parse_confidence(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return {"l": 25, "n": 50, "h": 75}.get(str(v).strip().lower(), np.nan)


def load_firms(dir_path, shapefile_path=None):
    if dir_path is None or not os.path.isdir(dir_path):
        print(f"[AVISO] Carpeta FIRMS no encontrada, se omite: {dir_path}")
        return pd.DataFrame()

    archivos = sorted(glob.glob(os.path.join(dir_path, "viirs-snpp_*_Colombia.csv")))
    if not archivos:
        print(f"[AVISO] No se encontraron archivos 'viirs-snpp_AAAA_Colombia.csv' en {dir_path}")
        return pd.DataFrame()

    dfs = []
    for f in archivos:
        print(f"[OK] Cargando: {f}")
        dfs.append(pd.read_csv(f))
    df = pd.concat(dfs, ignore_index=True)

    df["anio"] = pd.to_datetime(df["acq_date"]).dt.year
    df["confidence_num"] = df["confidence"].apply(_parse_confidence)

    # --- Intento de cruce espacial real (punto dentro de polígono) ---
    usar_shapefile = shapefile_path is not None and os.path.exists(shapefile_path)
    if shapefile_path is not None and not GEOPANDAS_DISPONIBLE:
        print("[AVISO] Diste un shapefile para FIRMS pero 'geopandas' no está instalado. "
              "Instala con:  pip install geopandas shapely\n"
              "        Mientras tanto, se usa el respaldo de agregación por grilla lat/lon.")
        usar_shapefile = False
    elif shapefile_path is not None and not usar_shapefile:
        print(f"[AVISO] No se encontró el shapefile en {shapefile_path}; se usa respaldo por grilla.")

    if usar_shapefile:
        print(f"[OK] Cruzando focos de calor con límites administrativos: {shapefile_path}")
        limites = gpd.read_file(shapefile_path)

        # Permite forzar la columna correcta a mano si la detección automática falla
        col_dep = CONFIG.get("firms_shapefile_col_departamento") or None
        col_mun = CONFIG.get("firms_shapefile_col_municipio") or None
        motivo_dep = motivo_mun = "forzada por CONFIG"
        if col_dep is None:
            col_dep, motivo_dep = _find_geo_name_col(limites.columns, ["dpto", "departamen", "name_1"])
        if col_mun is None:
            col_mun, motivo_mun = _find_geo_name_col(limites.columns, ["mpio", "municipio", "name_2"])

        if col_dep is None or col_mun is None:
            print(f"[AVISO] No se identificaron columnas de departamento/municipio en el shapefile "
                  f"(columnas disponibles: {list(limites.columns)}). Se usa respaldo por grilla.")
            usar_shapefile = False
        else:
            print(f"       Columna departamento: '{col_dep}' ({motivo_dep})")
            print(f"       Columna municipio:    '{col_mun}' ({motivo_mun})")
            _advertir_si_parece_codigo(limites, col_dep, "departamento")
            _advertir_si_parece_codigo(limites, col_mun, "municipio")
            puntos = gpd.GeoDataFrame(
                df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs="EPSG:4326")
            if limites.crs is not None and limites.crs != puntos.crs:
                limites = limites.to_crs(puntos.crs)
            cruce = gpd.sjoin(puntos, limites[[col_dep, col_mun, "geometry"]],
                               how="left", predicate="within")
            df["departamento"] = cruce[col_dep].values
            df["municipio"] = cruce[col_mun].values
            sin_match = df["municipio"].isna().mean() * 100
            print(f"       {100 - sin_match:.1f}% de los focos de calor quedaron asignados a un municipio "
                  f"({sin_match:.1f}% sin match, probablemente puntos fuera de tierra firme o error de coordenadas).")

    if usar_shapefile:
        llaves = ["departamento", "municipio", "anio"]
        agg = df.groupby(llaves, as_index=False, dropna=False).agg(
            num_focos_calor=("latitude", "count"),
            frp_promedio=("frp", "mean"),
            confianza_promedio_focos=("confidence_num", "mean"),
            latitud=("latitude", "mean"),
            longitud=("longitude", "mean"),
        )
    else:
        # Respaldo: sin shapefile, se agrega en una grilla aproximada de ~11km
        df["lat_grid"] = df["latitude"].round(1)
        df["lon_grid"] = df["longitude"].round(1)
        agg = df.groupby(["lat_grid", "lon_grid", "anio"], as_index=False).agg(
            num_focos_calor=("latitude", "count"),
            frp_promedio=("frp", "mean"),
            confianza_promedio_focos=("confidence_num", "mean"),
        ).rename(columns={"lat_grid": "latitud", "lon_grid": "longitud"})

    agg["nivel_analisis"] = "Regional"
    agg["fuente_origen"] = "FIRMS"
    agg["pais"] = "Colombia"
    return agg


# =============================================================================
# FAO SDG 15.1.1: detecta hoja con OBS_VALUE y filtra la serie de % forestal
# =============================================================================
def load_fao_sdg(path):
    """
    El archivo trae VARIAS hojas, cada una con una serie SDG distinta bajo
    el indicador 15.1.1. IMPORTANTE: en el archivo real de FAO, el código de
    texto de la serie (p.ej. AG_LND_FRST) está en la columna "SERIES", y
    "SERIES_ID" es un código NUMÉRICO (p.ej. 1867), no al revés. Por eso
    se filtra por la columna "SERIES" cuando existe, y solo se usa
    "SERIES_ID" como respaldo si "SERIES" no está presente.
      - AG_LND_FRST  -> porcentaje_area_forestal
      - AG_LND_FRSTN -> area_forestal_ha  (variable numérica adicional)
    """
    if path is None or not os.path.exists(path):
        print(f"[AVISO] No encontrado, se omite: {path}")
        return pd.DataFrame()

    todas = pd.read_excel(path, sheet_name=None)
    hojas_validas = [h for h in todas.values() if "OBS_VALUE" in h.columns]
    if not hojas_validas:
        print(f"[AVISO] Ninguna hoja de {path} tiene columna OBS_VALUE.")
        return pd.DataFrame()

    df = pd.concat(hojas_validas, ignore_index=True, sort=False)

    # Detecta cuál columna trae el código de texto (AG_LND_FRST, etc.)
    # probando primero "SERIES", luego "SERIES_ID", verificando que el
    # contenido sea texto (no numérico).
    col_codigo = None
    for candidata in ["SERIES", "SERIES_ID"]:
        if candidata in df.columns and df[candidata].astype(str).str.contains("[A-Za-z]", regex=True).any():
            col_codigo = candidata
            break

    if col_codigo is None:
        print(f"[AVISO] No se identificó una columna con el código de texto de la serie "
              f"(AG_LND_FRST, etc.) en {path}. Columnas disponibles: {list(df.columns)}")
        return pd.DataFrame()

    series_disponibles = df[[col_codigo, "SERIES_DESC"]].drop_duplicates()
    print(f"[OK] Cargando: {path} ({len(hojas_validas)} hojas, "
          f"{len(series_disponibles)} series distintas encontradas, "
          f"columna de código detectada: '{col_codigo}')")
    for _, row in series_disponibles.iterrows():
        print(f"       - {row[col_codigo]}: {row['SERIES_DESC']}")

    col_pais = "AREA" if "AREA" in df.columns else "REF_AREA"

    def _extraer_serie(codigo_serie, nombre_columna):
        sub = df[df[col_codigo].astype(str).str.upper() == codigo_serie]
        if sub.empty:
            print(f"[AVISO] No se encontró la serie {codigo_serie} en {path}; "
                  f"'{nombre_columna}' quedará vacía.")
            return pd.DataFrame(columns=["pais", "anio", nombre_columna])
        return sub[[col_pais, "TIME_PERIOD", "OBS_VALUE"]].rename(
            columns={col_pais: "pais", "TIME_PERIOD": "anio", "OBS_VALUE": nombre_columna})

    pct = _extraer_serie("AG_LND_FRST", "porcentaje_area_forestal")
    ha = _extraer_serie("AG_LND_FRSTN", "area_forestal_ha")

    out = pct.merge(ha, on=["pais", "anio"], how="outer")
    if out.empty:
        return out

    out["anio"] = pd.to_numeric(out["anio"], errors="coerce")
    out["nivel_analisis"] = out["pais"].apply(
        lambda p: "Nacional" if _norm(p) == "colombia" else "Global")
    out["fuente_origen"] = "FAO_SDG"
    return out


def load_owid(path):
    if path is None or not os.path.exists(path):
        print(f"[AVISO] No encontrado, se omite: {path}")
        return pd.DataFrame()
    print(f"[OK] Cargando: {path}")
    df = pd.read_csv(path)
    out = df.rename(columns={"Entity": "pais", "Year": "anio",
                              "Deforestation": "deforestacion_anual_ha_owid"})[
        ["pais", "anio", "deforestacion_anual_ha_owid"]]
    out["nivel_analisis"] = "Global"
    out["fuente_origen"] = "OWID"
    return out


def combinar_nivel(fuentes, llaves_geo, nivel):
    """
    Cruza (merge outer) varias tablas que comparten el MISMO nivel de
    granularidad geográfica (p.ej. todas a nivel municipio) en vez de
    apilarlas (concat), para no duplicar la unidad de observación
    lugar-año en filas separadas con la mitad de columnas en blanco.

    Normaliza las llaves geográficas (minúsculas, sin tildes) antes de
    cruzar, para que "Amazonas" y "AMAZONAS" o "Bogotá" y "Bogota" sí
    hagan match entre fuentes distintas.

    fuentes: lista de tuplas (dataframe, nombre_fuente)
    llaves_geo: columnas geográficas a usar como llave, p.ej. ["pais","departamento"]
    """
    fuentes = [(df, nom) for df, nom in fuentes if df is not None and not df.empty]
    if not fuentes:
        return pd.DataFrame()

    preparadas = []
    for df, nombre in fuentes:
        d = df.copy()
        for k in llaves_geo:
            if k not in d.columns:
                # dtype "object" explícito (no float NaN) para que el merge
                # no choque de tipos contra otra fuente donde esa misma
                # llave sí venga como texto (p.ej. FIRMS sin shapefile).
                d[k] = pd.Series([pd.NA] * len(d), index=d.index, dtype="object")
        for k in llaves_geo:
            d[k + "__norm"] = d[k].apply(_norm)
        d = d.drop(columns=[c for c in ["nivel_analisis", "fuente_origen"] if c in d.columns])
        d[f"_tiene_{nombre}"] = True
        preparadas.append((d, nombre))

    llaves_merge = [k + "__norm" for k in llaves_geo] + (
        ["anio"] if "anio" in preparadas[0][0].columns else [])

    resultado, primer_nombre = preparadas[0]
    for d, nombre in preparadas[1:]:
        resultado = resultado.merge(
            d, on=llaves_merge, how="outer", suffixes=("", f"__{nombre}"))
        # Reconciliar columnas de nombre geográfico duplicadas (coalesce:
        # toma el valor no nulo, priorizando la primera fuente que lo tenga)
        for k in llaves_geo:
            dup = f"{k}__{nombre}"
            if dup in resultado.columns:
                resultado[k] = resultado[k].combine_first(resultado[dup])
                resultado = resultado.drop(columns=[dup])

    resultado = resultado.drop(columns=[k + "__norm" for k in llaves_geo])
    resultado["nivel_analisis"] = nivel

    banderas = [c for c in resultado.columns if c.startswith("_tiene_")]

    def _fuente_combinada(row):
        activos = [c.replace("_tiene_", "") for c in banderas if row.get(c) is True]
        return "+".join(activos) if activos else np.nan

    resultado["fuente_origen"] = resultado.apply(_fuente_combinada, axis=1)
    resultado = resultado.drop(columns=banderas)
    return resultado


def agregar_centroides(df):
    if "departamento" not in df.columns:
        return df
    key = df["departamento"].apply(_norm)
    if "latitud" not in df.columns:
        df["latitud"] = np.nan
    if "longitud" not in df.columns:
        df["longitud"] = np.nan
    faltan = df["latitud"].isna()
    coords = key.map(lambda k: CENTROIDES_DEPARTAMENTOS_CO.get(k, (np.nan, np.nan)))
    df.loc[faltan, "latitud"] = coords[faltan].apply(lambda t: t[0])
    df.loc[faltan, "longitud"] = coords[faltan].apply(lambda t: t[1])
    return df


def validar_requisitos(df):
    numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    numericas = [c for c in numericas if c not in ("anio", "id_registro")]
    categoricas = [c for c in df.columns if c not in numericas + ["anio", "id_registro"]]

    print("\n" + "=" * 60)
    print("REPORTE DE VALIDACIÓN - Punto 4 (Dataset inicial)")
    print("=" * 60)
    print(f"Registros totales:        {len(df):,}  (mínimo 10.000)")
    print(f"Variables totales:        {df.shape[1]}  (mínimo 10)")
    print(f"Variables numéricas:      {len(numericas)}  -> {numericas}")
    print(f"Variables categóricas:    {len(categoricas)}  -> {categoricas}")
    print(f"Variable temporal (anio): {'OK' if 'anio' in df.columns else 'FALTA'}")
    geo_ok = any(c in df.columns for c in
                 ["pais", "departamento", "municipio", "latitud", "longitud"])
    print(f"Variable geográfica:      {'OK' if geo_ok else 'FALTA'}")
    print(f"Niveles presentes:        {sorted(df['nivel_analisis'].dropna().unique().tolist())}")
    print("-" * 60)
    print("Diagnóstico inicial de calidad (no se limpia, solo se reporta):")
    print(f"  Filas duplicadas:       {df.duplicated().sum():,}")
    print("  % nulos por columna:")
    print((df.isna().mean() * 100).round(1).sort_values(ascending=False).to_string())
    print("=" * 60)


def main():
    tablas = []

    print(f"[DEBUG] CONFIG['firms_shapefile'] = {CONFIG['firms_shapefile']!r}")
    if CONFIG["firms_shapefile"]:
        print(f"[DEBUG] ¿Existe esa ruta según Python? -> {os.path.exists(CONFIG['firms_shapefile'])}")
        print(f"[DEBUG] Directorio de trabajo actual   -> {os.getcwd()}")

    # ---------------------------------------------------------------
    # GFW: una sola vez se abren todas las hojas del xlsx, se detectan
    # por palabras clave, y se imprime el mapeo detectado.
    # ---------------------------------------------------------------
    gfw_hojas = _leer_hojas_excel(CONFIG["gfw_xlsx"])

    mapeo = {
        "country_loss": _find_sheet(gfw_hojas, ["tree cover loss"], ["subnational"]),
        "sub1_loss": _find_sheet(gfw_hojas, ["subnational 1", "tree cover loss"]),
        "sub2_loss": _find_sheet(gfw_hojas, ["subnational 2", "tree cover loss"]),
        "country_carbon": _find_sheet(gfw_hojas, ["carbon"], ["subnational"]),
        "sub1_carbon": _find_sheet(gfw_hojas, ["subnational 1", "carbon"]),
        "sub2_carbon": _find_sheet(gfw_hojas, ["subnational 2", "carbon"]),
        "country_drivers": _find_sheet(gfw_hojas, ["drivers"], ["subnational", "primary"]),
        "sub1_drivers": _find_sheet(gfw_hojas, ["subnational 1", "drivers"], ["primary"]),
        "sub2_drivers": _find_sheet(gfw_hojas, ["subnational 2", "drivers"], ["primary"]),
    }
    print("\n[Detección de hojas GFW]")
    for k, v in mapeo.items():
        print(f"  {k:16s} -> {v}")

    def hoja(nombre):
        s = mapeo[nombre]
        return gfw_hojas[s] if s else None

    df_g = load_gfw_loss(hoja("country_loss"), ["country"], "Global")
    df_n = load_gfw_loss(hoja("sub1_loss"), ["country", "subnational1"], "Nacional")
    df_r = load_gfw_loss(hoja("sub2_loss"), ["country", "subnational1", "subnational2"], "Regional")

    carb_g = load_gfw_carbon(hoja("country_carbon"), ["country"])
    carb_n = load_gfw_carbon(hoja("sub1_carbon"), ["country", "subnational1"])
    carb_r = load_gfw_carbon(hoja("sub2_carbon"), ["country", "subnational1", "subnational2"])

    if not df_g.empty and not carb_g.empty:
        df_g = df_g.merge(carb_g, on=["country", "anio"], how="left")
    if not df_n.empty and not carb_n.empty:
        df_n = df_n.merge(carb_n, on=["country", "subnational1", "anio"], how="left")
    if not df_r.empty and not carb_r.empty:
        df_r = df_r.merge(carb_r, on=["country", "subnational1", "subnational2", "anio"], how="left")

    drv_g = load_gfw_drivers(hoja("country_drivers"), ["country"])
    drv_n = load_gfw_drivers(hoja("sub1_drivers"), ["country", "subnational1"])
    drv_r = load_gfw_drivers(hoja("sub2_drivers"), ["country", "subnational1", "subnational2"])

    if not df_g.empty and not drv_g.empty:
        df_g = df_g.merge(drv_g, on=["country", "anio"], how="left")
    if not df_n.empty and not drv_n.empty:
        df_n = df_n.merge(drv_n, on=["country", "subnational1", "anio"], how="left")
    if not df_r.empty and not drv_r.empty:
        df_r = df_r.merge(drv_r, on=["country", "subnational1", "subnational2", "anio"], how="left")

    for d, cols in [(df_g, {"country": "pais"}),
                    (df_n, {"country": "pais", "subnational1": "departamento"}),
                    (df_r, {"country": "pais", "subnational1": "departamento", "subnational2": "municipio"})]:
        if not d.empty:
            d.rename(columns=cols, inplace=True)

    # ---------------------------------------------------------------
    # MapBiomas
    # ---------------------------------------------------------------
    mb_hojas = _leer_hojas_excel(CONFIG["mapbiomas_xlsx"])
    sheet_dep = _find_sheet(mb_hojas, ["departamento"])
    sheet_mun = _find_sheet(mb_hojas, ["municipio"])
    print("\n[Detección de hojas MapBiomas]")
    print(f"  departamento -> {sheet_dep}")
    print(f"  municipio    -> {sheet_mun}")

    mb_dep = load_mapbiomas(mb_hojas.get(sheet_dep) if sheet_dep else None, ["departamento", "pais"])
    mb_mun = load_mapbiomas(mb_hojas.get(sheet_mun) if sheet_mun else None, ["municipio", "departamento", "pais"])

    # ---------------------------------------------------------------
    # FIRMS, FAO, OWID
    # ---------------------------------------------------------------
    firms_agg = load_firms(CONFIG["firms_dir"], CONFIG.get("firms_shapefile"))
    fao = load_fao_sdg(CONFIG["fao_xlsx"])
    owid = load_owid(CONFIG["owid_csv"])

    # ---------------------------------------------------------------
    # Consolidación: MERGE (no concat) dentro de cada nivel, para las
    # fuentes que comparten exactamente la misma granularidad geográfica.
    #
    # FIRMS se incluye en el merge Regional (con GFW y MapBiomas) por
    # departamento/municipio/año. Si se dio un shapefile (CONFIG
    # "firms_shapefile"), FIRMS sí trae departamento/municipio reales por
    # cruce espacial, y cruza de verdad con GFW/MapBiomas. Si NO se dio
    # shapefile, FIRMS queda con departamento/municipio en NaN y el merge
    # simplemente la deja como filas aparte (mismo comportamiento de
    # respaldo que antes, sin romper nada).
    # ---------------------------------------------------------------
    nivel_global = combinar_nivel(
        [(df_g, "GFW"), (fao, "FAO_SDG"), (owid, "OWID")],
        llaves_geo=["pais"], nivel="Global")

    nivel_nacional = combinar_nivel(
        [(df_n, "GFW"), (mb_dep, "MapBiomas")],
        llaves_geo=["pais", "departamento"], nivel="Nacional")

    nivel_regional = combinar_nivel(
        [(df_r, "GFW"), (mb_mun, "MapBiomas"), (firms_agg, "FIRMS")],
        llaves_geo=["pais", "departamento", "municipio"], nivel="Regional")

    tablas = [t for t in [nivel_global, nivel_nacional, nivel_regional]
              if t is not None and not t.empty]

    if not tablas:
        print("\n[ERROR] No se cargó ninguna fuente. Revisa las rutas en CONFIG.")
        return

    df_final = pd.concat(tablas, ignore_index=True, sort=False)
    df_final = agregar_centroides(df_final)
    df_final.insert(0, "id_registro", range(1, len(df_final) + 1))

    if "anio" in df_final.columns:
        df_final = df_final[(df_final["anio"] >= CONFIG["anio_min"]) &
                             (df_final["anio"] <= CONFIG["anio_max"])]

    columnas_finales = [
        "id_registro", "nivel_analisis", "fuente_origen", "pais", "departamento",
        "municipio", "anio", "latitud", "longitud", "area_perdida_bosque_ha",
        "emisiones_co2_mg", "driver_dominante", "area_transformada_ha",
        "clase_transformacion_dominante", "num_focos_calor", "frp_promedio",
        "confianza_promedio_focos", "porcentaje_area_forestal", "area_forestal_ha",
        "deforestacion_anual_ha_owid",
    ]
    for c in columnas_finales:
        if c not in df_final.columns:
            df_final[c] = np.nan
    df_final = df_final[columnas_finales]

    df_final.to_csv(CONFIG["salida_csv"], index=False)
    print(f"\n[OK] Dataset guardado en: {CONFIG['salida_csv']}")

    validar_requisitos(df_final)


if __name__ == "__main__":
    main()
