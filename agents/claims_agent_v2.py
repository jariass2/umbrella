"""
Claims + Diferenciación Agent v2 — Agente 04
Pipeline multi-agente PAYMSA / qaizn

Genera:
  - Claims regulatorios autorizados (Reglamento CE 1924/2006 / UE 432/2012)
  - Selling points comerciales (mensajes no regulados)
  - Estructura de presentación PPT (7-8 slides)
"""

from pydantic import BaseModel, Field
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────

class EstadoClaim(str, Enum):
    AUTORIZADO = "AUTORIZADO"
    EN_ESPERA = "EN_ESPERA"
    RECHAZADO = "RECHAZADO"
    ARTICULO_13_5 = "ARTICULO_13_5"
    ARTICULO_14 = "ARTICULO_14"


class TipoClaim(str, Enum):
    NUTRICIONAL = "NUTRICIONAL"
    SALUD_GENERAL = "SALUD_GENERAL"
    REDUCCION_RIESGO = "REDUCCION_RIESGO"
    DESARROLLO_NINOS = "DESARROLLO_NINOS"


# ── Output schemas ──────────────────────────────────────────────────
#
# Estructura por partes (parte_a, parte_b…) según `outputs/v2/agente_4_claims_v2.json`.


class ClaimCompuestoSugerido(BaseModel):
    model_config = {"extra": "allow"}
    texto_sugerido_etiqueta: str = ""
    condiciones: str = ""


class ClaimPorIngrediente(BaseModel):
    model_config = {"extra": "allow"}
    ingrediente: str = ""
    claims: list[dict] = Field(default_factory=list)


class ParteAClaimsRegulatorios(BaseModel):
    model_config = {"extra": "allow"}
    resumen_ejecutivo: str = ""
    claim_compuesto_sugerido: ClaimCompuestoSugerido = Field(default_factory=ClaimCompuestoSugerido)
    claims_por_ingrediente: list[ClaimPorIngrediente] = Field(default_factory=list)


class SellingPoint(BaseModel):
    model_config = {"extra": "allow"}
    titular_corto_packaging: str = ""
    descripcion_ampliada: str = ""
    ingrediente_base: str = ""
    argumento_cientifico: str = ""
    canales_uso: list[str] = Field(default_factory=list)


class ParteBSellingPoints(BaseModel):
    model_config = {"extra": "allow"}
    selling_points: list[SellingPoint] = Field(default_factory=list)


class SlidePPT(BaseModel):
    model_config = {"extra": "allow"}
    numero: int = 0
    titulo: str = ""
    bullets: list[str] = Field(default_factory=list)
    dato_destacado: str = ""
    notas_presentador: str = ""


class ParteCEstructuraPPT(BaseModel):
    model_config = {"extra": "allow"}
    slides: list[SlidePPT] = Field(default_factory=list)


class ParteDDiferenciadores(BaseModel):
    model_config = {"extra": "allow"}
    vs_competencia: list[str] = Field(default_factory=list)
    formas_quimicas_superiores: list[str] = Field(default_factory=list)
    sinergias_exclusivas: list[str] = Field(default_factory=list)
    publico_objetivo_principal: str = ""
    publico_objetivo_secundario: str = ""
    momento_consumo: str = ""
    posicionamiento_precio_valor: str = ""


class SegmentoMercado(BaseModel):
    model_config = {"extra": "allow"}
    segmento: str = ""
    necesidad_principal: str = ""
    encaje_formula: str = ""
    mensaje_clave: str = ""


class ClaimNoAplicable(BaseModel):
    model_config = {"extra": "allow"}
    claim: str = ""
    razon: str = ""


class ParteEAdvertenciasLegales(BaseModel):
    model_config = {"extra": "allow"}
    claims_no_aplicables: list[ClaimNoAplicable] = Field(default_factory=list)
    mensajes_prohibidos: list[str] = Field(default_factory=list)
    ingredientes_sin_claim: list[str] = Field(default_factory=list)


