# -*- coding: utf-8 -*-
"""
contenido.py
============
Contenido de texto y datos estructurados de la Etapa 1 del proyecto de
Minería de Datos: "Deforestación y Transformación del Territorio".

Se separa del resto de la aplicación para que app.py se limite a definir
rutas y renderizar plantillas, y para que actualizar el contenido de una
etapa no implique tocar la lógica de la aplicación.
"""

PROYECTO = {
    "nombre": "Deforestación y Transformación del Territorio",
    "etapa": "Etapa 1 · Del problema a los datos",
}

# ---------------------------------------------------------------------------
# 1. Problema y contexto
# ---------------------------------------------------------------------------
PROBLEMA = {
    "intro": (
        "Entre 2001 y 2025, cerca de una tercera parte de la pérdida mundial de "
        "cobertura arbórea registrada por sensores satelitales no correspondió a "
        "un ciclo natural de tala y regeneración, sino a un cambio permanente en "
        "el uso del suelo: el bosque no vuelve a crecer porque el terreno pasó a "
        "cumplir otra función (agrícola, ganadera, minera o urbana). Esa proporción "
        "se duplica cuando se observa únicamente el bosque tropical primario. El "
        "dato importa porque separa dos fenómenos que suelen confundirse bajo la "
        "misma palabra: la pérdida de árboles y la transformación del territorio "
        "que ocupaban. Este proyecto se ocupa de esa segunda capa del problema."
    ),
    "global": (
        "A escala mundial, el monitoreo satelital coordinado por el World "
        "Resources Institute y la Universidad de Maryland (Global Forest Watch) "
        "permite rastrear la pérdida de cobertura arbórea año a año desde el "
        "2000, y desde 2025 incorpora un modelo de aprendizaje profundo capaz de "
        "atribuir esa pérdida a una causa dominante (agricultura, incendios, "
        "silvicultura, urbanización, minería). Más del 90% de la deforestación "
        "mundial se concentra en el cinturón tropical, lo que convierte a países "
        "como Colombia, Brasil, Indonesia o la República Democrática del Congo en "
        "los puntos de mayor interés analítico."
    ),
    "nacional": (
        "En Colombia, el IDEAM reportó 113.608 hectáreas deforestadas en 2024, "
        "la segunda cifra más baja en dos décadas, y parte de una reducción "
        "acumulada del 39% frente a la línea base de 2021 (174.103 ha). Sin "
        "embargo, el fenómeno está lejos de distribuirse uniformemente: cinco "
        "departamentos concentran más del 60% de la deforestación nacional, y "
        "tres de ellos (Caquetá, Guaviare y Putumayo) pertenecen al llamado "
        "\"arco de la deforestación\" amazónico, junto con Meta y Antioquia. "
        "Entender qué ocurre en esos territorios específicos importa tanto como "
        "conocer la cifra nacional agregada."
    ),
    "regional": (
        "A nivel regional el proyecto pone atención particular en la Amazonía "
        "colombiana, donde coexisten dinámicas de expansión de la frontera "
        "agropecuaria, ganadería extensiva, minería y construcción de vías no "
        "planificadas, factores que la literatura identifica como los "
        "principales motores de transformación del territorio en la región, y "
        "que los sistemas de monitoreo nacional (SINCHI, IDEAM) y colaborativo "
        "(MapBiomas) documentan con distintos niveles de detalle geográfico y "
        "temporal."
    ),
    "delimitacion": (
        "El proyecto delimita el problema a la relación entre pérdida de "
        "cobertura boscosa y transformación del uso del suelo en Colombia entre "
        "2001 y 2024, comparando el comportamiento nacional y regional contra el "
        "panorama global, y usando como evidencia series satelitales y "
        "estadísticas oficiales ya sistematizadas, en vez de captura de datos de "
        "campo propia. Las tres escalas no se tratan como secciones "
        "independientes: se definen como niveles de un mismo fenómeno que deben "
        "poder compararse entre sí, y por eso el dataset consolidado conserva "
        "para cada una la misma variable de pérdida de bosque (hectáreas/año) "
        "con idéntica definición operativa."
    ),
    "comparacion_escalas_metodologia": (
        "La comparación entre escalas se apoya en tres criterios explícitos: "
        "(1) la unidad de análisis, que pasa de país (Global) a departamento "
        "(Nacional) y a municipio (Regional) sin cambiar de variable; "
        "(2) la métrica común, hectáreas de pérdida de bosque por año, que "
        "permite calcular la participación de una escala dentro de la "
        "inmediatamente superior (por ejemplo, qué porcentaje de la pérdida "
        "nacional se concentra en un departamento del arco de la "
        "deforestación); y (3) la fuente que respalda cada nivel, documentada "
        "explícitamente en la ficha de cada fuente de datos (ver sección "
        "Fuentes de datos) para que cualquier comparación entre escalas pueda "
        "rastrearse hasta el origen de cada cifra."
    ),
    "conocimiento_esperado": (
        "Se espera poder caracterizar en qué medida la pérdida de bosque "
        "observada corresponde a una transformación duradera del territorio "
        "(y hacia qué uso), identificar qué departamentos y municipios "
        "concentran el fenómeno, relacionar la actividad de quemas detectada "
        "por satélite con las causas reportadas de pérdida, y establecer un "
        "punto de comparación entre la magnitud del fenómeno en Colombia y la "
        "tendencia mundial, como insumo para las etapas posteriores de "
        "minería de datos (asociación, clustering geográfico y modelos "
        "predictivos)."
    ),
}

# ---------------------------------------------------------------------------
# 2. Pregunta principal y secundarias
# ---------------------------------------------------------------------------
PREGUNTA_PRINCIPAL = (
    "¿En qué medida la pérdida de cobertura boscosa registrada en Colombia "
    "entre 2001 y 2024 corresponde a procesos de transformación del uso del "
    "suelo, y cómo se compara ese comportamiento entre las escalas global, "
    "nacional y regional?"
)

