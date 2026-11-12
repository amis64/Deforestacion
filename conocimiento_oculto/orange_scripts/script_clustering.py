# Widget "Python Script" de Orange - FLUJO CLUSTERING
# Entrada: salida del widget Group By (una fila por departamento-municipio-anio).
# Salida: una fila por municipio con su perfil histórico (variables para k-Means).
import numpy as np
import pandas as pd
from Orange.data.pandas_compat import table_from_frame, table_to_frame

df = table_to_frame(in_data, include_metas=True)
df.columns = [str(c).split(" - ")[0] for c in df.columns]
df["anio"] = df["anio"].astype(float).astype(int)

def perfil(x):
    x = x.sort_values("anio")
    p = x["area_perdida_bosque_ha"].astype(float)
    total, media = p.sum(), p.mean()
    ok = p.notna()
    pend = np.polyfit(x.loc[ok, "anio"], p[ok], 1)[0] if ok.sum() >= 5 else np.nan
    t = x["area_transformada_ha"].dropna()
    f = x.loc[x["anio"].between(2012, 2022), "num_focos_calor"]
    return pd.Series({
        "latitud": x["latitud"].dropna().iloc[0] if x["latitud"].notna().any() else np.nan,
        "longitud": x["longitud"].dropna().iloc[0] if x["longitud"].notna().any() else np.nan,
        "log_perdida_media_anual": np.log1p(media),
        "proporcion_perdida_reciente": p[x["anio"] >= 2015].sum() / total if total > 0 else np.nan,
        "pendiente_perdida_rel": pend / (media + 1),
        "variabilidad_perdida_cv": p.std(ddof=0) / (media + 1),
        "log_focos_medios": np.log1p(f.mean()) if f.notna().any() else 0.0,
        "log_area_transformada_media": np.log1p(t.mean()) if len(t) else np.nan,
        "crecimiento_transformada_pct": (t.iloc[-1] - t.iloc[0]) / t.iloc[0] * 100 if len(t) > 1 and t.iloc[0] > 0 else np.nan,
        "anios_con_datos": int(ok.sum()),
    })

res = df.groupby(["departamento", "municipio"]).apply(perfil, include_groups=False).reset_index()
res = res[res["anios_con_datos"] >= 10]
out_data = table_from_frame(res)
print(len(res), "municipios")
