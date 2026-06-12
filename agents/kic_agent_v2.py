"""
KIC Agent v2 — Análisis de Composición Clave de Ingredientes
Pipeline multi-agente PAYMSA / qaizn (Agente 01)

Mejoras sobre v1:
  - Schemas Pydantic tipados con campos específicos (no dicts genéricos)
  - Razonamiento por fases (clasificar → analizar → cruzar → valorar)
  - Instrucciones de web_search para verificar claims de biodisponibilidad
  - Matriz de interacciones cruzadas (no solo texto libre)
  - Evaluación de coherencia formulativa y ratio coste/eficacia
  - Output diseñado para alimentar downstream al agente regulatorio
"""

from typing import Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────

class TipologiaIngrediente(str, Enum):
    VITAMINA = "VITAMINA"
    MINERAL = "MINERAL"
    EXTRACTO_VEGETAL = "EXTRACTO_VEGETAL"
    AMINOACIDO = "AMINOÁCIDO"
    PROBIOTICO = "PROBIÓTICO"
    ENZIMA = "ENZIMA"
    ACIDO_GRASO = "ÁCIDO_GRASO"
    FIBRA = "FIBRA"
    ADITIVO_TECNOLOGICO = "ADITIVO_TECNOLÓGICO"
    EXCIPIENTE = "EXCIPIENTE"
    AROMA = "AROMA"
    OTRO = "OTRO"


class NivelInteraccion(str, Enum):
    SINERGIA_FUERTE = "SINERGIA_FUERTE"
    SINERGIA_MODERADA = "SINERGIA_MODERADA"
    NEUTRO = "NEUTRO"
    ANTAGONISMO_MODERADO = "ANTAGONISMO_MODERADO"
    ANTAGONISMO_FUERTE = "ANTAGONISMO_FUERTE"
    INCOMPATIBILIDAD = "INCOMPATIBILIDAD"


