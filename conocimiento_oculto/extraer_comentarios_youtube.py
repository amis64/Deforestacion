"""
Etapa 6 - Conocimiento Oculto: extracción y limpieza de comentarios de YouTube
(YouTube Data API v3). Solo biblioteca estándar de Python.

Propósito del análisis: conocer cómo percibe el público las CAUSAS de la
deforestación en Colombia (ganadería, coca, minería, incendios,
acaparamiento de tierras...) y compararlo con lo que muestran los datos
(driver dominante, transformación agropecuaria, focos de calor).

Credencial: NUNCA se escribe en el código ni se sube al repositorio.
    Linux/Mac:   export YOUTUBE_API_KEY="tu_clave"
    Windows:     set YOUTUBE_API_KEY=tu_clave        (cmd)
                 $env:YOUTUBE_API_KEY="tu_clave"     (PowerShell)

Uso:
    python conocimiento_oculto/extraer_comentarios_youtube.py
    (opcional) --videos-por-busqueda 5 --max-comentarios 500

Salidas en conocimiento_oculto/youtube/:
    videos.csv                 videos consultados (id, título, canal, enlace, fecha, n comentarios)
    comentarios_crudos.csv     todo lo extraído (sin nombre de autor)
    comentarios_limpios.csv    lo que se carga en Orange (columna "texto")
    reporte_extraccion.json    fecha, criterios, cuota usada, decisiones de limpieza y conteos
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://www.googleapis.com/youtube/v3/"
SALIDA = Path(__file__).resolve().parent / "youtube"

# Criterios de búsqueda: explícitos y documentables en el informe
BUSQUEDAS = [
    "deforestación Colombia Amazonía",
    "deforestación Caquetá Guaviare ganadería",
    "deforestación Colombia coca minería",
    "acaparamiento de tierras Amazonía colombiana",
    "incendios forestales Colombia deforestación",
]
PUBLICADO_DESPUES = "2018-01-01T00:00:00Z"  # periodo comparable con los datos
MIN_COMENTARIOS_VIDEO = 30                   # descartar videos sin conversación

cuota = {"unidades": 0}


def llamar(recurso, params, costo):
    params = dict(params, key=os.environ["YOUTUBE_API_KEY"])
    url = API + recurso + "?" + urllib.parse.urlencode(params)
    for intento in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                cuota["unidades"] += costo
                return json.load(r)
        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode("utf-8", "ignore")
            if e.code == 403 and "commentsDisabled" in cuerpo:
                return None  # comentarios desactivados en el video
            if e.code == 403 and "quotaExceeded" in cuerpo:
                sys.exit("Cuota diaria agotada (10.000 unidades). Intente mañana.")
            if intento == 2:
                raise RuntimeError(f"{e.code}: {cuerpo[:300]}")
            time.sleep(2 * (intento + 1))


def buscar_videos(consulta, n):
    r = llamar("search", {
        "part": "snippet", "q": consulta, "type": "video", "maxResults": n,
        "order": "relevance", "relevanceLanguage": "es", "regionCode": "CO",
        "publishedAfter": PUBLICADO_DESPUES,
    }, costo=100)
    return [i["id"]["videoId"] for i in r.get("items", [])]


def detalles_videos(ids):
    r = llamar("videos", {"part": "snippet,statistics", "id": ",".join(ids)}, costo=1)
    return r.get("items", [])


def comentarios(video_id, maximo):
    salida, token = [], None
    while len(salida) < maximo:
        params = {"part": "snippet", "videoId": video_id, "maxResults": 100,
                  "order": "relevance", "textFormat": "plainText"}
        if token:
            params["pageToken"] = token
        r = llamar("commentThreads", params, costo=1)
        if r is None:
            break
        for it in r.get("items", []):
            s = it["snippet"]["topLevelComment"]["snippet"]
            salida.append({
                "video_id": video_id,
                # id anonimizado: no se guarda nombre ni canal del autor
                "id_comentario": hashlib.sha256(it["id"].encode()).hexdigest()[:12],
                "texto": s.get("textOriginal", ""),
                "me_gusta": s.get("likeCount", 0),
                "respuestas": it["snippet"].get("totalReplyCount", 0),
                "fecha_publicacion": s.get("publishedAt", "")[:10],
            })
        token = r.get("nextPageToken")
        if not token:
            break
    return salida[:maximo]


# ---------------- limpieza ----------------
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_MENCION = re.compile(r"@\w+")
RE_TIEMPO = re.compile(r"\b\d{1,2}:\d{2}\b")
PALABRAS_ES = {"de", "la", "que", "el", "en", "y", "los", "se", "del", "las", "por", "un", "para",
               "con", "no", "una", "su", "al", "es", "lo", "como", "más", "pero", "sus", "le",
               "ya", "o", "este", "sí", "porque", "esta", "son", "hay", "muy", "todo", "nos"}
PALABRAS_EN = {"the", "and", "is", "are", "this", "that", "of", "to", "in", "it", "you", "for"}


def normalizar(t):
    t = unicodedata.normalize("NFKC", t)
    t = RE_URL.sub(" ", t)
    t = RE_MENCION.sub(" ", t)
    t = RE_TIEMPO.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


def idioma(t):
    w = re.findall(r"[a-záéíóúñü]+", t.lower())
    es, en = sum(x in PALABRAS_ES for x in w), sum(x in PALABRAS_EN for x in w)
    if es == 0 and en == 0:
        return "indeterminado"
    return "es" if es >= en else "en"


def limpiar(filas):
    motivos = {"vacio": 0, "muy_corto": 0, "solo_emojis_o_simbolos": 0,
               "duplicado": 0, "otro_idioma": 0, "spam_enlace": 0}
    vistos, limpios = set(), []
    for f in filas:
        original = f["texto"] or ""
        if not original.strip():
            motivos["vacio"] += 1
            continue
        if RE_URL.search(original) and len(RE_URL.sub("", original).split()) < 5:
            motivos["spam_enlace"] += 1
            continue
        t = normalizar(original)
        if not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{2,}", t):
            motivos["solo_emojis_o_simbolos"] += 1
            continue
        if len(t.split()) < 4:
            motivos["muy_corto"] += 1
            continue
        sin_tildes = "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")
        clave = re.sub(r"[^a-z0-9 ]", "", sin_tildes)
        if clave in vistos:
            motivos["duplicado"] += 1
            continue
        vistos.add(clave)
        lang = idioma(t)
        if lang == "en":
            motivos["otro_idioma"] += 1
            continue
        limpios.append(dict(f, texto=t, n_palabras=len(t.split()), idioma=lang))
    return limpios, motivos


def guardar(ruta, filas, campos):
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos-por-busqueda", type=int, default=5)
    ap.add_argument("--max-comentarios", type=int, default=500)
    a = ap.parse_args()
    if not os.environ.get("YOUTUBE_API_KEY"):
        sys.exit("Defina la variable de entorno YOUTUBE_API_KEY (ver encabezado del script).")
    SALIDA.mkdir(parents=True, exist_ok=True)
    fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")

    ids = []
    for q in BUSQUEDAS:
        for v in buscar_videos(q, a.videos_por_busqueda):
            if v not in ids:
                ids.append(v)

    videos, crudos = [], []
    for i in range(0, len(ids), 50):
        for v in detalles_videos(ids[i:i + 50]):
            n_coment = int(v["statistics"].get("commentCount", 0))
            if n_coment < MIN_COMENTARIOS_VIDEO:
                continue
            c = comentarios(v["id"], a.max_comentarios)
            videos.append({
                "video_id": v["id"],
                "titulo": v["snippet"]["title"],
                "canal": v["snippet"]["channelTitle"],
                "fecha_video": v["snippet"]["publishedAt"][:10],
                "enlace": f"https://www.youtube.com/watch?v={v['id']}",
                "comentarios_en_video": n_coment,
                "comentarios_extraidos": len(c),
            })
            for x in c:
                x["titulo_video"] = v["snippet"]["title"]
            crudos.extend(c)

    limpios, motivos = limpiar(crudos)
    guardar(SALIDA / "videos.csv", videos, list(videos[0].keys()) if videos else ["video_id"])
    campos = ["id_comentario", "video_id", "titulo_video", "fecha_publicacion", "me_gusta", "respuestas", "texto"]
    guardar(SALIDA / "comentarios_crudos.csv", crudos, campos)
    guardar(SALIDA / "comentarios_limpios.csv", limpios, campos + ["n_palabras", "idioma"])

    reporte = {
        "fecha_extraccion_utc": fecha,
        "busquedas": BUSQUEDAS,
        "filtros": {"publicado_despues": PUBLICADO_DESPUES, "idioma_relevancia": "es", "region": "CO",
                    "orden": "relevance", "min_comentarios_video": MIN_COMENTARIOS_VIDEO,
                    "max_comentarios_por_video": a.max_comentarios,
                    "solo_comentarios_principales": True},
        "videos_encontrados": len(ids),
        "videos_usados": len(videos),
        "comentarios_crudos": len(crudos),
        "comentarios_limpios": len(limpios),
        "descartados_por_motivo": motivos,
        "cuota_api_usada_unidades": cuota["unidades"],
        "privacidad": "No se guardan nombres, canales ni IDs originales de autores; id_comentario es un hash.",
    }
    (SALIDA / "reporte_extraccion.json").write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(reporte, indent=2, ensure_ascii=False))
    print("\nRevise videos.csv: elimine a mano los videos que no traten el tema y vuelva a ejecutar "
          "o filtre en Orange por video_id. Documente esa revisión en el informe.")


if __name__ == "__main__":
    main()
