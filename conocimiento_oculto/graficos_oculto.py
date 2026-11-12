# -*- coding: utf-8 -*-
"""Gráficos SVG propios de la Etapa 6 (curvas ROC y mapa de dispersión por grupo). Mismo estilo que multidimensional.graficos."""
import html

from multidimensional import graficos as g


def curvas_roc(modelos, ancho=520, alto=420):
    """modelos: {nombre: [[fpr, tpr], ...]}"""
    ml, mr, mt, mb = 52, 16, 14, 46
    w, h = ancho - ml - mr, alto - mt - mb
    c = []
    for t in (0, .25, .5, .75, 1):
        x, y = ml + t * w, mt + (1 - t) * h
        c.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1"/>' % (x, mt, x, mt + h, g.EJE))
        c.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>' % (ml, y, ml + w, y, g.EJE))
        c.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="11" fill="%s">%s</text>' % (x, mt + h + 16, g.SUAVE, ("%.2f" % t).rstrip("0").rstrip(".")))
        c.append('<text x="%d" y="%.1f" text-anchor="end" font-size="11" fill="%s">%s</text>' % (ml - 6, y + 4, g.SUAVE, ("%.2f" % t).rstrip("0").rstrip(".")))
    c.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-dasharray="4 4"/>' % (ml, mt + h, ml + w, mt, g.SUAVE))
    for i, (n, pts) in enumerate(modelos.items()):
        d = " ".join("%s%.1f,%.1f" % ("M" if j == 0 else "L", ml + p[0] * w, mt + (1 - p[1]) * h) for j, p in enumerate(pts))
        c.append('<path d="%s" fill="none" stroke="%s" stroke-width="2"/>' % (d, g.PALETA[[0, 1, 4][i % 3]]))
        c.append('<rect x="%d" y="%d" width="12" height="12" fill="%s"/><text x="%d" y="%d" font-size="12" fill="%s">%s</text>' % (ml + w - 170, mt + h - 70 + i * 18, g.PALETA[[0, 1, 4][i % 3]], ml + w - 153, mt + h - 60 + i * 18, g.TEXTO, html.escape(n)))
    c.append('<text x="%d" y="%d" text-anchor="middle" font-size="12" fill="%s">Tasa de falsos positivos</text>' % (ml + w / 2, alto - 6, g.SUAVE))
    c.append('<text x="14" y="%d" text-anchor="middle" font-size="12" fill="%s" transform="rotate(-90 14 %d)">Tasa de verdaderos positivos</text>' % (mt + h / 2, g.SUAVE, mt + h / 2))
    return g._svg(ancho, alto, "".join(c), "Curvas ROC de los tres modelos para la clase Alta")


def mapa_grupos(puntos, etiquetas, ancho=560, alto=560):
    """puntos: [[lon, lat, grupo]] (una coordenada puede repetirse: en el dataset la coordenada de la mayoría de los
    registros es la del departamento). Se dibuja un círculo dividido por grupo en cada ubicación distinta."""
    import math
    from collections import Counter, defaultdict
    lon = [p[0] for p in puntos]; lat = [p[1] for p in puntos]
    x0, x1, y0, y1 = min(lon), max(lon), min(lat), max(lat)
    ml, mr, mt, mb = 40, 200, 12, 30
    w, h = ancho - ml - mr, alto - mt - mb
    esc = min(w / (x1 - x0), h / (y1 - y0))
    col = {1: g.PALETA[7], 2: g.PALETA[1], 3: g.PALETA[2], 4: g.PALETA[4], 5: g.PALETA[5], 6: g.PALETA[3], 7: g.PALETA[6], 8: g.PALETA[0]}
    sitios = defaultdict(Counter)
    for lo, la, gr in puntos:
        sitios[(lo, la)][gr] += 1
    c = ['<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s"/>' % (ml, mt, (x1 - x0) * esc, (y1 - y0) * esc, g.EJE)]
    for (lo, la), cnt in sorted(sitios.items(), key=lambda t: -sum(t[1].values())):
        n = sum(cnt.values()); r = 4 + 1.1 * math.sqrt(n)
        cx, cy = ml + (lo - x0) * esc, mt + (y1 - la) * esc
        ang = -math.pi / 2
        for gr in sorted(cnt):
            fr = cnt[gr] / n
            if fr >= .999:
                c.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#fff" stroke-width=".8"><title>%d municipios del grupo %d</title></circle>' % (cx, cy, r, col[gr], cnt[gr], gr))
                break
            a2 = ang + fr * 2 * math.pi
            x_a, y_a, x_b, y_b = cx + r * math.cos(ang), cy + r * math.sin(ang), cx + r * math.cos(a2), cy + r * math.sin(a2)
            c.append('<path d="M%.1f,%.1f L%.1f,%.1f A%.1f,%.1f 0 %d 1 %.1f,%.1f Z" fill="%s" stroke="#fff" stroke-width=".8"><title>%d municipios del grupo %d</title></path>' % (cx, cy, x_a, y_a, r, r, 1 if fr > .5 else 0, x_b, y_b, col[gr], cnt[gr], gr))
            ang = a2
    for i, gno in enumerate(sorted(etiquetas)):
        c.append('<circle cx="%d" cy="%d" r="5" fill="%s"/><text x="%d" y="%d" font-size="12" fill="%s">%s</text>' % (ancho - mr + 14, mt + 20 + i * 22, col[gno], ancho - mr + 24, mt + 24 + i * 22, g.TEXTO, html.escape(etiquetas[gno])))
    c.append('<text x="%d" y="%d" text-anchor="middle" font-size="11" fill="%s">longitud</text>' % (ml + (x1 - x0) * esc / 2, alto - 8, g.SUAVE))
    c.append('<text x="12" y="%d" text-anchor="middle" font-size="11" fill="%s" transform="rotate(-90 12 %d)">latitud</text>' % (mt + (y1 - y0) * esc / 2, g.SUAVE, mt + (y1 - y0) * esc / 2))
    return g._svg(ancho, alto, "".join(c), "Municipios de cada grupo por ubicación (departamento)")