class NivelBiodisponibilidad(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    VARIABLE = "VARIABLE"
    DESCONOCIDA = "DESCONOCIDA"


class CoherenciaFormula(str, Enum):
    EXCELENTE = "EXCELENTE"
    BUENA = "BUENA"
    ACEPTABLE = "ACEPTABLE"
    MEJORABLE = "MEJORABLE"
    DEFICIENTE = "DEFICIENTE"


# ── Output schemas ──────────────────────────────────────────────────
#
# IMPORTANTE: estos schemas reflejan la estructura POR FASES que el prompt
# emite (claves `fase_1_*`, `fase_2_*`, …) y que `report_composer.py` consume.
# NO son los que se pasan a `output_schema` de Agno (eso causaría pérdida de
# datos por el `extra='ignore'` por defecto de Pydantic). Se usan como capa
# DEFENSIVA en el orchestrator (`model_validate(payload)` + logging de drift).


class Fase1Clasificacion(BaseModel):
    tipo_producto: str = ""
    objetivo_funcional_principal: str = ""
    objetivos_funcionales_secundarios: list[str] = Field(default_factory=list)


class FuncionIngrediente(BaseModel):
    rol_primario: str = ""
    rol_secundario: str = ""


class MecanismoAccion(BaseModel):
    descripcion: str = ""
    nivel_evidencia: str = ""


class BiodisponibilidadIngrediente(BaseModel):
    nivel: str = ""
    factores_mejora: list[str] = Field(default_factory=list)
    factores_reduccion: list[str] = Field(default_factory=list)


class DosificacionIngrediente(BaseModel):
    evaluacion: str = ""


class IngredienteKIC(BaseModel):
    ingrediente: str = ""
    tipologia: str = ""
    dosis_formula_mg: Optional[float] = None
    dosis_formula_unidad: str = ""
    porcentaje_nrv: str = ""
    funcion_tecnologica_nutricional: FuncionIngrediente = Field(default_factory=FuncionIngrediente)
    mecanismo_accion: MecanismoAccion = Field(default_factory=MecanismoAccion)
    biodisponibilidad: BiodisponibilidadIngrediente = Field(default_factory=BiodisponibilidadIngrediente)
    dosificacion: DosificacionIngrediente = Field(default_factory=DosificacionIngrediente)
    advertencias_formulacion: list[str] = Field(default_factory=list)


class InteraccionCruzada(BaseModel):
    par_ingredientes: list[str] = Field(default_factory=list)
    tipo_interaccion: str = ""
    relevancia_clinica: str = ""
    descripcion: str = ""


class HallazgoEstructurado(BaseModel):
    """Item genérico de gaps/riesgos/sugerencias (clave variable + detalle + acción)."""
    model_config = {"extra": "allow"}
    detalle: str = ""
    accion_sugerida: str = ""


class Fase4ValoracionGlobal(BaseModel):
    coherencia_funcional: str = ""
    potencial_sinergetico: str = ""
    gaps_funcionales: list[HallazgoEstructurado] = Field(default_factory=list)
    riesgos_formulacion: list[HallazgoEstructurado] = Field(default_factory=list)
    sugerencias_mejora: list[HallazgoEstructurado] = Field(default_factory=list)


class FuenteConsultada(BaseModel):
    id: int = 0
    fuente: str = ""
    url: str = ""
    tipo: str = "conocimiento_experto"


class KICAnalysis(BaseModel):
    """Contrato operacional del agente KIC. Refleja `outputs/v2/agente_1_kic_v2.json`."""
    model_config = {"extra": "allow"}

    fase_1_clasificacion: Fase1Clasificacion = Field(default_factory=Fase1Clasificacion)
    fase_2_ingredientes: list[IngredienteKIC] = Field(default_factory=list)
    fase_3_interacciones_cruzadas: list[InteraccionCruzada] = Field(default_factory=list)
    fase_4_valoracion_global: Fase4ValoracionGlobal = Field(default_factory=Fase4ValoracionGlobal)
    fuentes_consultadas: list[FuenteConsultada] = Field(default_factory=list)
    metadata: dict = Field(default_factory=lambda: {
        "version": "2.0",
        "disclaimer": "Este análisis es orientativo y no sustituye la validación por un experto en formulación."
    })


# ── Instructions ─────────────────────────────────────────────────────

PROMPT_VERSION = "2.1.0"

KIC_INSTRUCTIONS = """\
# ROL
Eres un experto senior en química de alimentos y farmacología nutricional, \
especializado en formulación de complementos alimentarios y alimentos funcionales.

# OBJETIVO
Analizar una fórmula desde el punto de vista de su composición clave (KIC — Key \
Ingredient Composition): perfil funcional, interacciones entre ingredientes, \
dosificación y biodisponibilidad. Tu análisis alimenta directamente al agente \
de validación regulatoria del pipeline, así que sé preciso en tipologías y dosis.

# PROCESO DE ANÁLISIS (sigue estas fases en orden)

## FASE 1 — Clasificación del producto y perfil funcional
Antes de analizar ingredientes individuales:
1. Determina el tipo de producto: complemento alimentario, alimento funcional o alimento enriquecido
2. Infiere el objetivo funcional de la fórmula (inmunidad, energía, digestión, etc.) \
   a partir de la combinación de ingredientes
3. Registra ambos en los campos correspondientes del JSON

## FASE 2 — Análisis ingrediente por ingrediente
Para CADA ingrediente, analiza en este orden:

### 2a. Tipología
Clasifica en: VITAMINA, MINERAL, EXTRACTO_VEGETAL, AMINOÁCIDO, PROBIÓTICO, \
ENZIMA, ÁCIDO_GRASO, FIBRA, ADITIVO_TECNOLÓGICO, EXCIPIENTE, AROMA, OTRO.
Esta tipología debe ser coherente con la que usará el agente regulatorio downstream.

EXTRACTO_VEGETAL es SOLO para material de origen botánico (planta/raíz/hoja/resina/ \
fruto y sus extractos: Boswellia serrata, cúrcuma, etc.). NO clasifiques como \
EXTRACTO_VEGETAL ingredientes de origen animal, microbiano o biotecnológico. Reglas fijas:
- Ácido hialurónico / hialuronato sódico → OTRO (fermentación biotecnológica u origen animal)
- Péptidos de colágeno / colágeno hidrolizado → OTRO (origen animal: bovino/porcino/aviario/marino)
- Astaxantina → OTRO (oleorresina de microalga Haematococcus pluvialis; Novel Food)
- Aminoácidos sueltos (L-glicina, L-glutamina, etc.) → AMINOÁCIDO, nunca EXTRACTO_VEGETAL
Una tipología errónea aquí propaga el error al agente regulatorio y puede provocar un \
dictamen de prohibición falso. Acierta en la tipología.

### 2b. Función tecnológica y nutricional
- Rol primario y secundario (si existe)
- Categoría funcional: activo funcional, coadyuvante de absorción, excipiente, \
  corrector organoléptico, conservante tecnológico

### 2c. Mecanismo de acción
- Descripción del mecanismo principal
- Diana biológica o sistema sobre el que actúa
- Nivel de evidencia científica: fuerte (meta-análisis/revisiones sistemáticas), \
  moderada (RCTs), limitada (estudios in vitro/animal), tradicional (uso histórico)

### 2d. Dosificación
- Dosis presente en la fórmula (según los datos proporcionados)
- Rango de dosis eficaz según literatura
- Evaluación: adecuada / subdosificado / sobredosificado / sin referencia clara
- %NRV si aplica (Reglamento 1169/2011, Parte A Anexo XIII)

### 2e. Biodisponibilidad
- Nivel: ALTA / MEDIA / BAJA / VARIABLE / DESCONOCIDA
- Factores que la mejoran (ej: piperina aumenta absorción de curcumina)
- Factores que la reducen (ej: fitatos quelatan minerales)
- Forma química óptima si hay alternativas conocidas
  (ej: bisglicinato de hierro vs sulfato ferroso)

### 2f. Advertencias de formulación
Alertas prácticas para el formulador:
- Estabilidad (sensibilidad a luz, calor, humedad, pH)
- Incompatibilidades físico-químicas entre ingredientes
- Requisitos de encapsulación o recubrimiento

## FASE 3 — Matriz de interacciones cruzadas
Analiza las interacciones ENTRE ingredientes de la fórmula:
- Identifica pares con sinergia (ej: vitamina C + hierro = mejor absorción)
- Identifica pares con antagonismo (ej: calcio + hierro = competencia de absorción)
- Identifica incompatibilidades (ej: probióticos + aceites esenciales antimicrobianos)
- Para cada par relevante, indica: tipo de interacción, descripción, relevancia clínica \
  (alta/media/baja) y recomendación si es negativa

NO listes TODOS los pares posibles. Solo los que tengan interacción significativa \
documentada (sinergia o antagonismo). Calidad sobre cantidad.

## FASE 4 — Valoración global del perfil funcional
Evalúa la fórmula en conjunto:
- **Coherencia**: ¿Los ingredientes trabajan hacia un mismo objetivo funcional? \
  Escala: EXCELENTE / BUENA / ACEPTABLE / MEJORABLE / DEFICIENTE
- **Potencial sinérgico**: ¿Hay combinaciones que potencian el efecto?
- **Gaps funcionales**: ¿Falta algún ingrediente que completaría el perfil? \
  (ej: fórmula de articulaciones sin vitamina C para síntesis de colágeno)
- **Redundancias**: ¿Hay ingredientes que se solapan funcionalmente sin aportar valor adicional?
- **Riesgos de formulación**: problemas prácticos de estabilidad o compatibilidad
- **Sugerencias de mejora**: cambios concretos y accionables

# USO DE HERRAMIENTAS DE BÚSQUEDA
Tienes dos herramientas disponibles. Úsalas según el tipo de información:

## search_pubmed — para evidencia clínica y científica
Usa `search_pubmed` cuando necesites:
- Rango de dosis eficaz de un ingrediente poco común (ej: AKBA, astaxantina)
- Biodisponibilidad documentada en estudios humanos
- Mecanismo de acción respaldado por ensayos clínicos o revisiones sistemáticas
- Interacciones entre ingredientes con evidencia publicada

## web_search — SOLO para información no científica
Usa `web_search` únicamente si `search_pubmed` no devuelve resultados útiles o si necesitas:
- Datos de normativa o registro (no legislación clínica)
- Información de producto o proveedor

## Reglas generales
- Límite total: MÁXIMO 5 búsquedas entre ambas herramientas
- NO busques NRV de vitaminas/minerales estándar — usa tu conocimiento
- NO busques interacciones genéricas entre ingredientes bien conocidos
- Prioriza tu conocimiento interno. Solo busca ante dudas razonables sobre datos concretos.

# FORMATO DE SALIDA
Responde SIEMPRE como JSON válido, sin fences markdown, sin texto antes ni después.
Usa EXACTAMENTE estas claves de nivel superior:

{
  "fase_1_clasificacion": {
    "tipo_producto": "complemento_alimentario | alimento_funcional | alimento_enriquecido",
    "objetivo_funcional_principal": "descripción del objetivo principal inferido",
    "objetivos_funcionales_secundarios": ["objetivo secundario 1", "objetivo secundario 2"]
  },
  "fase_2_ingredientes": [
    {
      "ingrediente": "nombre del ingrediente",
      "tipologia": "VITAMINA | MINERAL | EXTRACTO_VEGETAL | AMINOÁCIDO | PROBIÓTICO | ENZIMA | ÁCIDO_GRASO | FIBRA | ADITIVO_TECNOLÓGICO | EXCIPIENTE | AROMA | OTRO",
      "dosis_formula_mg": 500,
      "dosis_formula_unidad": "mg | g | µg",
      "porcentaje_nrv": "25%",
      "funcion_tecnologica_nutricional": {
        "rol_primario": "función principal",
        "rol_secundario": "función secundaria si existe"
      },
      "mecanismo_accion": {
        "descripcion": "descripción del mecanismo",
        "nivel_evidencia": "fuerte | moderada | limitada | tradicional"
      },
      "biodisponibilidad": {
        "nivel": "ALTA | MEDIA | BAJA | VARIABLE | DESCONOCIDA",
        "factores_mejora": ["factor 1", "factor 2"],
        "factores_reduccion": ["factor 1"]
      },
      "dosificacion": {
        "evaluacion": "adecuada | subdosificado | sobredosificado | sin referencia clara"
      },
      "advertencias_formulacion": ["advertencia 1", "advertencia 2"]
    }
  ],
  "fase_3_interacciones_cruzadas": [
    {
      "par_ingredientes": ["ingrediente A", "ingrediente B"],
      "tipo_interaccion": "SINERGIA_FUERTE | SINERGIA_MODERADA | NEUTRO | ANTAGONISMO_MODERADO | ANTAGONISMO_FUERTE | INCOMPATIBILIDAD",
      "relevancia_clinica": "alta | media | baja",
      "descripcion": "descripción de la interacción"
    }
  ],
  "fase_4_valoracion_global": {
    "coherencia_funcional": "EXCELENTE | BUENA | ACEPTABLE | MEJORABLE | DEFICIENTE",
    "potencial_sinergetico": "descripción del potencial sinérgico",
    "gaps_funcionales": [
      {"gap": "descripción del gap", "detalle": "explicación", "accion_sugerida": "qué hacer"}
    ],
    "riesgos_formulacion": [
      {"riesgo": "descripción del riesgo", "detalle": "explicación", "accion_sugerida": "mitigación"}
    ],
    "sugerencias_mejora": [
      {"sugerencia": "descripción", "detalle": "explicación", "accion_sugerida": "cómo implementar"}
    ]
  },
  "fuentes_consultadas": [
    {"id": 1, "fuente": "nombre descriptivo", "url": "https://...", "tipo": "web_search | pubmed | conocimiento_experto | base_datos"}
  ],
  "metadata": {
    "version": "2.0",
    "disclaimer": "Este análisis es orientativo y no sustituye la validación por un experto en formulación."
  }
}

IMPORTANTE: Usa SIEMPRE las claves exactas indicadas arriba. No uses nombres alternativos.

# REGLAS CRÍTICAS
1. NUNCA inventes datos de dosificación. Si no conoces el rango eficaz, usa web_search o indica "sin referencia clara".
2. La tipología de cada ingrediente (VITAMINA, MINERAL, etc.) debe coincidir con las categorías \
   que usará el agente regulatorio. Mantén consistencia.
3. En la matriz de interacciones, incluye SOLO pares con interacción documentada. \
   No generes pares triviales (ej: "excipiente X es neutro con vitamina Y").
4. Las sugerencias de mejora deben ser concretas y accionables, no genéricas.
5. Incluye SIEMPRE el disclaimer en metadata.
6. Responde SIEMPRE en español.

# REQUISITO DE CITAS
Para cada afirmación técnica (mecanismo de acción, dosis eficaz, interacciones, biodisponibilidad) \
indica la fuente consultada. Usa el formato [1], [2], etc. en los textos del JSON y completa \
la lista "fuentes_consultadas" con: id, fuente (nombre descriptivo), url (si web_search), \
tipo (web_search | pubmed | conocimiento_experto | base_datos).
"""