class ClaimsAnalysis(BaseModel):
    """Contrato operacional del agente Claims + Diferenciación."""
    model_config = {"extra": "allow"}

    parte_a_claims_regulatorios: ParteAClaimsRegulatorios = Field(default_factory=ParteAClaimsRegulatorios)
    parte_b_selling_points_comerciales: ParteBSellingPoints = Field(default_factory=ParteBSellingPoints)
    parte_c_estructura_ppt: ParteCEstructuraPPT = Field(default_factory=ParteCEstructuraPPT)
    parte_d_diferenciadores: ParteDDiferenciadores = Field(default_factory=ParteDDiferenciadores)
    parte_e_advertencias_legales: ParteEAdvertenciasLegales = Field(default_factory=ParteEAdvertenciasLegales)
    parte_f_segmentos_mercado: list[SegmentoMercado] = Field(default_factory=list)
    fuentes_consultadas: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=lambda: {
        "version": "2.0",
        "disclaimer": "Los claims regulatorios deben verificarse con el texto oficial vigente del Reglamento UE 432/2012 antes de su uso comercial."
    })


# ── Instructions ─────────────────────────────────────────────────────

PROMPT_VERSION = "2.1.0"  # +Parte F: segmentos de mercado estructurados

CLAIMS_INSTRUCTIONS = """\
# ROL
Eres un experto en marketing regulatorio especializado en el Reglamento (CE) 1924/2006 \
sobre declaraciones nutricionales y de propiedades saludables, y en el Reglamento (UE) 432/2012 \
(lista de claims autorizados). Conoces los límites entre lo que se puede y no se puede afirmar.

# OBJETIVO
Generar tres entregables para el producto:
A) Claims regulatorios autorizados con su referencia exacta
B) Selling points comerciales diferenciadores (mensajes de marketing, NO claims regulados)
C) Estructura de presentación PPT de 7-8 diapositivas

# PROCESO (sigue estas fases en orden)

## FASE 1 — Revisión de claims regulatorios (Parte A)
Para cada ingrediente activo de la fórmula:

1. Busca en el Reglamento (UE) 432/2012 los claims autorizados aplicables
2. Para cada claim encontrado, recoge:
   - Texto EXACTO del claim autorizado (no parafrasees)
   - Tipo: NUTRICIONAL | SALUD_GENERAL | REDUCCION_RIESGO | DESARROLLO_NINOS
   - Estado: AUTORIZADO / EN_ESPERA / RECHAZADO / ARTICULO_13_5 / ARTICULO_14
   - Condición de uso obligatoria (ej: "solo si el producto aporta al menos X mg/día")
   - Dosis mínima requerida para el claim
   - Referencia EFSA o ID europeo
3. Incluye SOLO claims directamente aplicables a los ingredientes presentes en la fórmula
4. Si un claim requiere dosis que la fórmula no alcanza, indícalo explícitamente

Para vitaminas y minerales estándar (vitamina B1, B2, B5, B6, B12, folato, zinc, magnesio, hierro, vitamina K) \
usa EXCLUSIVAMENTE tu conocimiento del Reglamento UE 432/2012 — son claims estables y bien documentados. \
NO hagas búsquedas para estos ingredientes.

Usa `web_search` para verificar el estado actual de claims de ingredientes no estándar o con estatus incierto \
(ej: AKBA/Boswellia, astaxantina, péptidos de colágeno, ácido hialurónico).

Para cada claim, indica explícitamente si la dosis presente en la fórmula cubre o no el mínimo requerido \
para poder usar ese claim (campo `aplica_a_formula`: true/false + explicación).

## FASE 2 — Selling points comerciales (Parte B)
Genera 5-7 argumentos comerciales diferenciadores:
- Deben ser mensajes de marketing PERMITIDOS (no claims regulatorios)
- Pueden destacar la combinación sinérgica, la calidad de las formas químicas, el target, el momento de uso
- Para cada selling point incluye:
  - Titular corto para packaging (máx 8 palabras)
  - Descripción ampliada (2-3 frases)
  - Ingrediente o combinación que lo justifica
  - Argumento científico de respaldo (mecanismo o evidencia, sin citar claims regulados)
  - Canales de uso recomendados (packaging, web, redes, prescriptores)
- NUNCA mezcles selling points con claims regulados en la misma frase

## FASE 3 — Diferenciadores vs. competencia (Parte D)
Analiza en qué se diferencia este producto de otros del mercado:
- Formas químicas superiores vs. estándar de mercado (ej: bisglicinato vs sulfato)
- Combinaciones sinérgicas exclusivas de esta fórmula
- Dosificación vs. competidores habituales
- Público objetivo principal y secundario
- Momento óptimo de consumo y por qué
- Posicionamiento de precio/valor recomendado

## FASE 4 — Estructura PPT (Parte C)
Diseña la estructura de una presentación de 7-8 diapositivas para distribuidores, farmacias o prescriptores:
- Slide 1: Portada y posicionamiento de marca
- Slide 2: El problema / necesidad del mercado (datos epidemiológicos si los conoces)
- Slide 3: La solución — perfil funcional del producto
- Slide 4: Los ingredientes clave y su ciencia (mecanismos, evidencia)
- Slide 5: Claims regulatorios y respaldo normativo
- Slide 6: Diferenciadores vs. competencia
- Slide 7: Target, momento de consumo y pauta
- Slide 8: Call to action / próximos pasos comerciales

Para cada slide: título, 3-5 bullets concretos, dato o claim destacado (cifra, frase de impacto), \
notas del presentador con contexto adicional.

## FASE 5 — Advertencias legales (Parte E)
Lista explícitamente:
- Claims que NO pueden usarse y por qué (no autorizados, dosis insuficiente, afirmación médica)
- Ingredientes sin claim autorizado que podrían generar confusión
- Mensajes de venta que deben evitarse en etiqueta o publicidad

## FASE 6 — Segmentos de mercado (Parte F)
Identifica 2-4 segmentos de mercado concretos para los que la fórmula encaja bien. \
Para cada uno indica: nombre del segmento, necesidad principal que cubre (jobs-to-be-done), \
por qué la fórmula encaja con ese segmento y el mensaje comercial clave. Sé específico para \
ESTA fórmula (no segmentos genéricos); apóyate en el público objetivo de la Parte D.

# USO DE HERRAMIENTAS DE BÚSQUEDA
LÍMITE ESTRICTO: MÁXIMO 5 búsquedas en total (entre `web_search` y `search_pubmed`).

- `web_search`: solo para verificar el estado actual (autorizado/rechazado/pendiente) de un claim \
  de un ingrediente NO estándar (Boswellia, astaxantina, colágeno, ácido hialurónico).
- `search_pubmed`: NO usar — los claims regulatorios no están en PubMed.
- Para vitaminas, minerales y aminoácidos estándar: usa tu conocimiento interno. No busques.

Si no estás seguro de un claim concreto, márcalo como EN_ESPERA en lugar de buscar.

# FORMATO DE SALIDA
Responde SIEMPRE como JSON válido, sin fences markdown, sin texto antes ni después.
Usa EXACTAMENTE estas claves de nivel superior:

{
  "parte_a_claims_regulatorios": {
    "resumen_ejecutivo": "Resumen ejecutivo de los claims disponibles y su aplicabilidad a la fórmula",
    "claim_compuesto_sugerido": {
      "texto_sugerido_etiqueta": "Texto del claim compuesto que puede usarse en etiqueta",
      "condiciones": "Condiciones que deben cumplirse para usarlo"
    },
    "claims_por_ingrediente": [
      {
        "ingrediente": "nombre del ingrediente",
        "claims": [
          {
            "texto_claim": "Texto oficial del claim en idioma original",
            "texto_traduccion_es": "Traducción al español",
            "tipo": "NUTRICIONAL | SALUD_GENERAL | REDUCCION_RIESGO | DESARROLLO_NINOS",
            "estado": "AUTORIZADO | EN_ESPERA | RECHAZADO | ARTICULO_13_5 | ARTICULO_14",
            "condicion_uso": "Condición obligatoria para poder usar el claim",
            "dosis_minima_requerida": "Dosis mínima que exige el claim",
            "aplica_a_formula": true,
            "aplica_explicacion": "Por qué sí/no aplica dado la dosis presente en la fórmula",
            "referencia_efsa": "Ref. EFSA o ID en UE 432/2012"
          }
        ]
      }
    ]
  },
  "parte_b_selling_points_comerciales": {
    "selling_points": [
      {
        "titular_corto_packaging": "Título corto (max 8 palabras)",
        "descripcion_ampliada": "Descripción ampliada (2-3 frases)",
        "ingrediente_base": "Ingrediente o combinación que lo justifica",
        "argumento_cientifico": "Mecanismo o evidencia de respaldo (sin citar claims regulados)",
        "canales_uso": ["packaging", "web", "redes_sociales", "prescriptores"]
      }
    ]
  },
  "parte_c_estructura_ppt": {
    "slides": [
      {
        "numero": 1,
        "titulo": "Título del slide",
        "bullets": ["bullet 1", "bullet 2", "bullet 3"],
        "dato_destacado": "Cifra, claim o frase de impacto para el slide",
        "notas_presentador": "Contexto adicional para quien presenta"
      }
    ]
  },
  "parte_d_diferenciadores": {
    "vs_competencia": ["ventaja 1 vs productos similares", "ventaja 2"],
    "formas_quimicas_superiores": ["ej: bisglicinato de hierro vs sulfato ferroso"],
    "sinergias_exclusivas": ["combinación sinérgica destacada de esta fórmula"],
    "publico_objetivo_principal": "Descripción del target primario",
    "publico_objetivo_secundario": "Descripción del target secundario si existe",
    "momento_consumo": "Cuándo y cómo consumir para maximizar el efecto",
    "posicionamiento_precio_valor": "Segmento de precio recomendado y justificación"
  },
  "parte_e_advertencias_legales": {
    "claims_no_aplicables": [
      {
        "claim": "Texto del claim no aplicable",
        "razon": "Por qué no puede usarse (dosis insuficiente, no autorizado, etc.)"
      }
    ],
    "mensajes_prohibidos": ["Mensaje de venta que debe evitarse y por qué"],
    "ingredientes_sin_claim": ["Ingredientes presentes sin claim autorizado aplicable"]
  },
  "parte_f_segmentos_mercado": [
    {
      "segmento": "Nombre del segmento (ej: Senior activo 60+)",
      "necesidad_principal": "Necesidad/jobs-to-be-done que cubre la fórmula para ese segmento",
      "encaje_formula": "Por qué esta fórmula encaja con ese segmento",
      "mensaje_clave": "Mensaje comercial principal para ese segmento"
    }
  ],
  "fuentes_consultadas": [
    {"id": 1, "fuente": "nombre descriptivo", "url": "", "tipo": "web_search|normativa|conocimiento_experto"}
  ],
  "metadata": {
    "version": "2.0",
    "disclaimer": "Los claims regulatorios deben verificarse con el texto oficial vigente del Reglamento UE 432/2012 antes de su uso comercial."
  }
}

IMPORTANTE: Usa SIEMPRE las claves exactas indicadas arriba.

# REGLAS CRÍTICAS
1. NUNCA inventes claims. Si no encuentras el claim en 432/2012, no lo incluyas.
2. Distingue SIEMPRE entre claims regulados (Parte A) y mensajes de marketing (Parte B). Nunca mezcles.
3. Para cada claim, rellena `aplica_a_formula` (true/false) y `aplica_explicacion` con la dosis presente vs. mínima requerida.
4. Los textos de claims deben ser los oficiales. Incluye siempre `texto_traduccion_es`.
5. La Parte C (PPT) debe tener exactamente 7-8 slides con bullets concretos, no genéricos.
6. La Parte D (diferenciadores) debe ser específica para esta fórmula, no descripciones genéricas del mercado.
7. Incluye el disclaimer en metadata.
8. Responde SIEMPRE en español (excepto el texto oficial de los claims, que va en idioma original + traducción).
9. CITAS OBLIGATORIAS: incluye la clave "fuentes_consultadas" con todas las fuentes consultadas.
   Si no consultaste fuentes externas, incluye la clave con array vacío [].
"""
