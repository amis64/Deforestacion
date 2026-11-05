# -*- coding: utf-8 -*-
"""
conocimientos.py
================
Los ocho conocimientos multidimensionales (dos por vista), con los ocho
elementos que pide la rúbrica, más la limitación y la decisión de cada vista,
las limitaciones generales y las conclusiones.

Las cifras NO están escritas a mano: salen de cifras.calcular(), que las
consulta al modelo estrella. Cada conocimiento trae un enlace que reproduce
la selección (filtros y niveles) en la vista correspondiente.
"""

from urllib.parse import urlencode

from . import cifras

ANIOS_FIRMS = [str(a) for a in range(2012, 2023)]


def qs(*pares):
    return "?" + urlencode(pares)


def _conocimientos(c):
    return {
        # ------------------------------------------------------------------ V1
        "causas-por-territorio": [
            dict(
                id="K1.1", operaciones=["Drill-down", "Slice"],
                titulo="El patrón agrícola nacional se rompe en el Chocó",
                pregunta="¿El peso de la agricultura permanente (%(ap_nacional)s %% a escala nacional) se sostiene cuando se baja de la región a sus departamentos?",
                dimensiones="Territorio (región → departamento) × Causa (causa dominante). Medida: área perdida (ha).",
                procedimiento="Se partió de la matriz región × causa (sin filtros). Drill-down de Territorio de «región natural» a «departamento» y slice Región = Pacífica, que es la región con menor peso de la agricultura permanente. Los porcentajes se recalculan con el total de cada fila como denominador.",
                evidencia="Matriz departamento × causa de la vista 1 con el filtro Región = Pacífica (enlace). La celda Chocó × Agricultura permanente y el total de la fila Chocó; la misma consulta está en sql/06_consultas_olap.sql (C-03).",
                hallazgo="A escala nacional la agricultura permanente explica el %(ap_nacional)s %% del área perdida y supera el 90 %% en todas las regiones salvo la Pacífica (%(ap_pac)s %%). La brecha se concentra en el Chocó: allí la agricultura permanente es solo el %(choco_ap)s %% de %(dep_choco_total)s ha, la migratoria pesa %(choco_mig)s %% y los incendios forestales %(choco_inc)s %%, mientras que en Nariño la permanente vuelve a ser el %(narino_ap)s %%.",
                interpretacion="El «conocimiento evidente» de la Etapa 4 (la agricultura permanente domina) es cierto como promedio nacional, pero no describe al Chocó. La causa dominante cambia dentro de una misma región, por lo que una política pensada para el patrón nacional no encaja en este departamento.",
                utilidad="Orientar medidas diferenciadas por departamento: en el Chocó, control de la agricultura migratoria y de los incendios; en Nariño, de la agricultura permanente.",
                limitacion="La causa es la dominante del municipio-año según la fuente; no mide qué parte de cada hectárea se debe a cada causa y no prueba que la causa sea el origen. Es una asociación descriptiva.",
                enlace=("causas-por-territorio", qs(("n_territorio", "departamento"), ("n_causa", "causa"), ("f_region", "Pacífica"))),
                selecciona="Nivel Territorio = departamento · Nivel Causa = causa dominante · Región = Pacífica"),
            dict(
                id="K1.2", operaciones=["Dice", "Drill-down"],
                titulo="Un solo año de incendios en el Chocó explica más de la mitad de la pérdida por incendios del país",
                pregunta="¿Dónde y cuándo se concentra la pérdida atribuida a incendios forestales?",
                dimensiones="Territorio (departamento) × Tiempo (año) × Causa = Incendios forestales. Medida: área perdida (ha).",
                procedimiento="Dice con dos filtros sobre dimensiones distintas: Causa = Incendios forestales (dimensión Causa) y Región = Pacífica (dimensión Territorio); drill-down de Tiempo de periodo a año. El total nacional de incendios se obtiene con la misma consulta sin el filtro de región.",
                evidencia="Matriz departamento × año de la vista 1 con los dos filtros (enlace): celda Chocó × 2016 frente al total de la fila Chocó y al total de la causa en el país (%(inc_pais)s ha).",
                hallazgo="Los incendios forestales suman %(inc_pais)s ha en el país (%(inc_pais_pct)s %% de la pérdida). Solo el Chocó en 2016 aporta %(inc_choco_2016)s ha: el %(inc_choco_2016_pct_pais)s %% de esa causa en 24 años y el %(inc_choco_2016_pct_choco)s %% de toda la pérdida del Chocó. Esas hectáreas son el %(inc_choco_2016_pct_pac_p2)s %% de los incendios de toda la región Pacífica en 2013–2024. En 2019 el mismo departamento tuvo %(inc_choco_2019)s ha. Por eso la proporción de causas naturales en la región Pacífica pasó de %(nat_pac_p1)s %% (2001–2012) a %(nat_pac_p2)s %% (2013–2024).",
                interpretacion="La causa «incendios» no es un fenómeno distribuido en el tiempo sino un evento puntual en un territorio. El cambio de composición de la Pacífica entre periodos no refleja un aumento gradual de las causas naturales sino un episodio concentrado.",
                utilidad="Tratar el episodio 2016 del Chocó como caso para verificar con la fuente y con información de campo antes de usar la serie en proyecciones; no extrapolar la tendencia de la causa «incendios».",
                limitacion="No se puede concluir qué ocurrió en 2016: el modelo solo muestra que el valor existe y está concentrado. Que sea un evento real, un cambio de detección o un error de atribución es una hipótesis que requiere validación externa.",
                enlace=("causas-por-territorio", qs(("n_territorio", "departamento"), ("n_tiempo", "anio"), ("eje_c", "tiempo"), ("f_region", "Pacífica"), ("f_causa", "Incendios forestales"))),
                selecciona="Nivel Territorio = departamento · Nivel Tiempo = año · Región = Pacífica · Causa = Incendios forestales · columnas = Tiempo"),
        ],
        # ------------------------------------------------------------------ V2
        "cambio-en-el-tiempo": [
            dict(
                id="K2.1", operaciones=["Roll-up", "Drill-down"],
                titulo="Cuatro departamentos concentran el %(cuatro_pct_bruto)s %% de los aumentos de la pérdida anual",
                pregunta="¿Quién explica el aumento de la pérdida anual entre 2001–2012 y 2013–2024?",
                dimensiones="Tiempo (periodo de 12 años) × Territorio (región → departamento). Medida: pérdida promedio anual (ha/año).",
                procedimiento="Primero la matriz región × periodo (nivel general) y se calcula el cambio de cada región. Luego drill-down a departamento. La medida es SUM(ha)/COUNT(DISTINCT año), que compara periodos de igual duración; el cambio porcentual usa como denominador el promedio de 2001–2012. Al volver a región (roll-up) la medida se recalcula, no se suman promedios.",
                evidencia="Vista 2, nivel departamento (enlace): columnas «Cambio (ha/año)» y «Cambio (%%)» de Caquetá, Guaviare, Putumayo y Meta; y nivel región para la Amazonía.",
                hallazgo="El promedio anual nacional pasa de %(nac_p1)s a %(nac_p2)s ha/año (+%(nac_var)s %%, +%(nac_neto)s ha/año). La Amazonía aporta +%(r_amaz_dif)s ha/año (+%(r_amaz_var)s %%), el %(amaz_aporte)s %% del aumento neto; la Andina (−%(r_andina_dif)s) y la Pacífica (−%(r_pac_dif)s) bajan. Por departamento, %(n_dep_suben)s de %(n_dep)s aumentan (+%(bruto_sube)s ha/año en total) y el resto baja (−%(bruto_baja)s ha/año). Caquetá (+%(d_caq_dif)s), Guaviare (+%(d_guav_dif)s), Putumayo (+%(d_put_dif)s) y Meta (+%(d_meta_dif)s) suman el %(cuatro_pct_bruto)s %% de los aumentos y el %(cuatro_dep_aporte)s %% del aumento neto (los descensos restan al neto).",
                interpretacion="El aumento nacional del %(nac_var)s %% no es un fenómeno parejo: combina aumentos muy altos en pocos departamentos (Putumayo +%(d_put_var)s %%, Guaviare +%(d_guav_var)s %%), aumentos menores en otros y descensos en la zona Andina y la Pacífica que lo compensan en parte. La Etapa 4 mostraba el promedio; aquí aparece de dónde viene.",
                utilidad="Priorizar el seguimiento en el arco Caquetá–Guaviare–Putumayo–Meta, que concentra la mayor parte del aumento, sin descuidar los otros departamentos que también suben (p. ej. Bolívar y Norte de Santander).",
                limitacion="Es un cambio de promedios entre dos periodos; no identifica el momento ni la causa, y el %(cuatro_dep_aporte)s %% es una proporción del aumento NETO (los descensos restan) y el %(cuatro_pct_bruto)s %% lo es de los aumentos brutos; ninguno es una participación en la pérdida total.",
                enlace=("cambio-en-el-tiempo", qs(("n_territorio", "departamento"), ("top", "20"))),
                selecciona="Nivel Territorio = departamento · Nivel Tiempo = periodo · sin filtros · 20 filas con mayor pérdida"),
            dict(
                id="K2.2", operaciones=["Pivot", "Drill-down"],
                titulo="El salto de 2016–2018 fue simultáneo en todas las regiones; la divergencia aparece después",
                pregunta="¿El aumento ocurre en un momento puntual o es gradual, y se comporta igual en todas las regiones?",
                dimensiones="Tiempo (trienio) × Territorio (región). Medida: pérdida promedio anual (ha/año).",
                procedimiento="Drill-down de Tiempo de periodo a trienio y pivot para dejar los trienios en las filas y las regiones en las columnas, lo que permite leer cada región como una serie. Se comparan trienios de tres años completos entre sí.",
                evidencia="Vista 2 con nivel de Tiempo = trienio y pivot activo (enlace); filas 2013–2015 y 2016–2018 y filas 2010–2012 y 2022–2024.",
                hallazgo="Entre 2013–2015 y 2016–2018 el promedio anual nacional pasa de %(tri_1315)s a %(tri_1618)s ha/año (×%(tri_salto)s) y todas las regiones se multiplican por un factor entre %(sal_min)s y %(sal_max)s. En cambio, entre 2010–2012 y 2022–2024 la Amazonía sube %(t_amaz_var)s %%, la Orinoquía %(t_orin_var)s %% y el Caribe %(t_caribe_var)s %%, mientras la Andina baja %(t_andina_var)s %% y la Pacífica %(t_pac_var)s %%.",
                interpretacion="El salto de 2016–2018 es común a todas las regiones, lo que apunta a un factor que actuó a escala nacional (o a un cambio en la detección) y no a dinámicas regionales. La diferencia entre regiones se construye en la trayectoria posterior. La Etapa 4 ya señalaba 2016–2018; aquí se separa lo común de lo regional.",
                utilidad="Para evaluar políticas o proyecciones, distinguir el choque común de 2016–2018 de las tendencias propias de cada región y no atribuir a una región un salto que fue nacional.",
                limitacion="El modelo no contiene variables de política, mercado o conflicto, así que no puede explicar el salto; cualquier explicación es una hipótesis. Un cambio en el método de detección de la fuente produciría un patrón similar.",
                enlace=("cambio-en-el-tiempo", qs(("n_tiempo", "trienio"), ("pivot", "1"))),
                selecciona="Nivel Tiempo = trienio · Pivot activo (filas = trienio, columnas = región)"),
        ],
        # ------------------------------------------------------------------ V3
        "intensidad-de-emisiones": [
            dict(
                id="K3.1", operaciones=["Pivot"],
                titulo="Una hectárea perdida en la Amazonía emite 45 %% más que en el Caribe, incluso con la misma causa",
                pregunta="¿La diferencia de emisiones por hectárea entre regiones se debe a que pierden bosque por causas distintas?",
                dimensiones="Territorio (región) × Causa (causa dominante). Medidas: intensidad (Mg CO₂e/ha), con el área como base.",
                procedimiento="Matriz región × causa con la medida intensidad, definida como SUM(emisiones)/SUM(área) sobre filas con área > 0; se recalcula en cada celda y en cada total (nunca se promedian las intensidades). Se comparan celdas de la misma causa entre regiones: así se controla el efecto de la composición de causas.",
                evidencia="Vista 3, ejes Territorio × Causa, medida Intensidad (enlace). Fila Amazonía y fila Caribe; columna Agricultura permanente.",
                hallazgo="La intensidad nacional es %(int_nac)s Mg CO₂e/ha. La Amazonía tiene %(int_amaz)s y el Caribe %(int_caribe)s (+%(int_amaz_vs_caribe)s %%). Solo para agricultura permanente: Amazonía %(int_ap_amaz)s frente a Caribe %(int_ap_caribe)s (+%(int_ap_dif)s %%). Dentro de la Amazonía la agricultura migratoria (%(int_mig_amaz)s) apenas supera a la permanente (+%(int_mig_vs_ap)s %%).",
                interpretacion="La correlación de 0,998 entre área y emisiones de la Etapa 4 ocultaba que la relación no es la misma en todas partes. La diferencia entre regiones persiste dentro de una misma causa, de modo que depende del lugar (hipótesis: contenido de carbono del bosque que se pierde) más que de la causa.",
                utilidad="Al estimar emisiones a partir de hectáreas perdidas, usar un factor regional y no un factor único nacional: aplicar %(int_nac)s a la Amazonía subestimaría sus emisiones.",
                limitacion="Las emisiones vienen estimadas por la fuente, no medidas; la intensidad refleja su método. Que la diferencia se deba al carbono del bosque es una hipótesis. Las filas con 0 ha (por redondeo) se excluyen del cociente.",
                enlace=("intensidad-de-emisiones", qs(("eje_f", "territorio"), ("eje_c", "causa"), ("medida", "intensidad"))),
                selecciona="Filas = Territorio (región) · Columnas = Causa (causa dominante) · medida = Intensidad"),
            dict(
                id="K3.2", operaciones=["Pivot"],
                titulo="El vacío de información sobre la transformación del suelo es un vacío geográfico",
                pregunta="¿Dónde se concentra la pérdida cuya transformación del suelo no se conoce?",
                dimensiones="Territorio (región) × Transformación del suelo (clase). Medida: área perdida (ha).",
                procedimiento="Matriz región × clase con la medida área. «Sin clase informada» se trata como categoría desconocida (no como «no hubo transformación» ni como cero) y se calcula su peso con la pérdida de cada región como denominador.",
                evidencia="Vista 3, ejes Territorio × Transformación, medida Área perdida (enlace); columna «Sin clase informada». La equivalencia con la ausencia de MapBiomas se comprueba en sql/06_consultas_olap.sql (C-09).",
                hallazgo="%(sc_ha)s ha (%(sc_pct)s %% de la pérdida) no tienen clase de transformación. Pesan %(sc_orin)s %% en la Orinoquía y %(sc_amaz)s %% en la Amazonía, frente a %(sc_andina)s %% en la Andina y %(sc_caribe)s %% en el Caribe; la Amazonía y la Orinoquía reúnen el %(sc_amaz_orin_pct)s %% de ese vacío. Toda esa pérdida (%(sc_sin_mapbiomas)s ha) proviene de registros que no incluyen la fuente MapBiomas.",
                interpretacion="El faltante no es aleatorio: coincide con dónde la cobertura de MapBiomas no llega a los registros. Los hallazgos sobre «qué se transforma» son más débiles justo en las regiones de mayor aumento de la pérdida (ver K2.1).",
                utilidad="Priorizar la integración de una fuente de cobertura para la Amazonía y la Orinoquía antes de usar la transformación del suelo como variable explicativa, y reportar siempre el peso de «Sin clase informada».",
                limitacion="No se puede inferir qué transformación ocurrió en esa pérdida. Que el vacío dependa de la fuente (y no de la naturaleza del cambio) es lo que muestran los datos; por qué MapBiomas no cubre esos registros queda fuera del modelo.",
                enlace=("intensidad-de-emisiones", qs(("eje_f", "territorio"), ("eje_c", "transformacion"), ("medida", "area"))),
                selecciona="Filas = Territorio (región) · Columnas = Transformación del suelo · medida = Área perdida"),
        ],
        # ------------------------------------------------------------------ V4
        "focos-y-fuentes": [
            dict(
                id="K4.1", operaciones=["Drill-down"],
                titulo="Por cada hectárea perdida hay seis veces más focos de calor en la Orinoquía que en la Amazonía",
                pregunta="¿La relación débil entre focos de calor y pérdida (r = 0,48 en la Etapa 4) es pareja entre regiones?",
                dimensiones="Territorio (región → departamento) × Tiempo (trienio). Medida: focos por 100 ha perdidas, con focos y área como base.",
                procedimiento="Se calcula la razón 100·SUM(focos)/SUM(área) con área solo de los territorio-año que tienen focos registrados (denominador explícito), por región y trienio; luego drill-down a departamento. La razón se recalcula en cada nivel.",
                evidencia="Vista 4, matriz región × trienio (enlace); fila Orinoquía y Amazonía, y drill-down a departamento con la medida «Focos por 100 ha».",
                hallazgo="El promedio nacional es %(f100_nac)s focos por 100 ha perdidas, pero la Orinoquía llega a %(f100_orin)s y el Caribe a %(f100_caribe)s, frente a %(f100_andina)s en la Andina, %(f100_pac)s en la Pacífica y %(f100_amaz)s en la Amazonía (la Orinoquía es %(f100_orin_vs_amaz)s veces la Amazonía). Orinoquía y Caribe tienen el %(focos_orin_caribe_pct)s %% de los %(focos_total)s focos pero solo el %(orin_caribe_area_pct)s %% de la pérdida. Dentro de la Orinoquía, Vichada alcanza %(f100_vichada)s focos/100 ha; en la Amazonía, Putumayo solo %(f100_putumayo)s.",
                interpretacion="La relación débil entre focos y pérdida es un promedio de situaciones distintas: en la Orinoquía y el Caribe hay muchos focos por hectárea perdida y en la Amazonía y la Pacífica pocos (hipótesis: en las sabanas el fuego es una práctica frecuente poco ligada a la pérdida de bosque). Los focos no sirven por igual como señal de deforestación en todo el país.",
                utilidad="Usar los focos de calor como alerta temprana solo donde la razón es alta y estable (Orinoquía y Caribe); en la Amazonía complementar con otras fuentes (imágenes, alertas de cobertura).",
                limitacion="Un foco de calor no es una hectárea deforestada ni un incendio confirmado; la razón es una asociación espacial y anual, no causal. Que en la selva se queme menos tras la tala es una hipótesis.",
                enlace=("focos-y-fuentes", qs(("n_territorio", "region"), ("n_tiempo", "trienio"))),
                selecciona="Nivel Territorio = región · Nivel Tiempo = trienio · sin filtros (bajar a departamento con el control de nivel)"),
            dict(
                id="K4.2", operaciones=["Roll-up", "Pivot"],
                titulo="Los resultados por periodo no son comparables sin mirar qué fuentes cubren cada año",
                pregunta="¿Cuánta de la pérdida está documentada por las tres fuentes y esa cobertura es igual en el tiempo y en las regiones?",
                dimensiones="Fuente (número de fuentes) × Tiempo (periodo) y Territorio (región) × Fuente. Medida: área perdida (ha) y pérdida con focos registrados.",
                procedimiento="Matriz número de fuentes × periodo con la medida área (denominador: pérdida de cada periodo). Roll-up de Fuente de «combinación» a «número de fuentes» y de Tiempo de trienio a periodo. Para la cobertura de FIRMS se usa la ventana 2012–2022 (años con FIRMS) con filtro de año y las dimensiones Región × Fuente, midiendo la cobertura de focos como pérdida con focos registrados dividida entre la pérdida de la región.",
                evidencia="Vista 4, ejes Fuente × Tiempo con la medida área (enlace). Para la cobertura de FIRMS: medida «Pérdida con focos registrados» y «Área perdida» con los filtros Año 2012–2022 (ver sql/06_consultas_olap.sql, C-12).",
                hallazgo="La pérdida con tres fuentes pasa de %(tres_p1)s %% (%(tres_ha_p1)s ha) en 2001–2012 a %(tres_p2)s %% (%(tres_ha_p2)s ha) en 2013–2024. En 2012–2022 la fuente de focos cubre el %(cob_firms_nac)s %% de la pérdida nacional, pero solo el %(cob_pac)s %% en la Pacífica y el %(cob_orin)s %% en la Orinoquía, frente al %(cob_caribe)s %% del Caribe y el %(cob_amaz)s %% de la Amazonía.",
                interpretacion="Las variables de focos, clase de transformación y emisiones no existen con la misma cobertura en todos los años ni en todas las regiones. Comparar 2001–2012 con 2013–2024 en medidas que dependen de más fuentes mezcla cambios de fenómeno con cambios de cobertura.",
                utilidad="Acompañar cada indicador con su cobertura (porcentaje de pérdida con la fuente) y comparar periodos solo con medidas que existan en ambos, como el área de la fuente principal.",
                limitacion="El número de fuentes describe qué bases aportaron al registro, no su calidad. No se sabe si en 2001–2012 hubo menos fenómeno o menos observación; los datos solo muestran la cobertura.",
                enlace=("focos-y-fuentes", qs(("eje_f", "fuente"), ("eje_c", "tiempo"), ("n_fuente", "n_fuentes"), ("n_tiempo", "periodo"), ("medida", "area"))),
                selecciona="Filas = Fuente (número de fuentes) · Columnas = Tiempo (periodo) · medida = Área perdida"),
        ],
    }


