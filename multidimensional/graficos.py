# -*- coding: utf-8 -*-
"""
graficos.py
===========
Gráficas SVG generadas en el servidor (sin librerías externas), a partir de
los resultados de las consultas. Cada gráfica trae título accesible (<title>)
con el valor exacto de cada marca y usa la paleta bosque/tierra del proyecto.
"""

from html import escape

PALETA = ["#1f3a2e", "#c98a3a", "#6aa27b", "#7a4f2b", "#4c6f8c", "#b5b35c", "#8d8d86", "#a65a5a", "#3f6b4f"]
TEXTO = "#222222"
SUAVE = "#55554f"
EJE = "#cfcabf"


def _num(v, dec=0):
    if v is None:
        return "—"
    s = "{:,.{d}f}".format(v, d=dec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _corta(t, n):
    t = str(t)
    return t if len(t) <= n else t[: n - 1] + "…"


def _svg(ancho, alto, cuerpo, descripcion):
    return ('<svg class="grafica" viewBox="0 0 %d %d" role="img" aria-label="%s" '
            'xmlns="http://www.w3.org/2000/svg" font-family="Arial, Helvetica, sans-serif" font-size="12">%s</svg>'
            % (ancho, alto, escape(descripcion, quote=True), cuerpo))


def vacio(mensaje="Sin datos para la selección actual."):
    return _svg(640, 60, '<text x="10" y="35" fill="%s">%s</text>' % (SUAVE, escape(mensaje)), mensaje)


def barras_h(items, unidad="", dec=0, color=None, referencia=None, etiqueta_ref="", colores=None, ancho=640):
    """items: [(etiqueta, valor)]. Barras horizontales con el valor al final."""
    items = [(e, v) for e, v in items if v is not None]
    if not items:
        return vacio()
    izq, der, alto_b, sep = 190, 110, 20, 8
    alto = 14 + len(items) * (alto_b + sep) + (22 if referencia else 8)
    maxv = max([abs(v) for _, v in items] + ([referencia] if referencia else [])) or 1
    area = ancho - izq - der
    c = []
    for i, (e, v) in enumerate(items):
        y = 10 + i * (alto_b + sep)
        w = max(1.0, abs(v) / maxv * area)
        col = (colores or {}).get(e) or color or PALETA[0]
        c.append('<text x="%d" y="%d" text-anchor="end" fill="%s">%s</text>' % (izq - 8, y + 14, TEXTO, escape(_corta(e, 30))))
        c.append('<rect x="%d" y="%d" width="%.1f" height="%d" fill="%s"><title>%s: %s %s</title></rect>'
                 % (izq, y, w, alto_b, col, escape(str(e)), _num(v, dec), escape(unidad)))
        c.append('<text x="%.1f" y="%d" fill="%s">%s</text>' % (izq + w + 6, y + 14, TEXTO, _num(v, dec)))
    if referencia:
        x = izq + referencia / maxv * area
        c.append('<line x1="%.1f" y1="4" x2="%.1f" y2="%d" stroke="%s" stroke-dasharray="4 3"/>' % (x, x, alto - 22, "#7a4f2b"))
        c.append('<text x="%.1f" y="%d" text-anchor="middle" fill="#7a4f2b">%s</text>' % (x, alto - 6, escape(etiqueta_ref)))
    c.insert(0, '<line x1="%d" y1="4" x2="%d" y2="%d" stroke="%s"/>' % (izq, izq, alto - (22 if referencia else 6), EJE))
    return _svg(ancho, alto, "".join(c), "Barras horizontales (%s)" % unidad)


def barras_divergentes(items, unidad="", dec=0, ancho=640):
    """items: [(etiqueta, valor)] con valores positivos (aumento) y negativos (disminución)."""
    items = [(e, v) for e, v in items if v is not None]
    if not items:
        return vacio()
    izq, der, alto_b, sep = 190, 20, 20, 8
    alto = 16 + len(items) * (alto_b + sep)
    mx = max(abs(v) for _, v in items) or 1
    mitad = (ancho - izq - der - 70) / 2
    cx = izq + 35 + mitad
    c = ['<line x1="%.1f" y1="4" x2="%.1f" y2="%d" stroke="%s"/>' % (cx, cx, alto - 4, SUAVE)]
    for i, (e, v) in enumerate(items):
        y = 10 + i * (alto_b + sep)
        w = max(1.0, abs(v) / mx * mitad)
        x = cx if v >= 0 else cx - w
        col = "#c98a3a" if v >= 0 else "#3f6b4f"
        c.append('<text x="%d" y="%d" text-anchor="end" fill="%s">%s</text>' % (izq - 8, y + 14, TEXTO, escape(_corta(e, 30))))
        c.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"><title>%s: %s%s %s</title></rect>'
                 % (x, y, w, alto_b, col, escape(str(e)), "+" if v > 0 else "", _num(v, dec), escape(unidad)))
        tx, anc = (x + w + 5, "start") if v >= 0 else (x - 5, "end")
        c.append('<text x="%.1f" y="%d" text-anchor="%s" fill="%s">%s%s</text>' % (tx, y + 14, anc, TEXTO, "+" if v > 0 else "", _num(v, dec)))
    return _svg(ancho, alto, "".join(c), "Barras divergentes (%s)" % unidad)