PREGUNTAS_SECUNDARIAS = [
    {
        "pregunta": (
            "¿Cómo se compara la evolución de la pérdida de bosque y las "
            "emisiones de carbono asociadas en los departamentos del arco de "
            "la deforestación (Caquetá, Guaviare, Putumayo, Meta y Antioquia) "
            "frente al promedio nacional?"
        ),
        "orienta": "Variables de pérdida (ha) y emisiones por departamento-año; comparación entre subgrupo y agregado nacional.",
    },
    {
        "pregunta": (
            "¿Qué proporción de la cobertura perdida corresponde efectivamente "
            "a una transformación hacia uso agropecuario u otro uso antrópico, "
            "y qué proporción no tiene una clase de transformación identificada "
            "en las fuentes disponibles?"
        ),
        "orienta": "Cruce entre pérdida de bosque (GFW) y clase de cobertura resultante (MapBiomas) por municipio-año.",
    },
    {
        "pregunta": (
            "¿Existe correspondencia entre la actividad de quemas detectada por "
            "sensores satelitales y las causas de pérdida de bosque reportadas "
            "(agricultura, incendios, minería) a nivel municipal?"
        ),
        "orienta": "Focos de calor (FIRMS) agregados por municipio-año, cruzados con el driver dominante de GFW.",
    },
    {
        "pregunta": (
            "¿Cómo se ubica Colombia frente a otros países con bosque tropical "
            "en cuanto al porcentaje de su territorio cubierto por bosque, según "
            "los indicadores oficiales reportados a Naciones Unidas?"
        ),
        "orienta": "Indicador ODS 15.1.1 (FAO) por país-año, y comparación con la serie de Our World in Data.",
    },
    {
        "pregunta": (
            "¿En qué departamentos la reducción reciente de la deforestación "
            "reportada oficialmente coincide con una reducción similar en la "
            "actividad satelital observada, y en cuáles hay una divergencia que "
            "valga la pena investigar más adelante?"
        ),
        "orienta": "Comparación temporal 2021-2024 entre la cifra oficial (IDEAM/GFW) y los indicadores satelitales derivados (FIRMS, MapBiomas).",
    },
]

# ---------------------------------------------------------------------------
# 3. Necesidades de información
# ---------------------------------------------------------------------------
NECESIDADES = {
    "entidades": [
        ("Unidades geográficas", "Países, departamentos y municipios de Colombia, y comparativos internacionales."),
        ("Eventos de quema", "Detecciones puntuales de focos de calor (satélite VIIRS)."),
        ("Clases de cobertura del suelo", "Categorías de uso/cobertura antes y después de la pérdida de bosque."),
        ("Series oficiales internacionales", "Reportes país-año de organismos como FAO."),
    ],
    "variables": [
        ("Pérdida de cobertura arbórea (ha/año)", "Es la medida directa del fenómeno central del proyecto."),
        ("Emisiones de carbono asociadas", "Traduce la pérdida física a un indicador de impacto climático."),
        ("Causa dominante de pérdida (driver)", "Explica el 'por qué', no solo el 'cuánto'."),
        ("Clase de cobertura/uso resultante", "Es la variable que distingue deforestación de mera pérdida temporal: el corazón de la 'transformación del territorio'."),
        ("Focos de calor (conteo, intensidad, confianza)", "Proxy de actividad de quema, una de las causas reportadas."),
        ("Porcentaje y hectáreas de área forestal por país", "Permite comparación internacional oficial."),
        ("Coordenadas / jerarquía geográfica", "Habilita el análisis espacial y la comparación entre escalas."),
        ("Año de observación", "Habilita el análisis de tendencia, que es la pregunta central del proyecto."),
    ],
    "periodo": "2001-2024 como ventana principal (limitada a 2012-2022 para la variable de focos de calor, por disponibilidad de la fuente).",
    "cobertura_geografica": "Mundial para el punto de comparación; Colombia a nivel de departamento y municipio para el análisis nacional y regional, con foco en los departamentos del arco de la deforestación.",
    "poblacion": "Unidad geográfica-año (país-año, departamento-año, municipio-año), no personas ni eventos individuales salvo en el caso de los focos de calor.",
    "granularidad": "El municipio es la unidad más fina disponible de forma sistemática; los focos de calor ofrecen resolución puntual pero se agregan a esa misma unidad para poder cruzarlos con el resto.",
    "comparacion_escalas": (
        "Las variables de pérdida de bosque, emisiones y porcentaje de área "
        "forestal están disponibles con la misma definición a nivel país, "
        "departamento y municipio, lo que permite comparar directamente las "
        "tres escalas sin tener que homologar unidades distintas."
    ),
}