def _por_vista(c):
    return {
        "causas-por-territorio": dict(
            limitacion="La causa es una sola por municipio-año (la dominante según la fuente) y no cuantifica el aporte de cada causa; hay %(sin_causa_ha)s ha sin causa informada, un valor mínimo que no altera los porcentajes. El área está redondeada a hectárea entera y los porcentajes cambian al cambiar el nivel porque cada uno usa su propio denominador.",
            decision="Diseñar el seguimiento por departamento y no con un único patrón nacional: en la región Pacífica, el Chocó (agricultura migratoria %(choco_mig)s %%, incendios %(choco_inc)s %%, minería %(choco_min)s %%) necesita medidas distintas de las de Nariño (agricultura permanente %(narino_ap)s %%)."),
        "cambio-en-el-tiempo": dict(
            limitacion="El promedio por periodo oculta la variación entre años, y un cambio en el método de detección de la fuente produciría un efecto parecido al de un cambio real. La Insular tiene casi 0 ha y no se interpreta.",
            decision="Priorizar el monitoreo en Caquetá, Guaviare, Putumayo y Meta, que concentran el %(cuatro_pct_bruto)s %% de los aumentos (%(cuatro_dep_aporte)s %% del aumento neto), y revisar con la fuente si el salto común de 2016–2018 (×%(tri_salto)s) refleja un cambio real o de detección antes de usarlo en proyecciones."),
        "intensidad-de-emisiones": dict(
            limitacion="Las emisiones son estimaciones de la fuente y la intensidad se calcula solo con filas de área > 0 (el área está redondeada a hectárea entera). %(sc_pct)s %% de la pérdida no tiene clase de transformación, de modo que las celdas «Sin clase informada» son una categoría desconocida y no una transformación nula. Las celdas con menos de 1.000 ha de base se marcan como poco confiables.",
            decision="Estimar emisiones con una intensidad regional (Amazonía %(int_amaz)s, Caribe %(int_caribe)s Mg CO₂e/ha) en lugar de la nacional (%(int_nac)s), y priorizar la incorporación de cobertura de transformación en la Amazonía y la Orinoquía."),
        "focos-y-fuentes": dict(
            limitacion="Los focos solo existen entre 2012 y 2022; un valor ausente no es cero focos y la ventana no cubre todos los años de la pérdida. Los porcentajes de cobertura tienen como denominador la pérdida de 2012–2022 de la selección. La razón focos/100 ha es una asociación, no una causa.",
            decision="Usar los focos como alerta temprana únicamente en regiones con razón alta y cobertura suficiente (Orinoquía %(f100_orin)s y Caribe %(f100_caribe)s focos/100 ha), y reportar siempre la cobertura de la fuente junto a cualquier comparación entre periodos."),
    }


