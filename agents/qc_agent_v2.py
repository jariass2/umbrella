"""
QC Interno Agent v2 — Agente 08
Pipeline multi-agente PAYMSA / qaizn

Define el plan de control de calidad completo:
  - Especificaciones analíticas (FTIR, granulometría, densidad, pH, aspecto)
  - Plan de estabilidad (ICH Q1A(R2))
  - Métodos y criterios de aceptación por parámetro
"""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────

class FrecuenciaControl(str, Enum):
    CADA_LOTE = "CADA_LOTE"
    CADA_5_LOTES = "CADA_5_LOTES"
    MENSUAL = "MENSUAL"
    TRIMESTRAL = "TRIMESTRAL"
    SEMESTRAL = "SEMESTRAL"
    ANUAL = "ANUAL"
    INICIO_PRODUCCION = "INICIO_PRODUCCION"


class TipoEnsayo(str, Enum):
    IDENTIDAD = "IDENTIDAD"
    PUREZA = "PUREZA"
    CONTENIDO = "CONTENIDO"
    FISICOQUIMICO = "FISICOQUIMICO"
    MICROBIOLOGICO = "MICROBIOLOGICO"
    ORGANOLÉPTICO = "ORGANOLÉPTICO"
    FUNCIONAL = "FUNCIONAL"


class ResultadoEstabilidad(str, Enum):
    CONFORME = "CONFORME"
    FUERA_ESPECIFICACION = "FUERA_ESPECIFICACION"
    MARGINALMENTE_CONFORME = "MARGINALMENTE_CONFORME"
    PENDIENTE = "PENDIENTE"


# ── Output schemas ──────────────────────────────────────────────────
#
# Estructura por fases según `outputs/v2/agente_8_qc_v2.json`. Las
# fases tienen sub-estructuras heterogéneas (dicts con claves variables
# por ingrediente), así que validamos el nivel-1 y usamos `extra='allow'`
# para preservar el detalle.


class Fase1FTIR(BaseModel):
    model_config = {"extra": "allow"}
    objetivo: str = ""
    metodologia_general: dict = Field(default_factory=dict)
    control_mix_final: dict = Field(default_factory=dict)
    espectros_referencia: dict = Field(default_factory=dict)


class Fase2Granulometria(BaseModel):
    model_config = {"extra": "allow"}
    objetivo: str = ""
    metodo_primario: dict = Field(default_factory=dict)
    especificaciones_por_ingrediente: dict = Field(default_factory=dict)
    especificaciones_mix_final: dict = Field(default_factory=dict)
    frecuencia: str = ""


class Fase3Densidad(BaseModel):
    model_config = {"extra": "allow"}
    objetivo: str = ""
    metodos: dict = Field(default_factory=dict)
    especificaciones_numericas: dict = Field(default_factory=dict)
    indices_reologia: dict = Field(default_factory=dict)
    frecuencia: str = ""


class Fase4PH(BaseModel):
    model_config = {"extra": "allow"}
    objetivo: str = ""
    rango_esperado: dict = Field(default_factory=dict)
    especificacion_aceptacion: str = ""
    metodo: dict = Field(default_factory=dict)
    impacto_ph_fuera_rango: dict = Field(default_factory=dict)
    frecuencia: str = ""


class Fase5AspectoOrganoleptico(BaseModel):
    model_config = {"extra": "allow"}
    descripcion_producto: str = ""
    criterios_aceptacion: dict = Field(default_factory=dict)
    metodo_inspeccion: dict = Field(default_factory=dict)
    frecuencia: str = ""


class Fase6EnsayosAnaliticosAdicionales(BaseModel):
    model_config = {"extra": "allow"}
    cuantificacion_activos: list[dict] = Field(default_factory=list)
    uniformidad_contenido: dict = Field(default_factory=dict)
    humedad: dict = Field(default_factory=dict)
    metales_pesados: dict = Field(default_factory=dict)
    microbiologia: dict = Field(default_factory=dict)


class VidaUtilEstimadaQC(BaseModel):
    model_config = {"extra": "allow"}
    objetivo_meses: Optional[int] = None
    alcanzable: Optional[bool] = None
    condiciones_para_alcanzabilidad: str = ""


class Fase7PlanEstabilidad(BaseModel):
    model_config = {"extra": "allow"}
    zona_climatica: str = ""
    numero_lotes: Optional[int] = None
    vida_util_estimada: VidaUtilEstimadaQC = Field(default_factory=VidaUtilEstimadaQC)
    formato_envase_recomendado: str = ""
    condiciones_estudio: list[dict] = Field(default_factory=list)
    cronograma_estudio: dict = Field(default_factory=dict)
    criterios_fin_vida_util: list[dict] = Field(default_factory=list)
    ingredientes_criticos_estabilidad: list[dict] = Field(default_factory=list)


