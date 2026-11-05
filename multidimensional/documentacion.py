# -*- coding: utf-8 -*-
"""
documentacion.py
================
Única fuente de verdad de la documentación del modelo estrella: la usan la
página «Modelo estrella» de Flask, el generador de docs/modelo_estrella/*.md
(`python multidimensional/generar_docs.py`) y el informe técnico.
"""

from . import olap

TITULO = "Hechos de pérdida forestal por territorio y año"

HECHOS = dict(
    nombre="hechos_perdida_forestal",
    proposito=("Registrar, para cada territorio y cada año, cuánto bosque se perdió y qué se asocia con esa pérdida "
               "(emisiones, transformación del suelo, focos de calor, cobertura de fuentes)."),
    granularidad=("Una fila por TERRITORIO y AÑO. La clave primaria compuesta (territorio_key, tiempo_key; la fuente es anual, así que hay un solo tiempo_key por año) impone esa "
                  "granularidad. Un municipio-año que en el dataset tratado aparece en varias filas (copias con distinta "
                  "combinación de fuentes) se consolida en una sola fila; el número de filas de origen se conserva en "
                  "n_registros_origen."),
    unidad_analisis=("El municipio en un año. La unidad de análisis del proyecto es el registro de pérdida de bosque de "
                     "un territorio y año; la granularidad del modelo es el territorio-año, que coincide con la unidad de "
                     "análisis pero no con la fila del CSV (un registro de origen ≠ una fila de hechos)."),
)