# ---------------------------------------------------------------------------
# 4. Fuentes de datos
# ---------------------------------------------------------------------------
FUENTES = [
    {
        "nombre": "Global Forest Watch: Country dashboard (Colombia)",
        "institucion": "World Resources Institute (WRI), en colaboración con la Universidad de Maryland (GLAD lab) y Google DeepMind",
        "url": "https://globalnaturewatch.org/dashboards/country/COL/?map=eyJjYW5Cb3VuZCI6dHJ1ZX0%3D",
        "tipo": "Secundaria",
        "nivel": "Global, Nacional, Regional",
        "rol_por_nivel": (
            "Global: aporta el punto de comparación dentro del cinturón "
            "tropical mundial; Nacional: se agrega por departamento para "
            "contrastarse contra la cifra oficial del IDEAM; Regional: llega "
            "hasta el municipio, la granularidad que sostiene el análisis "
            "del arco de la deforestación."
        ),
        "cobertura_geografica": "Mundial (nivel país); Colombia a nivel departamento y municipio",
        "periodo": "2001-2025 (pérdida de cobertura); 2001-2024 (atribución de causa/driver)",
        "formato": "Excel (.xlsx) multi-hoja descargado desde el panel de país",
        "metodo_adquisicion": "Descarga directa desde el dashboard de país de globalforestwatch.org",
        "registros_aprox": "Decenas de miles tras integrar país + departamento + municipio × año",
        "variables_disponibles": "Hectáreas de pérdida de cobertura arbórea, emisiones de carbono, causa dominante de pérdida, umbral de densidad de dosel",
        "fecha_consulta": "Agosto de 2026",
        "restricciones": "Acceso abierto; se solicita atribución a WRI/Global Forest Watch",
        "justificacion": (
            "Es la única fuente que ofrece la misma métrica de pérdida de bosque "
            "con definición homogénea en las tres escalas del proyecto, lo que la "
            "convierte en el eje de integración del resto de fuentes."
        ),
    },
    {
        "nombre": "MapBiomas Colombia: Estadísticas de cobertura y uso del suelo",
        "institucion": "Red MapBiomas Colombia (iniciativa regional con participación de instituciones colombianas de monitoreo ambiental)",
        "url": "https://colombia.mapbiomas.org/en/estadisticas/",
        "tipo": "Secundaria",
        "nivel": "Nacional, Regional",
        "rol_por_nivel": (
            "Nacional: distribuye por departamento la clase de cobertura "
            "resultante tras la pérdida de bosque; Regional: llega hasta el "
            "municipio, el nivel donde se decide si la transformación fue "
            "hacia uso agropecuario u otra categoría."
        ),
        "cobertura_geografica": "Colombia: país, departamento, municipio, bioma y cuenca",
        "periodo": "1985-2024 (se usa el subconjunto 2001-2024 para alinear con GFW)",
        "formato": "Excel (.xlsx) multi-hoja",
        "metodo_adquisicion": "Descarga de estadísticas agregadas desde el sitio web del proyecto",
        "registros_aprox": "Miles de combinaciones municipio × clase de cobertura × año",
        "variables_disponibles": "Área (ha) por clase de cobertura/uso del suelo (jerarquía de dos niveles), por año",
        "fecha_consulta": "Agosto de 2026",
        "restricciones": "Datos públicos y abiertos; se solicita citar a la Red MapBiomas",
        "justificacion": (
            "Es la fuente que permite distinguir hacia qué categoría de uso del "
            "suelo se transforma el territorio una vez perdido el bosque; la "
            "clasificación se obtiene mediante interpretación de imágenes Landsat "
            "con algoritmos de aprendizaje automático (Random Forest) sobre "
            "Google Earth Engine, con validación cruzada frente a fuentes de alta "
            "resolución."
        ),
    },
    {
        "nombre": "NASA FIRMS: Detecciones activas de fuego (VIIRS/Suomi-NPP)",
        "institucion": "NASA (Fire Information for Resource Management System)",
        "url": "https://firms.modaps.eosdis.nasa.gov/country/",
        "tipo": "Primaria",
        "nivel": "Regional",
        "rol_por_nivel": (
            "Regional exclusivamente: su valor está en la ubicación puntual "
            "del foco de calor, que solo tiene sentido analítico una vez se "
            "cruza espacialmente con el municipio; no se reporta a nivel "
            "nacional ni global en este proyecto."
        ),
        "cobertura_geografica": "Colombia (recorte del feed satelital global)",
        "periodo": "2012-2022",
        "formato": "CSV, un archivo por año",
        "metodo_adquisicion": "Descarga de archivo histórico (Archive Download) desde el portal FIRMS",
        "registros_aprox": "Decenas de miles de detecciones puntuales por año, agregadas por municipio-año tras el cruce espacial",
        "variables_disponibles": "Latitud, longitud, fecha, potencia radiativa del fuego (FRP), nivel de confianza de la detección",
        "fecha_consulta": "Agosto de 2026",
        "restricciones": "Uso público; NASA aclara que su uso no implica respaldo institucional al proyecto que la use",
        "justificacion": (
            "Es la única fuente primaria del proyecto en sentido estricto: "
            "observación directa por sensor (VIIRS, resolución de 375 m), sin "
            "procesamiento intermedio por terceros, útil como evidencia "
            "independiente de la actividad de quema reportada por otras fuentes."
        ),
    },
    {
        "nombre": "FAO: Indicador ODS 15.1.1 (proporción de superficie forestal)",
        "institucion": "Organización de las Naciones Unidas para la Alimentación y la Agricultura (FAO)",
        "rol_por_nivel": (
            "Global: incluye agregados por continente y grupo de ingreso "
            "que dan contexto internacional; Nacional: dentro de esa misma "
            "serie aparece la cifra oficial de Colombia, comparable "
            "directamente contra el resto de países."
        ),
        "url": "https://de-public-statsuite.fao.org/vis?fs[0]=Sustainable%20Development%20Goals%20%28SDGs%29,1%7CGoal%2015%20Life%20on%20Land%23SDG_G15%23%7C15.1.1%20Forest%20area%23SDG_G15_1511%23&pg=0&fc=Sustainable%20Development%20Goals%20%28SDGs%29&bp=true&snb=1&vw=ov&df[ds]=ds-release&df[id]=DF_SDG_15_1_1&df[ag]=FAO&df[vs]=1.0&dq=A...........&pd=2015,2025&to[TIME_PERIOD]=false",
        "tipo": "Terciaria",
        "nivel": "Global, Nacional",
        "cobertura_geografica": "Mundial, por país (incluye Colombia y agregados globales)",
        "periodo": "Serie histórica del Global Forest Resources Assessment",
        "formato": "Excel (.xlsx), una serie distinta por hoja",
        "metodo_adquisicion": "Descarga desde el portal de datos de los Objetivos de Desarrollo Sostenible de la FAO",
        "registros_aprox": "Cientos de combinaciones país-año-serie",
        "variables_disponibles": "Porcentaje de área forestal, área forestal en hectáreas, área total de tierra",
        "fecha_consulta": "Agosto de 2026",
        "restricciones": "Dominio público; se solicita citar a FAO",
        "justificacion": (
            "Al integrar los reportes oficiales que cada país presenta a Naciones "
            "Unidas, ofrece el punto de comparación internacional más "
            "estandarizado disponible para contrastar a Colombia contra otros "
            "países con bosque tropical."
        ),
    },
    {
        "nombre": "Our World in Data: Deforestación anual",
        "institucion": "Our World in Data (Universidad de Oxford / Global Change Data Lab)",
        "rol_por_nivel": (
            "Global exclusivamente: sirve como serie país-año de contraste "
            "frente a GFW; no está disponible con desagregación "
            "departamental ni municipal, por lo que no aporta a los niveles "
            "Nacional ni Regional."
        ),
        "url": "https://ourworldindata.org/grapher/annual-deforestation",
        "tipo": "Terciaria",
        "nivel": "Global",
        "cobertura_geografica": "Mundial, por país/entidad",
        "periodo": "Variable según país, alineada con la disponibilidad de FAO",
        "formato": "CSV",
        "metodo_adquisicion": "Descarga directa desde el explorador de datos de Our World in Data",
        "registros_aprox": "Miles de combinaciones país-año",
        "variables_disponibles": "Deforestación anual (hectáreas)",
        "fecha_consulta": "Agosto de 2026",
        "restricciones": "Licencia CC BY; requiere atribución a Our World in Data y a la fuente primaria original",
        "justificacion": (
            "Sirve como serie de contraste independiente frente a las cifras de "
            "GFW: si ambas divergen de forma importante para un mismo país-año, "
            "es una señal a investigar en el diagnóstico de calidad."
        ),
    },
    {
        "nombre": "DANE: Marco Geoestadístico Nacional (capa de municipios)",
        "institucion": "Departamento Administrativo Nacional de Estadística (DANE)",
        "rol_por_nivel": (
            "Nacional: define los límites departamentales usados para "
            "agregar FIRMS a esa escala; Regional: define los límites "
            "municipales, la unidad base de todo el cruce espacial del "
            "proyecto."
        ),
        "url": "https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/datos-geoestadisticos/",
        "tipo": "Primaria",
        "nivel": "Nacional, Regional",
        "cobertura_geografica": "Colombia, los 1.122 municipios del país",
        "periodo": "Versión vigente del Marco Geoestadístico Nacional",
        "formato": "Shapefile (.shp + archivos complementarios)",
        "metodo_adquisicion": "Descarga desde el geoportal oficial del DANE",
        "registros_aprox": "≈1.122 polígonos, uno por municipio",
        "variables_disponibles": "Nombre y código oficial de departamento y municipio, geometría del polígono",
        "fecha_consulta": "Agosto de 2026",
        "restricciones": "Información pública oficial del Estado colombiano, de libre uso",
        "justificacion": (
            "No es en sí misma una fuente del fenómeno de deforestación, sino la "
            "base cartográfica que permite asignar cada detección puntual de "
            "FIRMS al municipio correspondiente mediante un cruce espacial "
            "punto-en-polígono, integrándola con el resto de fuentes tabulares."
        ),
    },
]

