# -*- coding: utf-8 -*-
"""Diagrama del modelo estrella en SVG (python multidimensional/diagrama.py escribe static/img/etapa5/modelo_estrella.svg)."""

import os
from html import escape

VERDE, MEDIO, CLARO, TIERRA, AMBAR, TEXTO = "#1f3a2e", "#3f6b4f", "#e7ede8", "#7a4f2b", "#c98a3a", "#222222"

DIMS = [
    ("dim_territorio", ["territorio_key (PK)", "nivel_analisis · escala", "region_natural", "departamento", "municipio", "latitud · longitud"],
     "H1: región → departamento → municipio", 20, 20),
    ("dim_tiempo", ["id_dim_tiempo (PK, AAAAMMDD)", "fecha", "anio · anio_fiscal", "semestre · cuatrimestre",
                    "trimestre · bimestre", "mes · mes_nombre(_corto)", "semana · semana_nombre",
                    "dia · dia_del_anio", "dia_semana (numero/nombre/corto)", "hora (NULL: grano diario)",
                    "es_periodo_pandemia", "es_anio_con_pandemia", "trienio · periodo (+ orden)"],
     "H2 análisis · H2b y H2c calendario", 800, 20),
    ("dim_causa", ["causa_key (PK)", "driver_dominante (causa)", "grupo_causa", "tipo_valor"],
     "H3: grupo de causa → causa", 20, 440),
    ("dim_transformacion", ["transformacion_key (PK)", "clase_transformacion", "tipo_valor"],
     "(un nivel)", 425, 470),
    ("dim_fuente", ["fuente_key (PK)", "fuente_origen", "n_fuentes", "incluye_gfw … incluye_owid (0/1)"],
     "H4: nº de fuentes → combinación", 800, 440),
]
FECHAS = [("territorio_key", 0), ("tiempo_key", 1), ("causa_key", 2), ("transformacion_key", 3), ("fuente_key", 4)]


def caja(x, y, w, titulo, lineas, nota, color, texto="#fff"):
    h = 34 + 20 * len(lineas) + (24 if nota else 8)
    s = ['<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="#fff" stroke="%s" stroke-width="2"/>' % (x, y, w, h, color),
         '<rect x="%d" y="%d" width="%d" height="28" rx="6" fill="%s"/>' % (x, y, w, color),
         '<text x="%d" y="%d" fill="%s" font-weight="bold" font-size="14">%s</text>' % (x + 10, y + 19, texto, escape(titulo))]
    for i, l in enumerate(lineas):
        s.append('<text x="%d" y="%d" fill="%s" font-size="12">%s</text>' % (x + 10, y + 48 + 20 * i, TEXTO, escape(l)))
    if nota:
        s.append('<text x="%d" y="%d" fill="%s" font-size="11" font-style="italic">%s</text>' % (x + 10, y + h - 9, TIERRA, escape(nota)))
    return "\n".join(s), h


def svg():
    partes = []
    cajas = {}
    for nombre, lineas, nota, x, y in DIMS:
        s, h = caja(x, y, 250, nombre, lineas, nota, MEDIO)
        cajas[nombre] = (x, y, 250, h)
        partes.append(s)
    hechos = ["territorio_key (PK, FK)", "tiempo_key (PK, FK)", "causa_key (FK)", "transformacion_key (FK)", "fuente_key (FK)",
              "n_registros_origen", "area_perdida_bosque_ha", "emisiones_co2_mg", "area_transformada_ha",
              "num_focos_calor", "frp_promedio · confianza_promedio_focos", "area_perdida_atipica · emisiones_atipicas"]
    fx, fy, fw = 330, 135, 340
    s, fh = caja(fx, fy, fw, "hechos_perdida_forestal", hechos, "Granularidad: territorio × año (1 de enero)", VERDE)
    # conexiones (antes de dibujar los hechos para quedar debajo)
    cx, cy = fx + fw / 2, fy + fh / 2
    lineas = []
    for nombre, (x, y, w, h) in cajas.items():
        px = x + w if x < fx else x
        py = y + h / 2 if y < fy + 100 else y + 20
        if nombre == "dim_transformacion":
            px, py = x + w / 2, y
            lineas.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (px, py, px, fy + fh, TIERRA))
            lineas.append('<text x="%d" y="%d" font-size="11" fill="%s">N : 1</text>' % (px + 6, py - 8, TIERRA))
            continue
        tx = fx if x < fx else fx + fw
        ty = fy + 60
        lineas.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (px, py, tx, ty + (0 if y < 200 else fh - 120), TIERRA))
        lx, ly = (px + tx) / 2, (py + ty + (0 if y < 200 else fh - 120)) / 2
        lineas.append('<rect x="%d" y="%d" width="34" height="16" fill="#f6f4ef"/><text x="%d" y="%d" font-size="11" fill="%s" text-anchor="middle">N : 1</text>' % (lx - 17, ly - 12, lx, ly, TIERRA))
    cuerpo = "\n".join(lineas) + "\n" + "\n".join(partes) + "\n" + s
    ancho, alto = 1080, 610
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
            'aria-label="Modelo estrella: tabla de hechos hechos_perdida_forestal con las dimensiones territorio, tiempo, causa, '
            'transformación del suelo y fuente" font-family="Arial, Helvetica, sans-serif">'
            '<rect width="%d" height="%d" fill="#f6f4ef"/>%s</svg>' % (ancho, alto, ancho, alto, ancho, alto, cuerpo))


if __name__ == "__main__":
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(raiz, "static", "img", "etapa5", "modelo_estrella.svg")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    open(ruta, "w", encoding="utf-8").write(svg())
    print("escrito", ruta)
