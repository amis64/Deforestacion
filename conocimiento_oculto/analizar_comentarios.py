# -*- coding: utf-8 -*-
"""
Verificación en Python del análisis de comentarios de YouTube (flujo 3 de Orange, Etapa 6).

Entrada : youtube/comentarios_limpios.csv, youtube/videos.csv, youtube/reporte_extraccion.json
          (los produce extraer_comentarios_youtube.py; son los archivos que carga Orange)
Salida  : resultados/comentarios.json  (lo lee la página «Comentarios de YouTube» de Flask)

Qué calcula (equivale a los widgets del flujo):
  - términos relevantes (TF-IDF)                 ~ Bag of Words (TF-IDF)
  - temas (NMF, 5 temas)                         ~ Topic Modelling (LDA, 5 temas)
  - agrupación de comentarios (Ward + silueta)   ~ Distances (coseno) + Hierarchical Clustering
  - familias de términos y ejemplos citables     ~ Corpus Viewer / Word Enrichment
Orange usa LDA (gensim) y su propio preprocesamiento; los temas pueden salir distintos. Valen los de Orange.
"""
import json
import os
import re
import unicodedata
import scikit-learn as sklearn
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

AQUI = os.path.dirname(os.path.abspath(__file__))
YT = os.path.join(AQUI, "youtube")
SALIDA = os.path.join(AQUI, "resultados", "comentarios.json")

PV = set("""de la que el en y a los se del las un por con no una su para es al lo como mas pero sus le ya o este si porque esta entre
cuando muy sin sobre tambien me hasta hay donde quien desde todo nos durante todos uno les ni contra otros ese eso ante ellos e esto
antes algunos que unos yo otro otras otra el tanto esa estos mucho nada muchos cual poco ella estar estas algunas algo nosotros mi
mis tu te ti tus ellas son esta fue han ser tiene hacer pueden video videos gracias q pa vez solo asi cada ahi aqui ven vamos va
puede hace hacen estan estamos era eran sea tan bien muy mas menos ver nos les lo la le se si ha he voy vine""".split())

# familias de términos (se buscan en el texto sin tildes y en minúsculas); cada comentario puede estar en varias
FAMILIAS = [
    ("gobierno", "Gobierno, autoridades y corrupción", r"gobiern|president|estado|autoridad|politic|corrupci|congreso|entidades|ministerio|leyes?\b"),
    ("ganaderia", "Ganadería y pastos", r"ganader|ganado|pastos|potrero|pasturas"),
    ("coca_conflicto", "Coca, grupos armados y actividades ilegales", r"coca\b|cocal|guerrill|ilegal|armad|narco"),
    ("extractivas", "Minería, megaproyectos y monocultivos", r"miner|extraccion|extractor|megaproyecto|petrole|palma|monocultiv|empresas"),
    ("tala_fuego", "Tala, quemas e incendios", r"\btala|talador|quema|incendi|madera"),
    ("pueblos", "Pueblos indígenas y comunidades rurales", r"indigen|nativ|campesin"),
    ("propuestas", "Propuestas: reforestar, vigilar o sancionar", r"reforest|sembr|plantand|plantar|guardia|ejercito|mano dura|delito|sancion|castig|arboles"),
    ("humanidad", "La culpa es del ser humano en general", r"human|hombre|plaga|raza|nosotros|nuestra culpa"),
    ("emocion", "Tristeza o indignación", r"triste|tristeza|dolor|lastima|pena\b|duele|apocalipsis|tragedia|pobre"),
    ("escolar", "Uso escolar del video (tarea, exposición, proyecto)", r"tarea|exposicion|expo\b|proyecto|resumen|sinopsis|me sirvio|me ayudo|me ayudaste|trabajo"),
]
TERRITORIOS = [("Amazonía / Caquetá / Guaviare", r"amazon|caqueta|guaviare"), ("Otras regiones de Colombia", r"darien|colombia\b|putumayo|choco"),
               ("Otros países", r"guatemala|peru\b|republica dominicana|venezuela|brasil")]