# (campo, tipo, clave, descripción, origen en el dataset tratado, transformación)
TABLAS = [
    dict(nombre="dim_territorio", rol="Dimensión", pk="territorio_key",
         jerarquia="región natural → departamento → municipio",
         campos=[
             ("territorio_key", "INTEGER", "PK", "Clave sustituta del territorio.", "—", "Secuencia al cargar."),
             ("nivel_analisis", "TEXT", "UK", "Nivel de la fuente: Regional, Nacional o Global.", "nivel_analisis", "Sin cambio."),
             ("escala", "TEXT", "", "Escala del miembro: Municipal, Departamental o País.", "nivel_analisis", "Regional→Municipal, Nacional→Departamental, Global→País."),
             ("pais", "TEXT", "UK", "País.", "pais", "Espacios normalizados."),
             ("region_natural", "TEXT", "", "Región natural (Amazonía, Andina, Caribe, Orinoquía, Pacífica, Insular).", "departamento", "Asignada con la tabla departamento→región; «Sin región informada» / «No aplica» si no corresponde."),
             ("departamento", "TEXT", "UK", "Departamento.", "departamento", "Nulo → «Sin departamento informado» (Global: «No aplica»)."),
             ("municipio", "TEXT", "UK", "Municipio.", "municipio", "Nulo → «Sin municipio informado»; nivel Nacional → «(total del departamento)»."),
             ("es_agregado_regional", "INTEGER", "", "1 si el miembro es un agregado de la fuente.", "es_agregado_regional", "True/False → 1/0."),
             ("latitud / longitud", "REAL", "", "Coordenadas del centroide.", "latitud, longitud", "Primer valor no nulo."),
         ]),
    dict(nombre="dim_tiempo", rol="Dimensión", pk="id_dim_tiempo",
         jerarquia="calendario: año → semestre → trimestre → mes → día · análisis: periodo (12 años) → trienio → año",
         campos=[
             ("id_dim_tiempo", "INTEGER", "PK", "Clave sustituta con formato AAAAMMDD (ej. 20261104). Los hechos anuales usan AAAA0101.", "anio", "Calculada: año×10000 + mes×100 + día."),
             ("fecha", "TEXT", "UK", "Fecha completa AAAA-MM-DD.", "anio", "Calendario generado (2001-01-01 a 2024-12-31, 8.766 días)."),
             ("anio", "INTEGER", "", "Año calendario de 4 dígitos (2001–2024).", "anio", "Sin cambio."),
             ("anio_fiscal", "TEXT", "", "Año fiscal (FY2026). Coincide con el año calendario.", "anio", "'FY' + año."),
             ("semestre", "TEXT", "", "Semestre 1 o 2.", "(generada por el ETL)", "Calculado desde el mes."),
             ("cuatrimestre", "TEXT", "", "Cuatrimestre 1 a 3.", "(generada por el ETL)", "Calculado desde el mes."),
             ("trimestre", "TEXT", "", "Trimestre 1 a 4.", "(generada por el ETL)", "Calculado desde el mes."),
             ("bimestre", "TEXT", "", "Bimestre 1 a 6.", "(generada por el ETL)", "Calculado desde el mes."),
             ("mes / mes_nombre / mes_nombre_corto", "INTEGER / TEXT / TEXT", "", "Número del mes (1–12), nombre (Noviembre) y abreviatura (Nov).", "(generada por el ETL)", "Calculado desde la fecha."),
             ("semana / semana_nombre", "INTEGER / TEXT", "", "Semana ISO 8601 del año (1–53) y su nombre (Semana 45).", "(generada por el ETL)", "Calculado con isocalendar(); la semana no se anida en el mes."),
             ("dia / dia_del_anio", "INTEGER", "", "Día del mes (1–31) y día secuencial del año (1–366).", "(generada por el ETL)", "Calculado desde la fecha."),
             ("dia_semana_numero / dia_semana_nombre / dia_semana_corto", "INTEGER / TEXT / TEXT", "", "Posición en la semana (1 = lunes a 7 = domingo), nombre (Miércoles) y abreviatura (Mié).", "(generada por el ETL)", "Calculado desde la fecha."),
             ("hora", "INTEGER", "", "Hora del día (0–23). El grano de la dimensión es el día, por lo que es NULL («No aplica»); no hay datos horarios.", "(generada por el ETL)", "NULL; no se multiplica la dimensión por 24."),
             ("es_periodo_pandemia", "INTEGER", "", "1 si el día cae entre el 11-mar-2020 y el 5-may-2023 (declaración y fin de la emergencia internacional por COVID-19 de la OMS).", "(generada por el ETL)", "Bandera de contexto; 1.151 días."),
             ("es_anio_con_pandemia", "INTEGER", "", "1 si el año tiene algún día de pandemia (2020–2023). Es la bandera aplicable a los hechos anuales.", "anio", "Derivada de es_periodo_pandemia."),
             ("trienio / trienio_orden", "TEXT / INTEGER", "", "Trienio al que pertenece el año (2001–2003, …) y su orden.", "anio", "Calculado: (año − 2001) ÷ 3."),
             ("periodo / periodo_orden", "TEXT / INTEGER", "", "Periodo de 12 años (2001–2012 o 2013–2024) y su orden.", "anio", "Calculado; ambos periodos tienen 12 años (equivalentes)."),
         ]),
    dict(nombre="dim_causa", rol="Dimensión", pk="causa_key",
         jerarquia="grupo de causa → causa (driver dominante)",
         campos=[
             ("causa_key", "INTEGER", "PK", "Clave sustituta de la causa.", "—", "Secuencia al cargar."),
             ("driver_dominante", "TEXT", "UK", "Causa dominante de la pérdida según la fuente.", "driver_dominante", "Vacío → «Sin causa informada» (Colombia) o «No aplica» (otros países)."),
             ("grupo_causa", "TEXT", "", "Agropecuaria, Forestal (plantaciones), Natural, Infraestructura y minería.", "driver_dominante", "Agrupación definida en el ETL."),
             ("tipo_valor", "TEXT", "", "Informada / Sin informar / No aplica.", "—", "Distingue faltante de categoría no aplicable."),
         ]),
    dict(nombre="dim_transformacion", rol="Dimensión", pk="transformacion_key",
         jerarquia="clase de transformación (un nivel)",
         campos=[
             ("transformacion_key", "INTEGER", "PK", "Clave sustituta de la clase.", "—", "Secuencia al cargar."),
             ("clase_transformacion", "TEXT", "UK", "Clase de transformación dominante del suelo (Área agropecuaria, Área sin vegetación).", "clase_transformacion_dominante", "Vacío → «Sin clase informada» o «No aplica»."),
             ("tipo_valor", "TEXT", "", "Informada / Sin informar / No aplica.", "—", "Distingue faltante de categoría no aplicable."),
         ]),
    dict(nombre="dim_fuente", rol="Dimensión", pk="fuente_key",
         jerarquia="número de fuentes → combinación de fuentes",
         campos=[
             ("fuente_key", "INTEGER", "PK", "Clave sustituta de la combinación de fuentes.", "—", "Secuencia al cargar."),
             ("fuente_origen", "TEXT", "UK", "Combinación de fuentes (p. ej. GFW+MapBiomas+FIRMS).", "fuente_origen", "Se conserva la combinación textual."),
             ("n_fuentes", "INTEGER", "", "Cantidad de fuentes que aportaron al registro.", "fuente_origen", "Conteo de componentes."),
             ("incluye_gfw / _mapbiomas / _firms / _fao / _owid", "INTEGER", "", "Indicadores 0/1 de cada fuente.", "fuente_origen", "Derivados de la combinación."),
         ]),
    dict(nombre="hechos_perdida_forestal", rol="Hechos", pk="(territorio_key, tiempo_key)",
         jerarquia="—",
         campos=[
             ("territorio_key", "INTEGER", "PK, FK", "→ dim_territorio.", "—", "Búsqueda por clave natural."),
             ("tiempo_key", "INTEGER", "PK, FK", "→ dim_tiempo.id_dim_tiempo; el 1 de enero del año del hecho (AAAA0101).", "anio", "Calculada: año×10000 + 101."),
             ("causa_key", "INTEGER", "FK", "→ dim_causa.", "driver_dominante", "Primer valor no nulo entre las copias."),
             ("transformacion_key", "INTEGER", "FK", "→ dim_transformacion.", "clase_transformacion_dominante", "Primer valor no nulo entre las copias."),
             ("fuente_key", "INTEGER", "FK", "→ dim_fuente.", "fuente_origen", "Primer valor no nulo entre las copias."),
             ("n_registros_origen", "INTEGER", "", "Filas del dataset tratado consolidadas en este hecho.", "—", "Conteo de copias; permite reconstruir los 80.585 registros."),
             ("id_registro_min", "INTEGER", "", "Menor id_registro del grupo (trazabilidad).", "id_registro", "Mínimo."),
             ("area_perdida_bosque_ha", "REAL", "Medida", "Hectáreas de bosque perdidas.", "area_perdida_bosque_ha", "Primer valor no nulo (las copias comparten el área). Nulo se conserva nulo."),
             ("emisiones_co2_mg", "REAL", "Medida", "Emisiones estimadas de CO₂e (Mg).", "emisiones_co2_mg", "Promedio de las copias (difieren levemente)."),
             ("area_transformada_ha", "REAL", "Medida", "Área con transformación del suelo (ha).", "area_transformada_ha", "Primer valor no nulo."),
             ("num_focos_calor", "REAL", "Medida", "Focos de calor FIRMS asociados (2012–2022).", "num_focos_calor", "Primer valor no nulo; nulo ≠ 0."),
             ("frp_promedio, confianza_promedio_focos", "REAL", "Medida", "Potencia radiativa y confianza promedio de los focos.", "frp_promedio, confianza_promedio_focos", "Primer valor no nulo."),
             ("porcentaje_area_forestal, area_forestal_ha", "REAL", "Medida", "Contexto forestal del país (FAO).", "porcentaje_area_forestal, area_forestal_ha", "Primer valor no nulo."),
             ("deforestacion_anual_ha_owid", "REAL", "Medida", "Deforestación anual del país (OWID).", "deforestacion_anual_ha_owid", "Primer valor no nulo."),
             ("area_perdida_atipica, emisiones_atipicas", "INTEGER", "Marca", "1 si el valor fue marcado atípico en el tratamiento.", "*_atipico", "Máximo entre las copias. Los atípicos NO se eliminan."),
         ]),
]

