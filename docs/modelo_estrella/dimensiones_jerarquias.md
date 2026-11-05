# Dimensiones y jerarquías

| Dimensión | Perspectiva | Jerarquía | Justificación |
|---|---|---|---|
| Territorio | ¿Dónde ocurre la pérdida? | región natural → departamento → municipio | Es la pregunta central del proyecto (dónde se concentra la pérdida). |
| Tiempo | ¿Cuándo ocurre? | periodo de 12 años → trienio → año | Calendario diario con año fiscal, semestre, cuatrimestre, trimestre, bimestre, mes, semana, día, hora y bandera de pandemia. La fuente es anual: los hechos se asocian al 1 de enero de cada año, así que el análisis llega hasta el año y usa trienios y periodos equivalentes de 12 años; los niveles sub-anuales quedan disponibles para fuentes más finas. |
| Causa | ¿Qué la acompaña? | grupo de causa → causa dominante | El grupo agrupa causas con relación válida de pertenencia (p. ej. agricultura permanente y migratoria → Agropecuaria). |
| Transformación del suelo | ¿En qué se transforma el suelo? | clase de transformación (un nivel) | Perspectiva propia de MapBiomas; no se deriva de la causa. Se deja con un nivel porque solo hay dos clases informadas. |
| Fuente | ¿Con cuántas fuentes se documenta? | número de fuentes → combinación de fuentes | Es una perspectiva real del problema: la cobertura de las fuentes condiciona qué comparaciones son válidas. |

| Jerarquía | Niveles | Relación de agrupación |
|---|---|---|
| H1 · Territorio | Región natural → Departamento → Municipio | Cada municipio pertenece a un solo departamento y cada departamento a una sola región (convención declarada). |
| H2 · Tiempo (análisis) | Periodo (12 años) → Trienio → Año | Cada año pertenece a un solo trienio y a un solo periodo; los trienios no cruzan periodos. Es la jerarquía que usan las vistas. |
| H2b · Calendario | Año → Semestre → Trimestre → Mes → Día | Cada trimestre cae en un solo semestre y cada mes en un solo trimestre. Definida en la dimensión; los datos actuales solo llegan al nivel año. |
| H2c · Calendario alterno | Año → Cuatrimestre → Bimestre → Mes | Cada bimestre cae en un solo cuatrimestre. No se mezcla con H2b porque el cuatrimestre cruza semestres y el bimestre cruza trimestres. La semana ISO tampoco se anida en el mes. |
| H3 · Causa | Grupo de causa → Causa dominante | Cada causa pertenece a un solo grupo. |
| H4 · Fuente | Número de fuentes → Combinación de fuentes | Cada combinación tiene un número fijo de fuentes. |