# ---------------------------------------------------------------------------
# Relación con la Etapa 4: qué hallazgo evidente se profundiza y dónde
# ---------------------------------------------------------------------------
def _relacion_etapa4(c):
    return [
        dict(evidente="La agricultura permanente explica la mayor parte de los registros (Etapa 4, página poblacional).",
             pregunta="¿Se sostiene en cada región y departamento?", vista="causas-por-territorio",
             nuevo="Territorio × Causa con drill-down: el Chocó (%(choco_ap)s %% agricultura permanente) rompe el patrón nacional (%(ap_nacional)s %%)." % c),
        dict(evidente="2013–2024 pierde más bosque por año que 2001–2012, con el salto en 2016–2018 (Etapa 4, página temporal).",
             pregunta="¿Quién explica el aumento y cuándo?", vista="cambio-en-el-tiempo",
             nuevo="Tiempo × Territorio: la Amazonía aporta el %(amaz_aporte)s %% del aumento neto y el salto 2016–2018 es común a todas las regiones." % c),
        dict(evidente="Área perdida y emisiones se mueven casi igual, r = 0,998 (Etapa 4, página multivariada).",
             pregunta="¿Cada hectárea emite lo mismo en todas partes?", vista="intensidad-de-emisiones",
             nuevo="Causa × Transformación × Territorio: la Amazonía emite %(int_amaz_vs_caribe)s %% más por hectárea que el Caribe." % c),
        dict(evidente="Los focos de calor se relacionan débilmente con la pérdida, r = 0,48 (Etapa 4, página multivariada).",
             pregunta="¿Es pareja esa relación y con qué cobertura de fuentes?", vista="focos-y-fuentes",
             nuevo="Fuente × Tiempo × Territorio: la Orinoquía tiene %(f100_orin)s focos/100 ha y la Amazonía %(f100_amaz)s." % c),
    ]