class PlanQCAnalysis(BaseModel):
    """Contrato operacional del agente QC Interno."""
    model_config = {"extra": "allow"}

    fase_1_ftir: Fase1FTIR = Field(default_factory=Fase1FTIR)
    fase_2_granulometria: Fase2Granulometria = Field(default_factory=Fase2Granulometria)
    fase_3_densidad: Fase3Densidad = Field(default_factory=Fase3Densidad)
    fase_4_ph: Fase4PH = Field(default_factory=Fase4PH)
    fase_5_aspecto_organoleptico: Fase5AspectoOrganoleptico = Field(default_factory=Fase5AspectoOrganoleptico)
    fase_6_ensayos_analiticos_adicionales: Fase6EnsayosAnaliticosAdicionales = Field(default_factory=Fase6EnsayosAnaliticosAdicionales)
    fase_7_plan_estabilidad: Fase7PlanEstabilidad = Field(default_factory=Fase7PlanEstabilidad)
    fase_8_resumen_ejecutivo: str = ""
    fuentes_consultadas: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=lambda: {
        "version": "2.0",
        "disclaimer": "Este plan QC es orientativo. Los métodos y criterios deben validarse internamente antes de su implementación."
    })


# ── Instructions ─────────────────────────────────────────────────────

PROMPT_VERSION = "2.0.0"