FUENTES_DOCUMENTADAS_PENDIENTES = [
    {
        "nombre": "SIATAC (SINCHI): Pérdida de bosque, Amazonía colombiana",
        "tipo": "Primaria",
        "url": "https://datos.siatac.co/pages/coberturas",
        "nota": (
            "Capas vectoriales oficiales de monitoreo de la Amazonía colombiana. "
            "Quedan documentadas para la caracterización de fuentes, pero su "
            "integración cuantitativa se deja para una etapa posterior por el "
            "procesamiento geoespacial adicional que requieren."
        ),
    },
    {
        "nombre": "SIATAC (SINCHI): Degradación de bosque, Amazonía colombiana",
        "tipo": "Primaria",
        "url": "https://datos.siatac.co/pages/coberturas",
        "nota": "Misma plataforma que la fuente anterior, capa de fragmentación/degradación en vez de pérdida; pendiente de integración cuantitativa.",
    },
    {
        "nombre": "IDEAM: Geovisor de Bosques de Colombia",
        "tipo": "Primaria",
        "url": "https://www.ideam.gov.co/sala-de-prensa/noticia/abc-del-geovisor-de-datos-y-estadisticas-del-monitoreo-de-bosques-del-ideam",
        "nota": "Boletines y capas oficiales a nivel departamental y por Corporación Autónoma Regional; pendiente de integración cuantitativa.",
    },
    {
        "nombre": "Bosque No Bosque 10K (datos.gov.co / IDEAM)",
        "tipo": "Primaria",
        "url": "https://www.datos.gov.co/dataset/Bosque-No-Bosque-10K-2023-SI/gcty-vkv4/about_data",
        "nota": "Capa vectorial binaria de alta resolución; útil como validación cualitativa, pendiente de integración cuantitativa.",
    },
    {
        "nombre": "Hansen Global Forest Change",
        "tipo": "Primaria",
        "url": "https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/download.html",
        "nota": "Insumo satelital original detrás de buena parte de GFW, en formato ráster (.tif); requiere procesamiento geoespacial adicional.",
    },
]

# ---------------------------------------------------------------------------
# 5. Dataset
# ---------------------------------------------------------------------------
DATASET = {
    "resumen": (
        "El dataset consolidado se construye con un script reproducible "
        "(build_dataset.py, incluido como anexo técnico del proyecto) que lee "
        "las fuentes anteriores, las lleva a un formato largo (una fila por "
        "unidad geográfica-año-fuente) y las cruza mediante llaves geográficas "
        "(país, departamento, municipio) y temporales (año), normalizando los "
        "nombres de lugar para que coincidan aunque las fuentes originales usen "
        "mayúsculas, tildes o abreviaciones distintas."
    ),
    "cifras": [
        ("Registros consolidados", "88.513 filas"),
        ("Variables totales", "20"),
        ("Variables numéricas", "11"),
        ("Variables categóricas", "7"),
        ("Variable temporal", "Año de observación (2001-2024)"),
        ("Variables geográficas", "País / departamento / municipio, y coordenadas (latitud/longitud)"),
        ("Niveles de análisis presentes", "Global, Nacional y Regional en la misma tabla"),
    ],
    "integracion": (
        "Cuando dos fuentes comparten exactamente la misma unidad geográfica y "
        "el mismo año (por ejemplo, la pérdida de bosque de GFW y la clase de "
        "transformación de MapBiomas para un mismo municipio en un mismo año), "
        "el script las combina en una sola fila en vez de apilarlas por "
        "separado, así una fila puede describir, para 'Leticia, 2015', tanto "
        "la pérdida de bosque como la clase de uso a la que se transformó y la "
        "actividad de quema detectada, siempre que las tres fuentes tengan dato "
        "para ese lugar y ese año."
    ),
    "granularidad": (
        "El nivel Regional (municipio-año) concentra la mayoría de los "
        "registros por ser la granularidad más fina disponible de forma "
        "sistemática; los niveles Nacional (departamento-año) y Global "
        "(país-año) aportan los puntos de comparación agregada."
    ),
}