def _generales(c):
    limitaciones = [
        "Unidad de análisis y granularidad. La unidad de análisis es el municipio-año (el departamento-año y el país-año en las otras dos escalas). El dataset tratado tiene %(n_registros)s registros; el modelo los consolida en %(n_hechos)s filas de hechos (una por territorio y año), porque varios registros describen el mismo municipio-año con distintas fuentes. El número de registros de origen se conserva en la medida «Registros de origen».",
        "Escalas que no se mezclan. Las escalas municipal, departamental y país contienen la misma pérdida ya agregada; sumarlas la multiplicaría. Todas las vistas usan la escala municipal (%(n_municipios)s territorios) y la agregación a departamento y región se hace desde ella.",
        "Área redondeada. El área perdida está en hectáreas enteras, de modo que hay municipio-años con 0 ha y emisiones positivas; la intensidad solo usa filas con área > 0.",
        "Faltantes y categorías desconocidas. Los faltantes de medidas se conservan como nulos (no como 0). «Sin clase informada» (%(sc_pct)s %% de la pérdida) y «Sin causa informada» son categorías desconocidas; «No aplica» identifica registros de escalas donde la dimensión no tiene sentido.",
        "Cobertura desigual de las fuentes. Los focos de calor solo existen en 2012–2022 y la clase de transformación depende de MapBiomas, por lo que las comparaciones entre periodos de esas medidas no son equivalentes.",
        "Región natural. La región se asigna a cada departamento por convención (agrupación de uso común); los límites naturales no coinciden exactamente con los departamentales.",
        "Asociación no es causalidad. Ningún conocimiento demuestra causas; las explicaciones que no se pueden comprobar con los datos se presentan como hipótesis.",
        "Diferencia con la Etapa 4. El +22,6 %% de la Etapa 4 se reproduce exactamente sumando todas las filas del dataset sin consolidar (las tres escalas, que contienen la misma pérdida, y las copias de cada territorio-año). El modelo usa una sola escala y una fila por territorio-año y obtiene +%(var_modelo)s %%, igual al que resulta con la escala departamental (+%(var_dep)s %%) y la de país (+%(var_pais)s %%). El porcentaje cambia poco, pero las hectáreas absolutas calculadas sin consolidar quedan sobrestimadas varias veces (ver comprobación B3).",
    ]
    conclusiones = [
        "El patrón «evidente» de la Etapa 4 es un promedio que no describe a todos los territorios: el Chocó no sigue el patrón agrícola nacional y la Amazonía y la Orinoquía no se comportan como el resto del país.",
        "El aumento de la pérdida está concentrado: la Amazonía aporta el %(amaz_aporte)s %% del aumento neto y cuatro departamentos (Caquetá, Guaviare, Putumayo y Meta) el %(cuatro_pct_bruto)s %% de los aumentos, mientras la zona Andina y la Pacífica disminuyen.",
        "El salto de 2016–2018 fue simultáneo en todas las regiones; las diferencias regionales se construyen después.",
        "La intensidad de emisiones depende de la región más que de la causa; los cálculos de emisiones deben usar factores regionales.",
        "La calidad y cobertura de los datos no es uniforme (transformación del suelo, focos, número de fuentes) y condiciona qué comparaciones son válidas; el modelo permite verlo y reportarlo con cada cifra.",
        "Para el propósito del proyecto —entender la pérdida de bosque y la transformación del territorio— el análisis multidimensional pasa de describir el país a priorizar territorios, causas y fuentes concretas.",
    ]
    return limitaciones, conclusiones