def barras_apiladas(filas, series, valores, porcentaje=True, ancho=640, colores=None):
    """filas: [etiqueta]; series: [nombre]; valores[(fila, serie)] = valor. Barras apiladas horizontales."""
    filas = [f for f in filas if sum((valores.get((f, s)) or 0) for s in series) > 0]
    if not filas:
        return vacio()
    series = [s for s in series if sum((valores.get((f, s)) or 0) for f in filas) > 0]
    izq, der, alto_b, sep = 190, 20, 22, 8
    alto = 14 + len(filas) * (alto_b + sep) + 30 + 18 * ((len(series) + 2) // 3)
    area = ancho - izq - der
    mx = max(sum((valores.get((f, s)) or 0) for s in series) for f in filas)
    col = {s: (colores or {}).get(s) or PALETA[i % len(PALETA)] for i, s in enumerate(series)}
    c = []
    for i, f in enumerate(filas):
        y = 10 + i * (alto_b + sep)
        tot = sum((valores.get((f, s)) or 0) for s in series)
        c.append('<text x="%d" y="%d" text-anchor="end" fill="%s">%s</text>' % (izq - 8, y + 15, TEXTO, escape(_corta(f, 30))))
        x = izq
        for s in series:
            v = valores.get((f, s)) or 0
            if v <= 0:
                continue
            w = v / (tot if porcentaje else mx) * area
            p = v / tot * 100
            c.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"><title>%s · %s: %s (%s %%)</title></rect>'
                     % (x, y, w, alto_b, col[s], escape(str(f)), escape(str(s)), _num(v), _num(p, 1)))
            if w > 38:
                c.append('<text x="%.1f" y="%d" text-anchor="middle" fill="#ffffff" font-size="11">%s</text>'
                         % (x + w / 2, y + 15, _num(p, 0) + " %"))
            x += w
    ly = 14 + len(filas) * (alto_b + sep) + 6
    for j, s in enumerate(series):
        lx = 10 + (j % 3) * ((ancho - 20) / 3)
        yy = ly + (j // 3) * 18
        c.append('<rect x="%.1f" y="%d" width="11" height="11" fill="%s"/>' % (lx, yy, col[s]))
        c.append('<text x="%.1f" y="%d" fill="%s" font-size="11">%s</text>' % (lx + 16, yy + 10, TEXTO, escape(_corta(s, 30))))
    return _svg(ancho, alto, "".join(c), "Barras apiladas")


def lineas(x_labels, series, unidad="", dec=0, ancho=640, alto=300):
    """series: {nombre: [valores alineados con x_labels]}."""
    series = {k: v for k, v in series.items() if any(x is not None for x in v)}
    if not series or not x_labels:
        return vacio()
    izq, der, arr, aba = 64, 44, 14, 56 + 18 * ((len(series) + 3) // 4)
    w, h = ancho - izq - der, alto - arr - aba
    mx = max(x for v in series.values() for x in v if x is not None) or 1
    n = len(x_labels)
    xs = [izq + (i * w / (n - 1) if n > 1 else w / 2) for i in range(n)]
    c = []
    for k in range(5):
        y = arr + h - h * k / 4
        c.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s"/>' % (izq, y, izq + w, y, EJE))
        c.append('<text x="%d" y="%.1f" text-anchor="end" fill="%s" font-size="11">%s</text>' % (izq - 6, y + 4, SUAVE, _num(mx * k / 4, dec)))
    paso = max(1, n // 12 + (1 if n > 12 else 0))
    for i, e in enumerate(x_labels):
        if i % paso == 0 or i == n - 1:
            c.append('<text x="%.1f" y="%d" text-anchor="middle" fill="%s" font-size="11">%s</text>' % (xs[i], arr + h + 16, SUAVE, escape(str(e))))
    for j, (nombre, vals) in enumerate(series.items()):
        col = PALETA[j % len(PALETA)]
        pts = [(xs[i], arr + h - (v / mx * h)) for i, v in enumerate(vals) if v is not None]
        if len(pts) > 1:
            c.append('<polyline fill="none" stroke="%s" stroke-width="2.2" points="%s"/>' % (col, " ".join("%.1f,%.1f" % p for p in pts)))
        for i, v in enumerate(vals):
            if v is not None:
                c.append('<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"><title>%s · %s: %s %s</title></circle>'
                         % (xs[i], arr + h - v / mx * h, col, escape(str(nombre)), escape(str(x_labels[i])), _num(v, dec), escape(unidad)))
        lx = izq + (j % 4) * (w / 4)
        ly = arr + h + 34 + (j // 4) * 18
        c.append('<rect x="%.1f" y="%d" width="11" height="11" fill="%s"/>' % (lx, ly, col))
        c.append('<text x="%.1f" y="%d" fill="%s" font-size="11">%s</text>' % (lx + 16, ly + 10, TEXTO, escape(_corta(nombre, 20))))
    c.append('<text x="%d" y="10" fill="%s" font-size="11">%s</text>' % (izq, SUAVE, escape(unidad)))
    return _svg(ancho, alto, "".join(c), "Gráfica de líneas (%s)" % unidad)