# ---------------------------------------------------------------------------
# 6. Diccionario de datos
# ---------------------------------------------------------------------------
DICCIONARIO = [
    dict(nombre="id_registro", descripcion="Identificador único de fila, generado durante la consolidación.",
         tipo="Numérica (entero, identificador)", dominio="Entero positivo secuencial",
         fuente="Generado", ejemplo="10432"),
    dict(nombre="nivel_analisis", descripcion="Escala a la que corresponde el registro.",
         tipo="Categórica nominal", dominio="{Global, Nacional, Regional}",
         fuente="Derivado durante la integración", ejemplo="Regional"),
    dict(nombre="fuente_origen", descripcion="Fuente(s) que aportaron datos a esa fila; varias fuentes unidas se muestran concatenadas.",
         tipo="Categórica nominal", dominio="GFW, MapBiomas, FIRMS, FAO_SDG, OWID, o combinaciones (ej. 'GFW+MapBiomas')",
         fuente="Generado", ejemplo="GFW+MapBiomas+FIRMS"),
    dict(nombre="pais", descripcion="País al que corresponde el registro.",
         tipo="Categórica nominal / geográfica", dominio="Nombre de país",
         fuente="GFW, FAO, OWID", ejemplo="Colombia"),
    dict(nombre="departamento", descripcion="Departamento colombiano (o división administrativa de primer nivel).",
         tipo="Categórica nominal / geográfica", dominio="33 departamentos de Colombia",
         fuente="GFW, MapBiomas, FIRMS (vía cruce espacial)", ejemplo="Caquetá"),
    dict(nombre="municipio", descripcion="Municipio colombiano.",
         tipo="Categórica nominal / geográfica", dominio="≈1.122 municipios de Colombia",
         fuente="GFW, MapBiomas, FIRMS (vía cruce espacial)", ejemplo="Florencia"),
    dict(nombre="anio", descripcion="Año calendario de la observación.",
         tipo="Temporal (entero)", dominio="2001-2024",
         fuente="Todas", ejemplo="2019"),
    dict(nombre="latitud / longitud", descripcion="Coordenadas del centroide del municipio, o de la agregación puntual de focos de calor.",
         tipo="Numérica continua / geográfica", dominio="Rango geográfico de Colombia (aprox. -4° a 13° N, -79° a -66° O)",
         fuente="Centroides departamentales o FIRMS", ejemplo="0.85, -73.90"),
    dict(nombre="area_perdida_bosque_ha", descripcion="Hectáreas de cobertura arbórea perdidas en el año, sobre una base de densidad de dosel ≥30%.",
         tipo="Numérica continua", dominio="≥ 0 (hectáreas)",
         fuente="Global Forest Watch", ejemplo="128.4"),
    dict(nombre="emisiones_co2_mg", descripcion="Emisiones brutas de carbono asociadas a la pérdida de bosque de ese lugar y año.",
         tipo="Numérica continua", dominio="≥ 0 (megagramos de CO2 equivalente)",
         fuente="Global Forest Watch", ejemplo="9,842"),
    dict(nombre="driver_dominante", descripcion="Causa principal de la pérdida de bosque, entre las categorías con mayor pérdida ese lugar-año.",
         tipo="Categórica nominal", dominio="Agricultura, Incendios, Silvicultura, Urbanización, Minería, entre otras",
         fuente="Global Forest Watch (drivers)", ejemplo="Agricultura"),
    dict(nombre="area_transformada_ha", descripcion="Hectáreas clasificadas ese año bajo alguna categoría de uso antrópico (no natural).",
         tipo="Numérica continua", dominio="≥ 0 (hectáreas)",
         fuente="MapBiomas", ejemplo="342.1"),
    dict(nombre="clase_transformacion_dominante", descripcion="Categoría de uso antrópico con mayor área ese lugar-año.",
         tipo="Categórica nominal", dominio="Área agropecuaria, Área urbanizada, Minería, otras (según leyenda MapBiomas)",
         fuente="MapBiomas", ejemplo="Área agropecuaria"),
    dict(nombre="num_focos_calor", descripcion="Número de detecciones satelitales de fuego activo agregadas para ese lugar y año.",
         tipo="Numérica discreta", dominio="≥ 0 (conteo)",
         fuente="NASA FIRMS", ejemplo="47"),
    dict(nombre="frp_promedio", descripcion="Potencia radiativa del fuego promedio de las detecciones agregadas (proxy de intensidad).",
         tipo="Numérica continua", dominio="≥ 0 (megawatts)",
         fuente="NASA FIRMS", ejemplo="18.3"),
    dict(nombre="confianza_promedio_focos", descripcion="Confianza promedio asignada por el algoritmo satelital a las detecciones.",
         tipo="Numérica continua", dominio="0-100 (recodificada desde baja/nominal/alta cuando aplica)",
         fuente="NASA FIRMS", ejemplo="62.5"),
    dict(nombre="porcentaje_area_forestal", descripcion="Porcentaje del territorio de un país cubierto por bosque.",
         tipo="Numérica continua", dominio="0-100 (%)",
         fuente="FAO (ODS 15.1.1)", ejemplo="52.3"),
    dict(nombre="area_forestal_ha", descripcion="Área forestal total del país, en hectáreas.",
         tipo="Numérica continua", dominio="≥ 0 (hectáreas)",
         fuente="FAO (ODS 15.1.1)", ejemplo="58,470,000"),
    dict(nombre="deforestacion_anual_ha_owid", descripcion="Deforestación anual reportada por país, usada como serie de contraste frente a GFW.",
         tipo="Numérica continua", dominio="≥ 0 (hectáreas)",
         fuente="Our World in Data", ejemplo="101,240"),
]

