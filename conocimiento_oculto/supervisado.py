# -*- coding: utf-8 -*-
"""
Verificación en Python del flujo supervisado de Orange (Etapa 6).

Problema: dado el historial de un municipio hasta el año anterior (rezagos, tendencia, transformación del suelo,
focos de calor, causa dominante, ubicación), ¿su pérdida de bosque de este año será ALTA?
Alta = pérdida >= percentil 75 de 2004-2018 (129 ha). Entrenamiento: 2004-2018. Prueba: 2019-2024
(el mismo esquema del flujo: «Test and Score» con «Test on test data»).

Los tres modelos equivalen a los widgets de Orange: Logistic Regression (Ridge, C = 1), Tree (binario, profundidad 5,
hojas >= 50, no dividir < 100, mayoría suficiente 95 %) y Random Forest (200 árboles, no dividir < 10, semilla fija).
Orange usa su propia implementación del árbol y estandariza/imputa a su manera; por eso las cifras pueden diferir
levemente de las de la herramienta (en el informe y en la web valen las de Orange).
"""
import os
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, matthews_corrcoef, precision_score,
                             recall_score, roc_auc_score, roc_curve)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
NUM = ["perdida_t1", "perdida_t2", "perdida_media_3a", "tendencia_perdida_t1", "area_transformada_t1",
       "var_transformada_t1", "focos_t1", "latitud", "longitud"]
CAT = ["driver_dominante"]
ETIQ = {"perdida_t1": "pérdida del año anterior", "perdida_t2": "pérdida de hace 2 años",
        "perdida_media_3a": "promedio de los 3 años previos", "tendencia_perdida_t1": "tendencia (t-1 menos t-2)",
        "area_transformada_t1": "área transformada (t-1)", "var_transformada_t1": "cambio del área transformada",
        "focos_t1": "focos de calor (t-1)", "latitud": "latitud", "longitud": "longitud",
        "driver_dominante": "causa dominante"}
MODELOS = {
    "Regresión logística": dict(orange="Logistic Regression", params="regularización Ridge (L2), C = 1; variables estandarizadas e imputadas con el promedio"),
    "Árbol de decisión": dict(orange="Tree", params="árbol binario; hojas con al menos 50 casos; no dividir subconjuntos de menos de 100; profundidad máxima 5; detener con mayoría del 95 %"),
    "Random Forest": dict(orange="Random Forest", params="200 árboles; no dividir subconjuntos de menos de 10; semilla fija; sin límite de profundidad"),
}


def _modelo(nombre):
    imp = SimpleImputer(strategy="mean")
    if nombre == "Regresión logística":
        return make_pipeline(imp, StandardScaler(), LogisticRegression(C=1.0, max_iter=3000))
    if nombre == "Árbol de decisión":
        return make_pipeline(imp, DecisionTreeClassifier(criterion="entropy", max_depth=5, min_samples_leaf=50,
                                                         min_samples_split=100, random_state=0))
    return make_pipeline(imp, RandomForestClassifier(n_estimators=200, min_samples_split=10, random_state=0, n_jobs=-1))


def _matriz(df, cols, ref=None):
    x = df[[c for c in cols if c in NUM]].copy()
    for c in [c for c in cols if c in CAT or c == "driver_t1"]:
        x = pd.concat([x, pd.get_dummies(df[c].fillna("(sin dato)"), prefix=c)], axis=1)
    return x if ref is None else x.reindex(columns=ref.columns, fill_value=0)


def _metricas(y, pred, prob):
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(accuracy=accuracy_score(y, pred), auc=roc_auc_score(y, prob), f1=f1_score(y, pred), precision=precision_score(y, pred),
                recall=recall_score(y, pred), mcc=matthews_corrcoef(y, pred),
                f1_pond=f1_score(y, pred, average="weighted"), precision_pond=precision_score(y, pred, average="weighted"),
                recall_pond=recall_score(y, pred, average="weighted"),
                matriz=[[int(tn), int(fp)], [int(fn), int(tp)]])