RELACIONES = [
    ("hechos_perdida_forestal.territorio_key", "dim_territorio.territorio_key", "muchos a uno"),
    ("hechos_perdida_forestal.tiempo_key", "dim_tiempo.id_dim_tiempo", "muchos a uno"),
    ("hechos_perdida_forestal.causa_key", "dim_causa.causa_key", "muchos a uno"),
    ("hechos_perdida_forestal.transformacion_key", "dim_transformacion.transformacion_key", "muchos a uno"),
    ("hechos_perdida_forestal.fuente_key", "dim_fuente.fuente_key", "muchos a uno"),
]

DIMENSIONES = [
    ("Territorio", "¿Dónde ocurre la pérdida?", "región natural → departamento → municipio",
     "Es la pregunta central del proyecto (dónde se concentra la pérdida)."),
    ("Tiempo", "¿Cuándo ocurre?", "periodo de 12 años → trienio → año",
     "Calendario diario con año fiscal, semestre, cuatrimestre, trimestre, bimestre, mes, semana, día, hora y bandera de pandemia. La fuente es anual: los hechos se asocian al 1 de enero de cada año, así que el análisis llega hasta el año y usa trienios y periodos equivalentes de 12 años; los niveles sub-anuales quedan disponibles para fuentes más finas."),
    ("Causa", "¿Qué la acompaña?", "grupo de causa → causa dominante",
     "El grupo agrupa causas con relación válida de pertenencia (p. ej. agricultura permanente y migratoria → Agropecuaria)."),
    ("Transformación del suelo", "¿En qué se transforma el suelo?", "clase de transformación (un nivel)",
     "Perspectiva propia de MapBiomas; no se deriva de la causa. Se deja con un nivel porque solo hay dos clases informadas."),
    ("Fuente", "¿Con cuántas fuentes se documenta?", "número de fuentes → combinación de fuentes",
     "Es una perspectiva real del problema: la cobertura de las fuentes condiciona qué comparaciones son válidas."),
]