# ---------------------------------------------------------------------------
# 7. Calidad inicial de los datos
# ---------------------------------------------------------------------------
CALIDAD = {
    "completitud": [
        (
            "Cobertura temporal desigual entre fuentes",
            "FIRMS solo cubre 2012-2022, mientras que GFW y MapBiomas cubren 2001-2024. "
            "Cualquier fila fuera de esa ventana no puede tener información de focos de "
            "calor por definición, no por un error de integración: se documenta como "
            "ausencia estructural, no se imputa.",
        ),
        (
            "Variables que solo aplican a un nivel de análisis",
            "El porcentaje de área forestal (FAO) y la deforestación anual (OWID) solo "
            "existen a nivel país; no tiene sentido rellenarlas para filas de nivel "
            "Regional. Es 'missingness' por diseño, propia de integrar fuentes que "
            "miden a escalas distintas.",
        ),
        (
            "Ambigüedad entre 'cero' y 'sin dato' en la variable de transformación",
            "Un valor nulo en area_transformada_ha puede significar que MapBiomas no "
            "tenía información para ese lugar-año, o que sí la tenía y el área "
            "transformada fue efectivamente cero (todo el territorio era cobertura "
            "natural). Ambos casos hoy se registran igual, y se deja anotado como algo "
            "a resolver antes de cualquier análisis cuantitativo que dependa de esa "
            "variable.",
        ),
    ],
    "unicidad": (
        "No se encontraron registros duplicados en el dataset consolidado, se "
        "verifica automáticamente en cada ejecución del script de construcción."
    ),
    "consistencia": [
        (
            "Nombres de lugar con formato distinto entre fuentes",
            "GFW, MapBiomas y la capa de límites administrativos usan mayúsculas, "
            "tildes y capitalización diferentes para el mismo lugar (p. ej. "
            "'AMAZONAS' frente a 'Amazonas'). El proceso de integración normaliza el "
            "texto antes de cruzar las fuentes para no perder coincidencias válidas "
            "por una diferencia puramente tipográfica.",
        ),
        (
            "Columnas de código vs. columnas de nombre en las capas geográficas",
            "Algunas capas administrativas oficiales incluyen tanto el código "
            "numérico de un departamento/municipio como su nombre en columnas "
            "distintas mal diferenciadas por su etiqueta; se documentó un caso donde "
            "la detección automática inicial tomó por error la columna de código, y "
            "se ajustó para priorizar explícitamente la columna de nombre.",
        ),
        (
            "Rezago entre la hoja de pérdida total y la hoja de causas (drivers)",
            "La proporción de nulos en driver_dominante es ligeramente mayor que en "
            "area_perdida_bosque_ha, lo que sugiere que la atribución de causa de GFW "
            "se actualiza con algo de rezago frente a la cifra de pérdida total.",
        ),
    ],
    "validez": (
        "El cruce espacial de los focos de calor contra los límites municipales "
        "asignó correctamente el 99,9% de los puntos; el 0,1% restante "
        "corresponde probablemente a coordenadas en zonas costeras o fronterizas "
        "donde el punto cae justo fuera de cualquier polígono."
    ),
    "sesgos_y_limitaciones": (
        "La metodología satelital global de GFW aplica un único algoritmo a "
        "todo el planeta, lo que puede generar cifras distintas a las oficiales "
        "de un país (como las del IDEAM) que usan metodologías propias y "
        "criterios ajustados al contexto nacional; no deben tratarse como "
        "intercambiables sin aclarar la diferencia metodológica."
    ),
    "trazabilidad": (
        "Todas las transformaciones (paso de formato ancho a largo, cálculo de "
        "clase dominante, cruce espacial, normalización de nombres) quedan en "
        "un script versionado y documentado, y cada fila conserva en "
        "fuente_origen de qué fuente(s) original(es) proviene, de modo que "
        "cualquier valor del dataset final puede rastrearse hasta el archivo "
        "de origen correspondiente."
    ),
}

# ---------------------------------------------------------------------------
# 8. Limitaciones y consideraciones
# ---------------------------------------------------------------------------
LIMITACIONES = [
    (
        "Fuentes ráster y vectoriales pendientes de integración cuantitativa",
        "SIATAC, el Geovisor de Bosques del IDEAM, Bosque No Bosque 10K y Hansen "
        "Global Forest Change quedan documentados como fuentes primarias "
        "adicionales, pero su formato (ráster o vectorial de alta resolución) "
        "exige un procesamiento geoespacial que se decidió posponer para no "
        "comprometer el alcance de esta primera entrega; su incorporación queda "
        "como trabajo futuro natural del proyecto.",
    ),
    (
        "Diferencias metodológicas entre fuentes satelitales y oficiales",
        "Las cifras de Global Forest Watch (metodología global uniforme) y las "
        "del IDEAM (metodología nacional) no siempre coinciden exactamente para "
        "un mismo año, por diferencias de algoritmo, resolución y definición de "
        "bosque. El proyecto usa GFW por su cobertura homogénea entre escalas, "
        "pero cualquier conclusión sobre cifras oficiales colombianas debería "
        "contrastarse con los reportes directos del IDEAM.",
    ),
    (
        "Ventana temporal desigual entre fuentes",
        "Los focos de calor solo están disponibles para 2012-2022, un "
        "subconjunto del periodo 2001-2024 que cubren el resto de las fuentes; "
        "cualquier análisis que use esa variable debe restringirse a esos años.",
    ),
    (
        "Ambigüedad pendiente entre 'sin dato' y 'cero' en transformación del suelo",
        "Como se explica en el diagnóstico de calidad, esta distinción todavía "
        "no está resuelta y condiciona cualquier lectura cuantitativa de la "
        "variable area_transformada_ha hasta que se revise a fondo la fuente "
        "original.",
    ),
    (
        "Alcance geográfico del cruce espacial",
        "El cruce entre los focos de calor y los municipios depende de la "
        "vigencia y precisión de la capa de límites administrativos del DANE "
        "utilizada; cambios en la división político-administrativa entre la "
        "fecha de la capa y la fecha de los datos de fuego podrían introducir "
        "pequeñas inconsistencias, aunque el porcentaje de puntos sin "
        "asignación (0,1%) sugiere que el efecto es marginal.",
    ),
    (
        "Dataset pensado para descubrir, no para confirmar",
        "Esta etapa entrega una base íntegra y trazable para iniciar la "
        "minería de datos, no un análisis definitivo; la limpieza profunda, el "
        "tratamiento de nulos estructurales y la validación cruzada entre "
        "fuentes se abordarán en las etapas siguientes del proyecto.",
    ),
]

