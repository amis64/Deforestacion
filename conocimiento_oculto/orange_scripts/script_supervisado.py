# Widget "Python Script" de Orange - FLUJO SUPERVISADO
# Entrada: salida del widget Group By (una fila por departamento-municipio-anio).
# Salida: tabla con rezagos (solo información del pasado), clase_perdida y particion.
import numpy as np
from Orange.data.pandas_compat import table_from_frame, table_to_frame

df = table_to_frame(in_data, include_metas=True)
# Group By nombra las columnas "variable - Agregación"; se deja solo el nombre original
df.columns = [str(c).split(" - ")[0] for c in df.columns]
df["anio"] = df["anio"].astype(float).astype(int)
df = df.sort_values(["departamento", "municipio", "anio"])

k = df.groupby(["departamento", "municipio"])
df["perdida_t1"] = k["area_perdida_bosque_ha"].shift(1)
df["perdida_t2"] = k["area_perdida_bosque_ha"].shift(2)
df["perdida_media_3a"] = k["area_perdida_bosque_ha"].transform(
    lambda s: s.shift(1).rolling(3, min_periods=2).mean())
df["tendencia_perdida_t1"] = df["perdida_t1"] - df["perdida_t2"]
df["area_transformada_t1"] = k["area_transformada_ha"].shift(1)
df["var_transformada_t1"] = df["area_transformada_t1"] - k["area_transformada_ha"].shift(2)
df["focos_t1"] = k["num_focos_calor"].shift(1)

df = df[(df["anio"] >= 2004) & df["area_perdida_bosque_ha"].notna() & df["perdida_t1"].notna()]
UMBRAL = df.loc[df["anio"] <= 2018, "area_perdida_bosque_ha"].quantile(0.75)  # P75 solo del entrenamiento
print("Umbral 'Alta' (ha):", UMBRAL)
df["clase_perdida"] = np.where(df["area_perdida_bosque_ha"] >= UMBRAL, "Alta", "No alta")
df["particion"] = np.where(df["anio"] <= 2018, "Entrenamiento", "Prueba")
df["anio"] = df["anio"].astype(str)  # el año se usa solo para identificar/partir, no como predictor

columnas = ["departamento", "municipio", "anio", "particion", "area_perdida_bosque_ha",
            "perdida_t1", "perdida_t2", "perdida_media_3a", "tendencia_perdida_t1",
            "area_transformada_t1", "var_transformada_t1", "focos_t1",
            "driver_dominante", "latitud", "longitud", "clase_perdida"]
out_data = table_from_frame(df[columnas].reset_index(drop=True))
print(len(df), "filas;", df["clase_perdida"].value_counts().to_dict())
