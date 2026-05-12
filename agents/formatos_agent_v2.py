"""
Formatos e Innovación Agent v2 — Agente 06
Pipeline multi-agente PAYMSA / qaizn

Propone y evalúa formatos de presentación (sticks, cápsulas, vial, etc.),
compara con mercado y recomienda el formato óptimo con ingredientes diferenciadores.
"""

from typing import Any
from pydantic import BaseModel, Field
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────

class TipoFormato(str, Enum):
    STICK_POLVO = "STICK_POLVO"
    CAPSULA_DURA = "CAPSULA_DURA"
    CAPSULA_BLANDA = "CAPSULA_BLANDA"
    COMPRIMIDO = "COMPRIMIDO"
    COMPRIMIDO_EFERVESCENTE = "COMPRIMIDO_EFERVESCENTE"
    VIAL_LIQUIDO = "VIAL_LIQUIDO"
    SOBRE_ALUMINIO = "SOBRE_ALUMINIO"
    POT_VIDRIO = "POT_VIDRIO"
    GOMINOLA = "GOMINOLA"
    SPRAY_ORAL = "SPRAY_ORAL"
    OTRO = "OTRO"


class NivelCompatibilidad(str, Enum):
    EXCELENTE = "EXCELENTE"
    BUENA = "BUENA"
    ACEPTABLE = "ACEPTABLE"
    PROBLEMATICA = "PROBLEMATICA"
    INCOMPATIBLE = "INCOMPATIBLE"


class NivelCoste(str, Enum):
    MUY_BAJO = "MUY_BAJO"
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    MUY_ALTO = "MUY_ALTO"


# ── Output schemas ──────────────────────────────────────────────────
#
# Estructura por fases según `outputs/v2/agente_6_formatos_v2.json`.


class FilaTablaFormato(BaseModel):
    """Fila de comparativa. Campos `Any` porque el LLM mezcla strings y floats."""
    model_config = {"extra": "allow"}
    formato: str = ""
    puntuacion: Any = ""
    coste: Any = ""
    compatibilidad: Any = ""
    ventajas_clave: Any = ""  # str | list[str]
    desventajas_clave: Any = ""  # str | list[str]


class Fase1EvaluacionFormatos(BaseModel):
    model_config = {"extra": "allow"}
    tabla_comparativa_resumen: list[FilaTablaFormato] = Field(default_factory=list)


class MarcaLider(BaseModel):
    model_config = {"extra": "allow"}
    marca: str = ""
    formato: str = ""
    posicionamiento: str = ""


class Fase2AnalisisCompetencia(BaseModel):
    model_config = {"extra": "allow"}
    formato_predominante: str = ""
    marcas_lideres: list[MarcaLider] = Field(default_factory=list)
    tendencias_2024_2025: list[str] = Field(default_factory=list)
    oportunidades_diferenciacion: str = ""


class Fase3InnovacionIngredientes(BaseModel):
    model_config = {"extra": "allow"}
    propuesta_innovacion: str = ""
    ingredientes_diferenciadores: list[str] = Field(default_factory=list)
    formas_quimicas_premium: list[str] = Field(default_factory=list)
    combinaciones_sinergicas: list[str] = Field(default_factory=list)


class FormatoOptimo(BaseModel):
    model_config = {"extra": "allow"}
    nombre: str = ""
    justificacion_tecnica: str = ""
    justificacion_comercial: str = ""
    condiciones_exito: list[str] = Field(default_factory=list)


class FormatoAlternativo(BaseModel):
    model_config = {"extra": "allow"}
    nombre: str = ""
    escenario: str = ""


class Fase4RecomendacionFinal(BaseModel):
    model_config = {"extra": "allow"}
    formato_optimo: FormatoOptimo = Field(default_factory=FormatoOptimo)
    formato_alternativo: FormatoAlternativo = Field(default_factory=FormatoAlternativo)
    condiciones_cambio_formato_futuro: list[str] = Field(default_factory=list)


class FormatosAnalysis(BaseModel):
    """Contrato operacional del agente Formatos e Innovación."""
    model_config = {"extra": "allow"}

    fase_1_evaluacion_formatos: Fase1EvaluacionFormatos = Field(default_factory=Fase1EvaluacionFormatos)
    fase_2_analisis_competencia: Fase2AnalisisCompetencia = Field(default_factory=Fase2AnalisisCompetencia)
    fase_3_innovacion_ingredientes: Fase3InnovacionIngredientes = Field(default_factory=Fase3InnovacionIngredientes)
    fase_4_recomendacion_final: Fase4RecomendacionFinal = Field(default_factory=Fase4RecomendacionFinal)
    fuentes_consultadas: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=lambda: {
        "version": "2.0",
        "disclaimer": "Las estimaciones de coste y caducidad son orientativas y deben verificarse con los proveedores de Umbrella Group."
    })


# ── Instructions ─────────────────────────────────────────────────────

PROMPT_VERSION = "2.0.0"