# ---------------------------------------------------------------------------
# ETAPA 2 · Calidad de datos
# ---------------------------------------------------------------------------
# El contenido de esta sección se calcula a partir de dataset_consolidado.csv
# mediante los scripts en calidad_datos/ (perfilamiento.py, metricas_calidad.py
# y tratamiento.py); las cifras que aparecen aquí son la salida de esos
# scripts al momento de redactar el informe, no estimaciones.

SUBMENU2 = [
    ("descripcion2", "1. Descripción y propósito"),
    ("requisitos2", "2. Requisitos de calidad"),
    ("perfilamiento2", "3. Perfilamiento"),
    ("dimensiones2", "4. Dimensiones y métricas"),
    ("problemas2", "5. Problemas, causas e integración"),
    ("tratamiento2", "6. Tratamiento y comparación"),
]

DESCRIPCION2 = {
    "proposito": (
        "El dataset consolidado (dataset_consolidado.csv, 88.513 filas, 20 "
        "variables) se construyó en la Etapa 1 para comparar la pérdida de "
        "cobertura boscosa y su transformación en uso del suelo entre tres "
        "escalas (Global, Nacional, Regional). Esta etapa evalúa si ese "
        "conjunto de datos, tal como quedó consolidado, es apto para ese "
        "propósito: si permite agregar y comparar correctamente entre "
        "escalas, si sus categorías coinciden con lo documentado en el "
        "diccionario de datos, y si los valores que contiene son creíbles."
    ),
    "fuente": (
        "El archivo es la salida de anexo_construccion_dataset/build_dataset.py, "
        "que integra Global Forest Watch, MapBiomas Colombia, NASA FIRMS, FAO "
        "(ODS 15.1.1) y Our World in Data (ver sección Fuentes de datos de la "
        "Etapa 1 para el detalle de cada una)."
    ),
    "variables_principales": [
        "nivel_analisis, pais, departamento, municipio, anio (identifican la unidad geográfica-año)",
        "area_perdida_bosque_ha y emisiones_co2_mg (magnitud del fenómeno, Global Forest Watch)",
        "driver_dominante (causa reportada de la pérdida, Global Forest Watch)",
        "area_transformada_ha y clase_transformacion_dominante (uso resultante, MapBiomas)",
        "num_focos_calor, frp_promedio, confianza_promedio_focos (actividad de quema, NASA FIRMS)",
        "porcentaje_area_forestal, area_forestal_ha, deforestacion_anual_ha_owid (comparación internacional, FAO/OWID)",
    ],
    "cantidad_registros": "88.513 registros, 20 variables (antes del tratamiento aplicado en esta etapa).",
    "uso_esperado": (
        "Servir como insumo de etapas posteriores de minería de datos "
        "(asociación, clustering geográfico, modelos predictivos); por eso "
        "cualquier problema de calidad que afecte la comparación entre "
        "escalas o la homologación de categorías debe corregirse o quedar "
        "explícitamente controlado antes de avanzar."
    ),
}

REQUISITOS2 = {
    "intro": (
        "Los requisitos se derivan directamente del uso esperado del dataset: "
        "comparar el fenómeno entre las escalas Global, Nacional y Regional, "
        "y sostener análisis de tendencia y de causas. No son requisitos "
        "genéricos de \"buenos datos\": cada uno responde a una forma "
        "concreta en que un problema de calidad rompería ese uso."
    ),
    "requisitos": [
        (
            "Completitud",
            "Las variables núcleo (nivel_analisis, pais, departamento, "
            "municipio, anio) deben estar completas al 100%, porque son la "
            "llave que permite ubicar y comparar cualquier registro entre "
            "escalas.",
        ),
        (
            "Unicidad",
            "Cada combinación real de lugar, año y fuente debe aparecer una "
            "sola vez; de lo contrario, cualquier suma o promedio agregado "
            "(por ejemplo, hectáreas perdidas por departamento) queda "
            "sobreestimado sin que se note a simple vista.",
        ),
        (
            "Consistencia",
            "Los nombres de lugar y las categorías (departamento, municipio, "
            "driver_dominante, clase_transformacion_dominante) deben escribirse "
            "siempre igual y coincidir con el dominio documentado en el "
            "diccionario de datos, porque una variante de formato no "
            "reconocida separa artificialmente lo que debería agregarse "
            "junto.",
        ),
        (
            "Validez",
            "La columna pais debe contener países, no agregados regionales o "
            "de grupo de ingreso, para que el nivel Global compare entidades "
            "del mismo tipo; y las variables numéricas deben respetar sus "
            "rangos físicos (porcentajes entre 0 y 100, hectáreas no "
            "negativas, año dentro de la ventana 2001-2024).",
        ),
        (
            "Exactitud",
            "Cuando dos fuentes miden el mismo fenómeno para la misma "
            "unidad geográfica-año, la diferencia entre ambas debe quedar "
            "documentada y no oculta, para no presentar una cifra como más "
            "precisa de lo que realmente es.",
        ),
        (
            "Actualidad",
            "El dataset debe dejar explícito qué tan reciente es su dato más "
            "nuevo y qué proporción de filas corresponde a los últimos años "
            "de la serie, porque el proyecto compara una tendencia y no solo "
            "una fotografía histórica.",
        ),
    ],
}