def calcular(ruta=None):
    ruta = ruta or os.path.join(AQUI, "datos", "datos_supervisado.csv")
    d = pd.read_csv(ruta).sort_values(["departamento", "municipio", "anio"]).reset_index(drop=True)
    d["driver_t1"] = d.groupby(["departamento", "municipio"]).driver_dominante.shift(1)
    tr, te = d[d.particion == "Entrenamiento"], d[d.particion == "Prueba"]
    ytr, yte = (tr.clase_perdida == "Alta").astype(int), (te.clase_perdida == "Alta").astype(int)
    xtr = _matriz(tr, NUM + CAT)
    xte = _matriz(te, NUM + CAT, xtr)
    umbral = float(tr.loc[tr.clase_perdida == "Alta", "perdida_ha"].min())

    res = dict(
        problema="¿La pérdida de bosque de un municipio será alta este año?",
        umbral_alta_ha=umbral, anio_corte=2018,
        n_total=int(len(d)), n_entrenamiento=int(len(tr)), n_prueba=int(len(te)),
        alta_entrenamiento=int(ytr.sum()), alta_prueba=int(yte.sum()),
        pct_alta_entrenamiento=float(ytr.mean()), pct_alta_prueba=float(yte.mean()),
        municipios=int(d[["departamento", "municipio"]].drop_duplicates().shape[0]),
        variables=[dict(nombre=c, etiqueta=ETIQ[c], tipo="categórica" if c in CAT else "numérica",
                        faltantes=float(d[c].isna().mean())) for c in NUM + CAT],
    )
    # líneas base
    pers = (te.perdida_t1 >= umbral).astype(int)
    res["baseline_mayoritaria"] = float(1 - yte.mean())
    res["baseline_persistencia"] = dict(
        regla="Alta si la pérdida del año anterior ya fue de %d ha o más" % round(umbral),
        accuracy=accuracy_score(yte, pers), f1=f1_score(yte, pers), precision=precision_score(yte, pers),
        recall=recall_score(yte, pers), mcc=matthews_corrcoef(yte, pers),
        matriz=confusion_matrix(yte, pers, labels=[0, 1]).tolist())

    modelos, ajustados = {}, {}
    for nombre in MODELOS:
        m = _modelo(nombre).fit(xtr, ytr)
        ajustados[nombre] = m
        prob = m.predict_proba(xte)[:, 1]
        pred = (prob >= 0.5).astype(int)
        r = _metricas(yte, pred, prob)
        fpr, tpr, _ = roc_curve(yte, prob)
        idx = np.unique(np.linspace(0, len(fpr) - 1, 60).astype(int))
        r["roc"] = [[round(float(fpr[i]), 4), round(float(tpr[i]), 4)] for i in idx]
        r.update(MODELOS[nombre])
        # estabilidad por año de prueba
        r["por_anio"] = {int(a): dict(accuracy=accuracy_score(yte[te.anio == a], pred[(te.anio == a).values]),
                                      recall=recall_score(yte[te.anio == a], pred[(te.anio == a).values]),
                                      n=int((te.anio == a).sum()))
                         for a in sorted(te.anio.unique())}
        modelos[nombre] = r
    res["modelos"] = modelos

    # modelo elegido: mejor F1 de la clase Alta; desempata AUC (se documenta el criterio)
    orden = sorted(modelos, key=lambda n: (round(modelos[n]["f1"], 3), modelos[n]["auc"]), reverse=True)
    res["elegido"] = orden[0]
    res["criterio_eleccion"] = "mayor F1 de la clase Alta (equilibra precisión y recall); a igualdad, mayor AUC"

    # interpretación
    rf = ajustados["Random Forest"][-1]
    imp = pd.Series(rf.feature_importances_, index=xtr.columns)
    agr = {}
    for c, v in imp.items():
        base = "driver_dominante" if c.startswith("driver_dominante_") else c
        agr[ETIQ[base]] = agr.get(ETIQ[base], 0) + float(v)
    res["importancia_variables"] = dict(sorted(agr.items(), key=lambda t: -t[1]))
    lr = ajustados["Regresión logística"]
    coef = pd.Series(lr[-1].coef_[0], index=xtr.columns)
    res["coeficientes_logistica"] = [[k, float(v)] for k, v in coef.reindex(coef.abs().sort_values(ascending=False).index).head(10).items()]
    a3 = make_pipeline(SimpleImputer(strategy="mean"), DecisionTreeClassifier(criterion="entropy", max_depth=3, min_samples_leaf=50, random_state=0)).fit(xtr, ytr)
    res["arbol_reglas"] = export_text(a3[-1], feature_names=list(xtr.columns), max_depth=3)

    # sensibilidad: variable de causa dominante (mismo año, año anterior, sin ella)
    sens = {}
    for etiqueta, cols in (("con la causa del mismo año (flujo de Orange)", NUM + CAT), ("sin la causa dominante", NUM),
                           ("con la causa del año anterior", NUM + ["driver_t1"]),
                           ("sin latitud ni longitud", [c for c in NUM if c not in ("latitud", "longitud")] + CAT)):
        a, b = _matriz(tr, cols), None
        b = _matriz(te, cols, a)
        m = _modelo("Random Forest").fit(a, ytr)
        p = m.predict_proba(b)[:, 1]
        sens[etiqueta] = dict(f1=f1_score(yte, (p >= .5).astype(int)), auc=roc_auc_score(yte, p), accuracy=accuracy_score(yte, (p >= .5).astype(int)))
    res["sensibilidad_causa"] = sens
    res["filas_sin_causa_pct_alta"] = float((d.loc[d.driver_dominante.isna(), "clase_perdida"] == "Alta").mean())
    res["filas_sin_causa"] = int(d.driver_dominante.isna().sum())

    # validación aleatoria 10 pliegues estratificada (para comparar con la temporal)
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    xt = _matriz(d, NUM + CAT); yt = (d.clase_perdida == "Alta").astype(int)
    pa = cross_val_predict(_modelo("Random Forest"), xt, yt, cv=StratifiedKFold(5, shuffle=True, random_state=1), method="predict_proba")[:, 1]
    res["validacion_aleatoria_rf"] = dict(f1=f1_score(yt, (pa >= .5).astype(int)), accuracy=accuracy_score(yt, (pa >= .5).astype(int)), pliegues=5)

    # dónde falla el modelo elegido: por departamento (falsos negativos)
    nombre = res["elegido"]
    pr = (ajustados[nombre].predict_proba(xte)[:, 1] >= .5).astype(int)
    t2 = te.assign(real=yte.values, pred=pr)
    fn = t2[(t2.real == 1) & (t2.pred == 0)]
    res["falsos_negativos"] = int(len(fn))
    res["fn_muestra_perdida_mediana_ha"] = float(fn.perdida_ha.median())
    res["fn_perdida_t1_mediana_ha"] = float(fn.perdida_t1.median())
    res["fn_pct_t1_bajo_umbral"] = float((fn.perdida_t1 < umbral).mean())
    res["_te_predicciones"] = t2[["departamento", "municipio", "anio", "real", "pred"]]
    return res


if __name__ == "__main__":
    r = calcular()
    for n, m in r["modelos"].items():
        print(n, {k: round(v, 3) for k, v in m.items() if isinstance(v, float)})
    print(r["elegido"], r["baseline_persistencia"])
