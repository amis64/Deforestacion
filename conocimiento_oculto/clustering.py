# -*- coding: utf-8 -*-
"""
Verificación en Python del flujo de clustering de Orange (Etapa 6).

Flujo: perfil por municipio (script de Python) -> Select Columns (7 variables) -> Preprocess (imputar con el promedio) ->
k-Means (k de 2 a 8, k-means++, 10 repeticiones, 300 iteraciones, columnas normalizadas) -> Silhouette Plot, Box Plot,
mapa (latitud/longitud), Group By (perfil promedio por grupo). La causa dominante y la ubicación NO entran al modelo;
se usan después para describir los grupos.
"""
import os
import warnings

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
VARS = ["log_perdida_media_anual", "proporcion_perdida_reciente", "pendiente_perdida_rel", "variabilidad_perdida_cv",
        "log_focos_medios", "log_area_transformada_media", "crecimiento_transformada_pct"]
ETIQ = {"log_perdida_media_anual": "log(1 + pérdida media anual, ha)", "proporcion_perdida_reciente": "fracción de la pérdida ocurrida desde 2015",
        "pendiente_perdida_rel": "pendiente de la pérdida (relativa a su media)", "variabilidad_perdida_cv": "variabilidad anual de la pérdida (CV)",
        "log_focos_medios": "log(1 + focos de calor medios 2012–2022)", "log_area_transformada_media": "log(1 + área transformada media, ha)",
        "crecimiento_transformada_pct": "crecimiento del área transformada (%)"}


def calcular(ruta=None, pred_te=None):
    ruta = ruta or os.path.join(AQUI, "datos", "datos_clustering.csv")
    d = pd.read_csv(ruta)
    X = d[VARS].copy()
    faltantes = {v: int(X[v].isna().sum()) for v in VARS}
    Xi = pd.DataFrame(SimpleImputer(strategy="mean").fit_transform(X), columns=VARS)
    Z = StandardScaler().fit_transform(Xi)
    comp, etiquetas = [], {}
    for k in range(2, 9):
        km = KMeans(k, init="k-means++", n_init=10, max_iter=300, random_state=0).fit(Z)
        etiquetas[k] = km.labels_
        tam = np.bincount(km.labels_)
        comp.append(dict(k=k, silueta=float(silhouette_score(Z, km.labels_)), davies_bouldin=float(davies_bouldin_score(Z, km.labels_)),
                         calinski_harabasz=float(calinski_harabasz_score(Z, km.labels_)), tamanos=[int(t) for t in sorted(tam, reverse=True)],
                         minimo=int(tam.min())))
    mejor = max(comp, key=lambda c: c["silueta"])["k"]
    # k elegido: mejor silueta entre k >= 3 (con k = 2 solo se separa «alto» de «bajo») y sin grupos de menos del 2 % de los municipios
    validos = [c for c in comp if c["k"] >= 3 and c["minimo"] >= 0.02 * len(d)]
    k = max(validos, key=lambda c: c["silueta"])["k"]
    lab = etiquetas[k]
    # numerar los grupos de mayor a menor pérdida media
    orden = d.assign(g=lab).groupby("g").log_perdida_media_anual.mean().sort_values(ascending=False).index.tolist()
    nuevo = {viejo: i + 1 for i, viejo in enumerate(orden)}
    d["grupo"] = [nuevo[x] for x in lab]
    d["silueta"] = silhouette_samples(Z, d.grupo)
    d["perdida_media_ha"] = np.expm1(d.log_perdida_media_anual)
    NOMBRES4 = ["Frentes de mayor pérdida", "Pérdida alta sostenida", "Pérdida moderada", "Pérdida baja y en descenso"]
    perfil = []
    for gno, x in d.groupby("grupo"):
        top = x.departamento.value_counts().head(4)
        drv = x.driver_dominante.value_counts(normalize=True).head(3)
        perfil.append(dict(
            grupo=int(gno), nombre=(NOMBRES4[gno - 1] if k == 4 else 'Grupo %d' % gno), municipios=int(len(x)), pct=float(len(x) / len(d)), silueta=float(x.silueta.mean()),
            perdida_media_ha_mediana=float(x.perdida_media_ha.median()), pct_perdida_total=float(x.perdida_media_ha.sum() / d.perdida_media_ha.sum()),
            medias={v: float(x[v].mean()) for v in VARS},
            medianas={v: float(x[v].median()) for v in VARS},
            departamentos=[[a, int(b)] for a, b in top.items()],
            causas=[[a, float(b)] for a, b in drv.items()],
            ejemplos=[[r.municipio, r.departamento] for r in x.sort_values("perdida_media_ha", ascending=False).head(4).itertuples()]))
    # ¿en qué grupos se concentra la pérdida alta? (años de prueba) y dónde falla el modelo supervisado
    extra = {}
    if pred_te is not None:
        t = pred_te.merge(d[["departamento", "municipio", "grupo"]], on=["departamento", "municipio"], how="left")
        extra["alta_por_grupo"] = {int(g): dict(filas=int(len(x)), alta=int(x.real.sum()), pct_alta=float(x.real.mean()),
                                               recall=float(((x.pred == 1) & (x.real == 1)).sum() / max(x.real.sum(), 1)))
                                   for g, x in t.dropna(subset=["grupo"]).groupby("grupo")}
    # puntos para el mapa
    mapa = [[round(float(r.longitud), 3), round(float(r.latitud), 3), int(r.grupo)] for r in d.itertuples() if pd.notna(r.latitud) and pd.notna(r.longitud)]
    reg = None
    return dict(
        n_municipios=int(len(d)), variables=[dict(nombre=v, etiqueta=ETIQ[v], faltantes=faltantes[v]) for v in VARS],
        faltantes_total=int(sum(faltantes.values())), comparacion=comp, k_elegido=int(k), k_mejor_silueta=int(mejor),
        silueta_global=float(silhouette_score(Z, d.grupo)), perfil=perfil, mapa=mapa, **extra,
        correlaciones={a: {b: float(x) for b, x in r.items()} for a, r in pd.DataFrame(Z, columns=VARS).corr().round(3).iterrows()},
    )


if __name__ == "__main__":
    r = calcular()
    for c in r["comparacion"]:
        print(c["k"], round(c["silueta"], 3), round(c["davies_bouldin"], 2), round(c["calinski_harabasz"]), c["tamanos"])
    print("k =", r["k_elegido"])
    for p in r["perfil"]:
        print(p["grupo"], p["municipios"], round(p["silueta"], 2), round(p["perdida_media_ha_mediana"], 1), p["departamentos"][:3], p["causas"][:2])
        print("   ", {k: round(v, 2) for k, v in p["medias"].items()})