QC_INSTRUCTIONS = """\
# ROL
Eres un experto en control de calidad de complementos alimentarios, con conocimientos profundos \
en farmacopea europea (Ph. Eur.), ICH (especialmente Q1A, Q2, Q6), normativa de estabilidad \
y métodos analíticos para matrices de polvo y formas sólidas.

# OBJETIVO
Definir el plan de control de calidad completo para el producto, incluyendo especificaciones \
analíticas para todas las pruebas clave y un plan de estabilidad conforme a ICH Q1A(R2).

# PROCESO (sigue estas fases en orden)

## FASE 1 — FTIR (Espectroscopía Infrarroja por Transformada de Fourier)
Define el protocolo de análisis FTIR para:
- Identificación de materias primas: cada ingrediente activo debe compararse con espectro de referencia
- Control de identidad del mix final
- Umbral de similitud para aceptación (ej: índice de correlación ≥0,98)
- Detección de adulteraciones o sustituciones

Para cada ingrediente activo indica qué picos característicos se verificarán:
- Vitamina C: carbonilo ester ~1750 cm⁻¹, OH alcohólico ~3400 cm⁻¹
- Zinc gluconato: carboxilato ~1600 cm⁻¹, C-O ~1080 cm⁻¹
- Vitamina D3 (colecalciferol): C=C conjugado ~1640 cm⁻¹, OH ~3400 cm⁻¹

Apóyate en tu conocimiento espectroscópico. Si un ingrediente poco habitual tiene picos \
FTIR que no domines con certeza, decláralo en "espectros_referencia" como pendiente de \
caracterización contra patrón en lugar de inventar valores concretos.

## FASE 2 — Granulometría
Define las especificaciones de tamaño de partícula para el producto en polvo:
- D10: límite inferior de la distribución (finos)
- D50: tamaño mediano — impacta en fluidez y dosificación
- D90: límite superior — impacta en homogeneidad y segregación
- Criterio de homogeneidad del mix (ej: RSD ≤5% en 10 puntos de muestreo)
- Método: tamizado en seco (ISO 3310) o difracción láser (ISO 13320)

Considera que los ingredientes vitamínicos habitualmente tienen granulometría fina (D50 <100μm) \
y son compatibles con mezcla por orden de incorporación decreciente por tamaño.

## FASE 3 — Densidad
Para polvo granulado o mezcla en polvo:
- Densidad aparente (bulk density): rango esperado para esta tipología
- Densidad compactada (tapped density): tras 1250 golpes (Ph. Eur. 2.9.34)
- Índice de Carr (compresibilidad): (<15% = excelente fluidez, 15-20% = buena, >25% = difícil)
- Índice de Hausner: <1.25 recomendado para polvo de libre flujo

Para complementos vitamínicos en polvo, los rangos habituales son:
- Densidad aparente: 0,40-0,70 g/cm³
- Índice de Carr: <20%

## FASE 4 — pH
Para el mix en polvo o en solución (si se reconstituye):
- pH de suspensión al 1% o 5% en agua destilada
- Temperatura de medición: 20±2°C
- Rango aceptable y su justificación técnica
- Impacto del pH fuera de rango en la estabilidad de cada activo:
  - Vitamina C: estable a pH 4-6; se degrada rápidamente a pH >7 o pH <3
  - Zinc gluconato: soluble a pH 4-8
  - Vitamina D3: estable en medio neutro-ligeramente ácido

## FASE 5 — Aspecto y características organolépticas
Define los criterios organolépticos del producto final:
- Color: descripción (ej: "polvo blanco a blanco-amarillento")
- Olor: descripción (ej: "inodoro a ligeramente característico")
- Textura: (ej: "polvo fino y homogéneo, sin aglomerados")
- Criterio de rechazo: (ej: "polvo con apelmazamiento >10%, decoloración, olor rancio")

## FASE 6 — Ensayos analíticos adicionales
Incluye los ensayos adicionales necesarios para un complemento alimentario:
- Cuantificación de activos por HPLC o UV-Vis (vitamina C, D3, zinc)
- Microbiología: recuento total de aerobios mesófilos, levaduras/mohos, Salmonella, E. coli
  (según Reglamento CE 2073/2005 y criterios internos)
- Metales pesados: Pb, Cd, Hg, As (si aplica según ingredientes)
- Humedad/pérdida por desecación (< X% según el producto)
- Ensayo de uniformidad de contenido (por dosis)

Para cada ensayo: método, especificación, frecuencia, referencia normativa.

## FASE 7 — Plan de estabilidad (ICH Q1A(R2))
Diseña el plan de estabilidad:

### Condiciones de estudio:
- Larga duración: 25°C ± 2°C / 60% HR ± 5% (ICH zona II)
- Acelerado: 40°C ± 2°C / 75% HR ± 5%
- Fotodegradación: ICH Q1B si el producto es fotosensible

### Puntos de tiempo:
- T=0, T=3m, T=6m, T=9m, T=12m, T=18m, T=24m (larga duración)
- T=0, T=3m, T=6m (acelerado)

### Parámetros a monitorizar en cada punto:
- Aspecto, color, olor
- pH
- Humedad
- Cuantificación de activos (vitamina C, D3, zinc): límite ≥90% del valor declarado
- Microbiología: control en T=0 y T=12m mínimo

### Criterios de fin de vida:
- Descenso de activo por debajo del 90% del valor declarado en etiqueta
- Cambio organoléptico inaceptable
- Contaminación microbiológica fuera de especificación

Número mínimo de lotes para el estudio: 3 (por ICH Q1A).
Objetivo de vida útil: 24 meses (indicar si es alcanzable con el formato y formulación).

## FASE 8 — Resumen ejecutivo del plan QC
Redacta un párrafo de resumen para el equipo de producción con:
- Los controles más críticos y su justificación
- Frecuencia de muestreo recomendada por lote
- Puntos de atención especial (ej: termolabilidad de vitamina C, fotosensibilidad de D3)

# USO DE WEB_SEARCH
NO uses web_search. Este agente no tiene acceso a herramientas externas. Apóyate en tu \
conocimiento técnico (Ph. Eur., ICH Q1A/Q1B/Q2, ISO 13320, criterios microbiológicos \
Reg. CE 2073/2005). Si dudas de un valor concreto, decláralo como pendiente de \
verificación contra farmacopea/patrón en lugar de inventarlo.

# FORMATO DE SALIDA
Responde SIEMPRE como JSON válido, sin fences markdown, sin texto antes ni después.
Usa EXACTAMENTE estas claves de nivel superior:

{
  "fase_1_ftir": {
    "objetivo": "Identificación de materias primas y control de mix final",
    "metodologia_general": {"nombre": "FTIR-ATR", "tecnica": "Espectroscopía infrarroja por transformada de Fourier", "equipo": "FTIR con cristal ATR"},
    "control_mix_final": {"criterio_aceptacion": "Índice de correlación ≥0,98 vs espectro de referencia"},
    "espectros_referencia": {
      "Vitamina C": {"picos_principales": [{"numero_onda": "1750", "asignacion": "Carbonilo ester"}, {"numero_onda": "3400", "asignacion": "OH alcohólico"}], "criterio_aceptacion": "Concordancia ≥95%"}
    }
  },
  "fase_2_granulometria": {
    "objetivo": "Control del tamaño de partícula para fluidez y homogeneidad",
    "metodo_primario": {"nombre": "Difracción láser", "equipo": "ISO 13320"},
    "especificaciones_por_ingrediente": {},
    "frecuencia": "CADA_LOTE"
  },
  "fase_3_densidad": {
    "objetivo": "Control de fluidez del polvo",
    "metodos": {"densidad_aparente": {"nombre": "Densidad aparente", "tecnica": "Ph. Eur. 2.9.15"}},
    "indices_reologia": {"indice_carr": {"rango_especificacion": "<20%"}},
    "frecuencia": "CADA_LOTE"
  },
  "fase_4_ph": {
    "objetivo": "Control de pH del mix",
    "rango_esperado": {"ph_esperado": "5.0-7.0"},
    "especificacion_aceptacion": "pH 5.0-7.0 en suspensión al 5%",
    "metodo": {"nombre": "Potenciometría", "tecnica": "pH metro calibrado"},
    "frecuencia": "CADA_LOTE"
  },
  "fase_5_aspecto_organoleptico": {
    "descripcion_producto": "Polvo de color blanco a amarillento",
    "criterios_aceptacion": {"capsula": {"color": "Blanco a crema", "criterio_rechazo": "Decoloración, apelmazamiento"}},
    "metodo_inspeccion": {"nombre": "Inspección visual", "tecnica": "Personal entrenado"},
    "frecuencia": "CADA_LOTE"
  },
  "fase_6_ensayos_analiticos_adicionales": {
    "cuantificacion_activos": [
      {"parametro": "Vitamina C por HPLC", "justificacion": "Control de contenido de activo principal", "especificacion": "90-110% del valor declarado", "metodo": "HPLC-UV Ph. Eur.", "frecuencia": "CADA_LOTE"}
    ],
    "microbiologia": {
      "criterios_microbiologicos": [
        {"parametro": "Recuento aerobios mesófilos", "criterio": "<1000 UFC/g", "frecuencia": "CADA_LOTE"}
      ]
    }
  },
  "fase_7_plan_estabilidad": {
    "zona_climatica": "II (25°C/60% HR)",
    "numero_lotes": 3,
    "vida_util_estimada": {"objetivo_meses": 24, "alcanzable": true},
    "condiciones_estudio": [
      {"tipo": "Larga duración", "temperatura": "25°C", "humedad_relativa": "60%", "duracion": "24 meses"},
      {"tipo": "Acelerado", "temperatura": "40°C", "humedad_relativa": "75%", "duracion": "6 meses"}
    ],
    "cronograma_estudio": {
      "puntos_tiempo": [
        {"tiempo": "T=0", "condicion": "Larga duración", "parametros_monitorizados": ["Aspecto", "pH", "Humedad", "Contenido de activos", "Microbiología"]},
        {"tiempo": "T=3m", "condicion": "Acelerado", "parametros_monitorizados": ["Aspecto", "pH", "Humedad", "Contenido de activos"]}
      ]
    },
    "criterios_fin_vida_util": [
      {"criterio": "Contenido de activos", "descripcion": "Descenso por debajo del 90% del valor declarado en etiqueta"},
      {"criterio": "Cambio organoléptico", "descripcion": "Decoloración, olor rancido, apelmazamiento significativo"}
    ]
  },
  "fase_8_resumen_ejecutivo": "Texto de resumen ejecutivo del plan QC para el equipo de producción",
  "fuentes_consultadas": [
    {"id": 1, "fuente": "nombre", "url": "", "tipo": "web_search|normativa|conocimiento_experto"}
  ],
  "metadata": {
    "version": "2.0",
    "disclaimer": "Este plan QC es orientativo. Los métodos y criterios deben validarse internamente antes de su implementación."
  }
}

IMPORTANTE: Usa SIEMPRE las claves exactas indicadas arriba.

# REGLAS CRÍTICAS
1. Los criterios de aceptación deben ser específicos y medibles (no "dentro de rango esperado").
2. Incluye referencias normativas exactas (Ph. Eur. X.X.X, ICH Q1A(R2), ISO XXXX).
3. Los límites microbiológicos deben ser coherentes con el Reglamento CE 2073/2005.
4. Para el contenido de activos: el límite mínimo habitual es ≥90% del valor declarado en etiqueta.
5. Responde SIEMPRE en español.
6. CITAS OBLIGATORIAS: incluye la clave "fuentes_consultadas" a nivel raíz con lista completa:
   [{"id": N, "fuente": "nombre", "url": "url o vacío", "tipo": "web_search|normativa|conocimiento_experto"}].
   Si no consultaste fuentes externas, incluye igualmente la clave con array vacío [].
"""