FORMATOS_INSTRUCTIONS = """\
# ROL
Eres un experto en desarrollo de producto de complementos alimentarios, especializado en \
formatos de administración, posicionamiento de mercado y ciclo de vida del producto. \
Conoces las implicaciones técnicas, logísticas y comerciales de cada formato.

# OBJETIVO
Proponer y evaluar los formatos de presentación más adecuados para el producto, \
comparar con el mercado actual, identificar ingredientes diferenciadores y recomendar \
el formato óptimo con justificación técnica y comercial.

# PROCESO (sigue estas fases en orden)

## FASE 1 — Evaluación de formatos candidatos
Para el producto recibido, evalúa al menos 5 formatos candidatos entre:
- Stick de polvo (monodosis)
- Cápsula dura (vegetal o gelatina)
- Comprimido recubierto / comprimido efervescente
- Vial líquido (bebible)
- Sobre de aluminio (polvo o granulado)
- Pot de vidrio o HDPE (polvo o granulado a granel)
- Gominola / formato masticable
- Spray oral

Para cada formato analiza:

### 1a. Compatibilidad con la fórmula
- Reactividad química de los ingredientes activos con el material de envase
- Sensibilidad a humedad, luz, oxígeno, temperatura
- Caducidad esperada en ese formato
- Requisitos de encapsulación, recubrimiento o atmósfera modificada

### 1b. Target y momento de consumo
- Perfil de consumidor más adecuado para ese formato
- Momento de consumo óptimo
- Canal de distribución natural

### 1c. Imagen y posicionamiento
- Percepción del consumidor (premium, funcional, farmacéutico, lifestyle)
- Compatibilidad con la marca y el posicionamiento objetivo

### 1d. Logística
- Envase primario y secundario
- Fragilidad en transporte
- Condiciones y coste de almacenaje

### 1e. Coste relativo
- Escala: MUY_BAJO / BAJO / MEDIO / ALTO / MUY_ALTO
- Comparativa relativa entre formatos (no precio absoluto)

Asigna una puntuación global 0-10 a cada formato.

## FASE 2 — Análisis de competencia y tendencias
Usa web_search para investigar:
- ¿Cuál es el formato predominante para productos inmunitarios (vitamina C + zinc + D3)?
- ¿Qué marcas líderes existen y qué formato usan?
- ¿Cuál es la tendencia emergente en este segmento (2023-2025)?
- Oportunidades de diferenciación por formato

Consultas sugeridas:
- "immune supplement vitamin C zinc D3 format market trends 2024"
- "complemento inmunidad vitamina C zinc formato mercado España"
- "immune complex supplement stick sachets capsules market Spain pharmacy"

## FASE 3 — Innovación de ingredientes
Analiza cómo esta fórmula se diferencia de productos similares en el mercado:
- Formas químicas premium vs. estándar (ej: zinc gluconato vs. zinc óxido)
- Combinaciones sinérgicas poco habituales
- Dosificación vs. competidores
- Narrativa de innovación para comunicación

## FASE 4 — Recomendación final
Con toda la información anterior:
1. Recomienda el formato óptimo con justificación detallada
2. Propón un formato alternativo para escenarios diferentes (ej: menor coste, target diferente)
3. Indica condiciones para cambiar de formato en el futuro (ej: si se amplía la gama)

# USO DE WEB_SEARCH
Usa web_search con moderación. Límite: MÁXIMO 1 búsqueda en total.
Solo busca tendencias de mercado si necesitas datos actualizados de 2024-2025 para la Fase 2. \
NO busques estabilidad de ingredientes por formato — usa tu conocimiento técnico.

# FORMATO DE SALIDA
Responde SIEMPRE como JSON válido, sin fences markdown, sin texto antes ni después.
Usa EXACTAMENTE estas claves de nivel superior:

{
  "fase_1_evaluacion_formatos": {
    "tabla_comparativa_resumen": [
      {
        "formato": "Stick de polvo monodosis",
        "puntuacion": 8.5,
        "coste": "MEDIO",
        "compatibilidad": "Descripción breve",
        "ventajas_clave": ["ventaja 1", "ventaja 2"],
        "desventajas_clave": ["desventaja 1"]
      }
    ]
  },
  "fase_3_innovacion_ingredientes": {
    "propuesta_innovacion": "Narrativa de innovación para el producto",
    "ingredientes_diferenciadores": ["ingrediente diferenciador 1", "ingrediente diferenciador 2"],
    "formas_quimicas_premium": ["forma química premium 1"],
    "combinaciones_sinergicas": ["combinación sinérgica 1"]
  },
  "fase_4_recomendacion_final": {
    "formato_optimo": {
      "nombre": "Stick monodosis 3g",
      "justificacion_tecnica": "Justificación técnica del formato óptimo",
      "justificacion_comercial": "Justificación comercial",
      "condiciones_exito": ["condición 1", "condición 2"]
    },
    "formato_alternativo": {
      "nombre": "Cápsula dura vegetal",
      "escenario": "Alternativa para menor coste o target diferente"
    }
  },
  "fuentes_consultadas": [
    {"id": 1, "fuente": "nombre", "url": "", "tipo": "web_search|normativa|conocimiento_experto"}
  ],
  "metadata": {
    "version": "2.0",
    "disclaimer": "Las estimaciones de coste y caducidad son orientativas y deben verificarse con los proveedores de Umbrella Group."
  }
}

IMPORTANTE: Usa SIEMPRE las claves exactas indicadas arriba.

# REGLAS CRÍTICAS
1. Evalúa al menos 5 formatos distintos.
2. Las puntuaciones deben ser coherentes entre sí (no des 9/10 a todos).
3. El formato recomendado debe estar entre los evaluados.
4. Los costes son RELATIVOS entre formatos, no absolutos.
5. Responde SIEMPRE en español.
6. CITAS OBLIGATORIAS: incluye la clave "fuentes_consultadas" a nivel raíz con lista completa:
   [{"id": N, "fuente": "nombre", "url": "url o vacío", "tipo": "web_search|normativa|conocimiento_experto"}].
   Si no consultaste fuentes externas, incluye igualmente la clave con array vacío [].
"""
