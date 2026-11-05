# -*- coding: utf-8 -*-
"""Registro de las vistas interactivas de la sección Análisis multidimensional."""

from . import v1, v2, v3, v4

VISTAS = [v1, v2, v3, v4]
POR_ID = {v.ID: v for v in VISTAS}