def sin_tildes(t):
    t = unicodedata.normalize("NFD", str(t).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def recorta(t, n=240):
    t = re.sub(r"\s+", " ", str(t)).strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def calcular():
    d = pd.read_csv(os.path.join(YT, "comentarios_limpios.csv"))
    v = pd.read_csv(os.path.join(YT, "videos.csv"))
    rep = json.load(open(os.path.join(YT, "reporte_extraccion.json"), encoding="utf-8"))
    d["fecha"] = pd.to_datetime(d.fecha_publicacion, errors="coerce")
    d["norm"] = d.texto.map(sin_tildes)
    corto = {r.video_id: "V%d" % (i + 1) for i, r in enumerate(v.itertuples())}

    videos = []
    for r in v.itertuples():
        videos.append(dict(codigo=corto[r.video_id], video_id=r.video_id, titulo=r.titulo, canal=r.canal, fecha_video=r.fecha_video,
                           enlace=r.enlace, comentarios_en_video=int(r.comentarios_en_video), extraidos=int(r.comentarios_extraidos),
                           utiles=int((d.video_id == r.video_id).sum())))
    res = dict(
        extraccion=dict(fecha_utc=rep["fecha_extraccion_utc"], busquedas=rep["busquedas"], filtros=rep["filtros"],
                        videos_encontrados=rep["videos_encontrados"], videos_usados=rep["videos_usados"], crudos=rep["comentarios_crudos"],
                        limpios=rep["comentarios_limpios"], descartados=rep["descartados_por_motivo"], cuota=rep["cuota_api_usada_unidades"]),
        videos=videos,
        resumen=dict(n=int(len(d)), mediana_palabras=float(d.n_palabras.median()), me_gusta_total=int(d.me_gusta.sum()),
                     fecha_min=str(d.fecha.min().date()), fecha_max=str(d.fecha.max().date()),
                     por_anio={str(k): int(x) for k, x in d.fecha.dt.year.value_counts().sort_index().items()}),
    )

    # términos (TF-IDF)
    vec = TfidfVectorizer(preprocessor=sin_tildes, stop_words=sorted(PV), token_pattern=r"[a-z]{3,}", ngram_range=(1, 1), min_df=3, max_df=0.5, sublinear_tf=True)
    X = vec.fit_transform(d.texto)
    voc = np.array(vec.get_feature_names_out())
    docf = np.asarray((X > 0).sum(axis=0)).ravel()
    pes = np.asarray(X.sum(axis=0)).ravel()
    top = np.argsort(-pes)[:20]
    res["terminos"] = [dict(termino=voc[i], comentarios=int(docf[i])) for i in top]

    # temas (NMF, 5)
    nm = NMF(5, init="nndsvda", random_state=0, max_iter=800).fit(X)
    W = nm.transform(X)
    tema = W.argmax(axis=1)
    temas = []
    for t in range(5):
        idx = np.where(tema == t)[0]
        mejores = idx[np.argsort(-W[idx, t])][:2]
        temas.append(dict(tema=t + 1, palabras=[voc[i] for i in np.argsort(-nm.components_[t])[:7]], comentarios=int(len(idx)),
                          pct=float(len(idx) / len(d)), ejemplos=[recorta(d.texto.iloc[i], 200) for i in mejores]))
    res["temas"] = temas

    # agrupación de comentarios (Ward sobre TF-IDF normalizado; equivale a distancia coseno)
    Xn = normalize(X).toarray()
    comp = []
    for k in range(2, 9):
        lab = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(Xn)
        comp.append(dict(k=k, silueta=float(silhouette_score(Xn, lab, metric="cosine")), minimo=int(np.bincount(lab).min())))
    k = max((c for c in comp if c["minimo"] >= 5), key=lambda c: c["silueta"])["k"]
    lab = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(Xn)
    grupos = []
    for g in range(k):
        idx = np.where(lab == g)[0]
        cen = np.asarray(X[idx].mean(axis=0)).ravel()
        grupos.append(dict(grupo=g + 1, comentarios=int(len(idx)), pct=float(len(idx) / len(d)), palabras=[voc[i] for i in np.argsort(-cen)[:6]],
                           ejemplo=recorta(d.texto.iloc[idx[np.argmax(X[idx].dot(cen))]], 200)))
    grupos.sort(key=lambda x: -x["comentarios"])
    for i, g in enumerate(grupos):
        g["grupo"] = i + 1
    res["agrupacion"] = dict(comparacion=comp, k_elegido=int(k), grupos=grupos)

    # familias de términos y evidencias
    fam = []
    for clave, nombre, patron in FAMILIAS:
        m = d.norm.str.contains(patron, regex=True)
        sel = d[m].sort_values(["me_gusta", "n_palabras"], ascending=False)
        fam.append(dict(clave=clave, nombre=nombre, comentarios=int(m.sum()), pct=float(m.mean()),
                        por_video={corto[a]: int(m[d.video_id == a].sum()) for a in v.video_id},
                        ejemplos=[dict(video=corto[r.video_id], me_gusta=int(r.me_gusta), texto=recorta(r.texto, 260)) for r in sel.head(3).itertuples()]))
    res["familias"] = fam
    esc = d.norm.str.contains(FAMILIAS[-1][2], regex=True)
    causal = d.norm.str.contains("|".join(f[2] for f in FAMILIAS[:6]), regex=True)
    res["uso"] = dict(escolar=int(esc.sum()), escolar_pct=float(esc.mean()), con_causa_o_actor=int(causal.sum()), con_causa_o_actor_pct=float(causal.mean()),
                      sin_causa_ni_escolar=int((~causal & ~esc).sum()),
                      por_video={corto[a]: dict(causa_pct=float(causal[d.video_id == a].mean()), escolar_pct=float(esc[d.video_id == a].mean()),
                                                n=int((d.video_id == a).sum())) for a in v.video_id})
    res["territorios"] = [dict(nombre=n, comentarios=int(d.norm.str.contains(p, regex=True).sum())) for n, p in TERRITORIOS]
    res["sesgos"] = [
        "Solo se leyeron %d comentarios principales de %d videos (los más relevantes según YouTube, no una muestra aleatoria)." % (len(d), len(v)),
        "Quien comenta no representa a la población: hay estudiantes que usan el video para una tarea y personas de otros países.",
        "Las respuestas a los comentarios no se extrajeron; el orden «relevancia» favorece los comentarios con más interacción.",
        "El idioma se detectó con una heurística de palabras funcionales; quedan comentarios fuera de tema que el filtro automático no detecta.",
    ]
    return res


def main():
    r = calcular()
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    print("comentarios:", r["resumen"]["n"], "| temas:", [" ".join(t["palabras"][:4]) for t in r["temas"]])
    print("k:", r["agrupacion"]["k_elegido"], [round(c["silueta"], 3) for c in r["agrupacion"]["comparacion"]])
    print([(f["clave"], f["comentarios"]) for f in r["familias"]], r["uso"]["escolar"], r["uso"]["con_causa_o_actor"])


if __name__ == "__main__":
    main()