RELACION_NOTA = (
    "El informe de Power BI de la Etapa 4 (páginas Poblacional, Territorial, Temporal y Multivariada, con 12 "
    "conocimientos evidentes) describió el fenómeno sobre este mismo dataset tratado. Aquí se profundiza en los cuatro "
    "que dejaban una pregunta abierta. Los demás se usan como reglas de cálculo o ya quedan resueltos en la Etapa 4: "
    "que 80.585 registros no son 80.585 territorios (por eso el modelo guarda una fila por territorio-año), que los "
    "blancos de clase y de causa son faltantes por cobertura y no respuestas negativas (por eso se tratan como "
    "«Sin … informada», distinto de «No aplica»), y la concentración territorial y la comparación Colombia–mundo.")


def todos():
    """Devuelve (por_vista, relacion_etapa4, limitaciones, conclusiones) ya con las cifras sustituidas."""
    c = cifras.calcular()
    conoc = _conocimientos(c)
    for lista in conoc.values():
        for k in lista:
            for campo in ("titulo", "pregunta", "dimensiones", "procedimiento", "evidencia", "hallazgo",
                          "interpretacion", "utilidad", "limitacion"):
                k[campo] = (k[campo] % c).replace("%%", "%")
    pv = _por_vista(c)
    for v in pv.values():
        for campo in ("limitacion", "decision"):
            v[campo] = v[campo] % c
    lim, con = _generales(c)
    lim = [t % c for t in lim]
    con = [t % c for t in con]
    return conoc, pv, _relacion_etapa4(c), lim, con