JERARQUIAS = [
    ("H1 · Territorio", "Región natural → Departamento → Municipio", "Cada municipio pertenece a un solo departamento y cada departamento a una sola región (convención declarada)."),
    ("H2 · Tiempo (análisis)", "Periodo (12 años) → Trienio → Año", "Cada año pertenece a un solo trienio y a un solo periodo; los trienios no cruzan periodos. Es la jerarquía que usan las vistas."),
    ("H2b · Calendario", "Año → Semestre → Trimestre → Mes → Día", "Cada trimestre cae en un solo semestre y cada mes en un solo trimestre. Definida en la dimensión; los datos actuales solo llegan al nivel año."),
    ("H2c · Calendario alterno", "Año → Cuatrimestre → Bimestre → Mes", "Cada bimestre cae en un solo cuatrimestre. No se mezcla con H2b porque el cuatrimestre cruza semestres y el bimestre cruza trimestres. La semana ISO tampoco se anida en el mes."),
    ("H3 · Causa", "Grupo de causa → Causa dominante", "Cada causa pertenece a un solo grupo."),
    ("H4 · Fuente", "Número de fuentes → Combinación de fuentes", "Cada combinación tiene un número fijo de fuentes."),
]

HERRAMIENTAS = [
    ("SQLite 3", "Almacén del modelo estrella. Se consulta desde Flask con el módulo estándar sqlite3, no requiere servidor y el archivo se despliega junto con la aplicación en Render."),
    ("Python (csv, sqlite3, hashlib)", "ETL reproducible solo con la biblioteca estándar: no añade dependencias nuevas al despliegue."),
    ("Flask (Blueprint)", "La sección se integra a la aplicación existente sin modificar las páginas de las etapas anteriores."),
    ("SVG generado en el servidor", "Gráficas legibles, sin librerías externas ni JavaScript obligatorio; los filtros y las operaciones funcionan por enlaces y formularios."),
]

ETL_PASOS = [
    "Leer deforestacion_limpio.csv (dataset tratado, 80.585 registros) y calcular su huella SHA-256.",
    "Agrupar las filas por la clave natural del hecho: (nivel de análisis, país, departamento, municipio, año).",
    "Generar la dimensión tiempo como calendario diario (2001-01-01 a 2024-12-31): atributos de año, año fiscal, semestre a bimestre, mes, semana ISO, día, hora (NULL) y banderas de pandemia; cada hecho anual se asocia al 1 de enero de su año.",
    "Construir las demás dimensiones con claves sustitutas y asignar región natural, grupo de causa y periodos; los vacíos se mapean a «Sin … informada» o «No aplica» según corresponda.",
    "Colapsar cada grupo en una fila de hechos: área = primer valor no nulo, emisiones = promedio de las copias, demás medidas = primer valor no nulo; se guarda n_registros_origen.",
    "Crear las tablas con el DDL (sql/05_modelo_estrella_ddl.sql), cargar dimensiones y hechos con las claves foráneas activadas y registrar la trazabilidad en meta_carga.",
    "Ejecutar multidimensional/validar_modelo.py: 30 verificaciones de integridad (incluye el calendario) y 10 comparaciones con el dataset tratado (reporte_validacion.json).",
]


def medidas():
    """Medidas de análisis: significado, unidad, fórmula, agregación y cuándo se suman."""
    return [dict(clave=k, nombre=m["nombre"], unidad=m["unidad"], formula=m["formula"],
                 agregacion=m["agregacion"], suma=m["suma"]) for k, m in olap.MEDIDAS.items()]