PERFILAMIENTO2 = {
    "registros": 88513,
    "variables": 20,
    "tipos_resumen": [
        ("Numérica entera", 2, "id_registro, anio"),
        ("Numérica continua", 11, "latitud, longitud, area_perdida_bosque_ha, emisiones_co2_mg, area_transformada_ha, num_focos_calor, frp_promedio, confianza_promedio_focos, porcentaje_area_forestal, area_forestal_ha, deforestacion_anual_ha_owid"),
        ("Categórica nominal", 7, "nivel_analisis, fuente_origen, pais, departamento, municipio, driver_dominante, clase_transformacion_dominante"),
    ],
    "columnas": [
        dict(variable="id_registro", tipo="int64", unicos=88513, nulos=0, pct_nulos=0.0),
        dict(variable="nivel_analisis", tipo="texto", unicos=3, nulos=0, pct_nulos=0.0),
        dict(variable="fuente_origen", tipo="texto", unicos=11, nulos=0, pct_nulos=0.0),
        dict(variable="pais", tipo="texto", unicos=312, nulos=0, pct_nulos=0.0),
        dict(variable="departamento", tipo="texto", unicos=44, nulos=3622, pct_nulos=4.09),
        dict(variable="municipio", tipo="texto", unicos=1119, nulos=5998, pct_nulos=6.78),
        dict(variable="anio", tipo="int64", unicos=24, nulos=0, pct_nulos=0.0),
        dict(variable="latitud", tipo="float64", unicos=9634, nulos=3768, pct_nulos=4.26),
        dict(variable="longitud", tipo="float64", unicos=9630, nulos=3768, pct_nulos=4.26),
        dict(variable="area_perdida_bosque_ha", tipo="float64", unicos=2359, nulos=5470, pct_nulos=6.18),
        dict(variable="emisiones_co2_mg", tipo="float64", unicos=48293, nulos=5470, pct_nulos=6.18),
        dict(variable="driver_dominante", tipo="texto", unicos=7, nulos=8731, pct_nulos=9.86),
        dict(variable="area_transformada_ha", tipo="float64", unicos=27504, nulos=9601, pct_nulos=10.85),
        dict(variable="clase_transformacion_dominante", tipo="texto", unicos=2, nulos=9601, pct_nulos=10.85),
        dict(variable="num_focos_calor", tipo="float64", unicos=821, nulos=60697, pct_nulos=68.57),
        dict(variable="frp_promedio", tipo="float64", unicos=8482, nulos=60697, pct_nulos=68.57),
        dict(variable="confianza_promedio_focos", tipo="float64", unicos=1888, nulos=60697, pct_nulos=68.57),
        dict(variable="porcentaje_area_forestal", tipo="float64", unicos=662, nulos=85201, pct_nulos=96.26),
        dict(variable="area_forestal_ha", tipo="float64", unicos=701, nulos=85201, pct_nulos=96.26),
        dict(variable="deforestacion_anual_ha_owid", tipo="float64", unicos=266, nulos=86977, pct_nulos=98.26),
    ],
    "duplicados": {
        "incluyendo_id": 0,
        "ignorando_id_generado": 7928,
        "pct_ignorando_id_generado": 8.96,
        "nota": (
            "id_registro se genera de forma secuencial durante la "
            "construcción del dataset, así que nunca se repite; comparar "
            "incluyéndolo esconde los duplicados reales. Al excluirlo, "
            "7.928 filas (8,96%) tienen exactamente el mismo contenido que "
            "otra fila."
        ),
    },
    "estadisticos": [
        dict(variable="area_perdida_bosque_ha", minimo=0.0, maximo=424642.0, promedio=678.96, unidad="ha"),
        dict(variable="emisiones_co2_mg", minimo=0.0, maximo=243821901.0, promedio=378424.63, unidad="Mg CO2eq"),
        dict(variable="area_transformada_ha", minimo=147.05, maximo=3278380.11, promedio=52438.62, unidad="ha"),
        dict(variable="num_focos_calor", minimo=1.0, maximo=13851.0, promedio=133.58, unidad="focos"),
        dict(variable="frp_promedio", minimo=0.31, maximo=96.88, promedio=7.63, unidad="MW"),
        dict(variable="confianza_promedio_focos", minimo=25.0, maximo=75.0, promedio=49.53, unidad="%"),
        dict(variable="porcentaje_area_forestal", minimo=0.0, maximo=97.09, promedio=32.94, unidad="%"),
        dict(variable="area_forestal_ha", minimo=0.0, maximo=4200995.2, promedio=79259.75, unidad="ha"),
        dict(variable="deforestacion_anual_ha_owid", minimo=0.0, maximo=9880680.0, promedio=228431.36, unidad="ha"),
    ],
    "atipicos": [
        dict(variable="area_perdida_bosque_ha", limite_superior=337.0, atipicos=11385, pct=13.71),
        dict(variable="emisiones_co2_mg", limite_superior=165483.25, atipicos=11683, pct=14.07),
        dict(variable="area_transformada_ha", limite_superior=66337.24, atipicos=8745, pct=11.08),
        dict(variable="num_focos_calor", limite_superior=154.0, atipicos=3954, pct=14.21),
        dict(variable="frp_promedio", limite_superior=15.9, atipicos=1259, pct=4.53),
        dict(variable="confianza_promedio_focos", limite_superior=51.25, atipicos=6016, pct=21.63),
        dict(variable="area_forestal_ha", limite_superior=48731.38, atipicos=524, pct=15.82),
        dict(variable="deforestacion_anual_ha_owid", limite_superior=169955.0, atipicos=214, pct=13.93),
    ],
    "nota_atipicos": (
        "El método usado (rango intercuartílico, límite superior = Q3 + "
        "1,5·RIC) es deliberadamente sensible porque el fenómeno estudiado "
        "es de cola larga por naturaleza: unos pocos municipios y años "
        "concentran eventos extremos de pérdida de bosque o de quema, que "
        "son reales y no errores de captura. La decisión sobre qué hacer "
        "con estos valores se documenta en el plan de tratamiento, no aquí."
    ),
    "script": "calidad_datos/perfilamiento.py -> calidad_datos/reporte_perfilamiento.json",
}
