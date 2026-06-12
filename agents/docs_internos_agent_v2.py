"""
Documentación Interna Agent v2 — Agente 07
Pipeline multi-agente PAYMSA / qaizn

Genera documentación interna de producción:
  - Lista de Materiales (L.M.) estilo NAVISION
  - Fórmula cuantitativa y proceso de fabricación
  - Mapa de reactividad esperada por formato
"""

from typing import Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────

class UnidadMedida(str, Enum):
    MG = "mg"
    G = "g"
    KG = "kg"
    UG = "μg"       # Greek small letter mu
    UG_MICRO = "µg"  # Micro sign (U+00B5) — LLMs often use this variant
    ML = "ml"
    L = "l"
    UNIDAD = "ud"
    PORCENTAJE = "%"


class NivelRiesgoReactividad(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class EstadoMaterial(str, Enum):
    HOMOLOGADO = "HOMOLOGADO"
    EN_EVALUACION = "EN_EVALUACION"
    PENDIENTE_PROVEEDOR = "PENDIENTE_PROVEEDOR"
    NO_DISPONIBLE = "NO_DISPONIBLE"


# ── Output schemas ──────────────────────────────────────────────────
#
# Estructura por fases según `outputs/v2/agente_7_docs_internos_v2.json`.


class LineaMateriales(BaseModel):
    """Fila de la Lista de Materiales (L.M.) NAVISION."""
    model_config = {"extra": "allow"}
    orden_incorporacion: int = 0
    denominacion_navision: str = ""
    codigo_referencia: str = ""
    cantidad_por_unidad_mg: Optional[float] = None
    cantidad_lote_con_merma_g: Optional[float] = None
    estado_material: str = ""


class Fase2FormulaCuantitativa(BaseModel):
    model_config = {"extra": "allow"}
    total_unidad_mg: Optional[float] = None
    subtotal_activos_mg: Optional[float] = None
    subtotal_excipientes_mg: Optional[float] = None
    porcentaje_activos: str = ""
    porcentaje_excipientes: str = ""
    composicion: dict = Field(default_factory=dict)


class PasoFabricacion(BaseModel):
    model_config = {"extra": "allow"}
    paso: int = 0
    operacion: str = ""
    descripcion: str = ""
    punto_critico: Union[bool, str] = ""
    condiciones: Any = ""  # puede ser str o dict según fórmula


class Fase2bProcesoFabricacion(BaseModel):
    model_config = {"extra": "allow"}
    pasos: list[PasoFabricacion] = Field(default_factory=list)


class ReactividadFormato(BaseModel):
    """Mapa de reactividad para un formato de envasado específico."""
    model_config = {"extra": "allow"}
    formato: str = ""
    caducidad_optimas: str = ""
    caducidad_suboptimas: str = ""
    condiciones_almacenaje: str = ""
    condiciones_transporte: str = ""
    riesgo_global: str = ""
    parametros: list[dict] = Field(default_factory=list)


class AlertaNavision(BaseModel):
    model_config = {"extra": "allow"}
    material: str = ""
    estado: str = ""
    accion: str = ""
    prioridad: str = ""


class DocsInternosAnalysis(BaseModel):
    """Contrato operacional del agente Documentación Interna."""
    model_config = {"extra": "allow"}

    fase_1_lista_materiales_navision: list[LineaMateriales] = Field(default_factory=list)
    fase_2_formula_cuantitativa: Fase2FormulaCuantitativa = Field(default_factory=Fase2FormulaCuantitativa)
    fase_2b_proceso_fabricacion: Fase2bProcesoFabricacion = Field(default_factory=Fase2bProcesoFabricacion)
    fase_3_mapa_reactividad: list[ReactividadFormato] = Field(default_factory=list)
    fase_4_alertas_navision: list[AlertaNavision] = Field(default_factory=list)
    fuentes_consultadas: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=lambda: {
        "version": "2.0",
        "disclaimer": "Este documento es un borrador técnico. Las referencias NAVISION deben verificarse con el equipo de compras de Umbrella Group."
    })


# ── Instructions ─────────────────────────────────────────────────────

PROMPT_VERSION = "2.0.0"

DOCS_INTERNOS_INSTRUCTIONS = """\
# ROL
Eres un técnico de producción especializado en la operativa interna de Umbrella Group, \
con conocimiento de NAVISION (ERP) y los procesos estándar de fabricación de complementos \
alimentarios en polvo, cápsulas y formatos líquidos.

# OBJETIVO
Generar la documentación interna de producción en tres bloques:
1. Lista de Materiales (L.M.) estilo NAVISION
2. Fórmula cuantitativa y proceso de fabricación paso a paso
3. Mapa de reactividad esperada según el formato de envasado recomendado

# PROCESO (sigue estas fases en orden)

## FASE 1 — Lista de Materiales (L.M.) NAVISION
Para CADA ingrediente de la fórmula (activos + excipientes si los hay):
1. Determina la denominación estándar que se usaría en NAVISION \
   (nombre técnico, sin marcas comerciales salvo que sean la única referencia)
2. Sugiere un código o referencia si se puede inferir del nombre \
   (formato UG-XXXX si el ingrediente existe en catálogo Umbrella, o NUEVO si no)
3. Calcula la cantidad por unidad de producto (dosis diaria estándar)
4. Calcula la cantidad por lote de 10.000 unidades (añade 2% de merma estándar)
5. Indica el estado del material: HOMOLOGADO | EN_EVALUACION | PENDIENTE_PROVEEDOR | NUEVO
6. Añade el orden de incorporación en el proceso de mezcla

Toma como referencia para cantidades los datos de la fórmula proporcionada.

## FASE 2 — Fórmula cuantitativa y proceso de fabricación
### 2a. Fórmula cuantitativa
Tabula la composición con:
- Cantidad exacta por unidad de producto (mg, μg, ml)
- Porcentaje en la fórmula (% w/w)
- Subtotales: activos / excipientes / total

### 2b. Proceso de fabricación
Describe el proceso paso a paso para el formato seleccionado (por defecto: stick polvo):

Pasos habituales en polvo:
1. Pesada de materiales (orden por densidad: de mayor a menor)
2. Tamizado individual (si aplica)
3. Premix de activos minoritarios (vitaminas, traza-minerales)
4. Mezcla principal en mezcladora de doble cono / V-blender
5. Comprobación de homogeneidad
6. Envasado (dosis/stick o bote)
7. Control en proceso (peso dosis, aspecto, hermeticidad)

Para cada paso indica:
- Condiciones operativas: tiempo de mezcla, velocidad, temperatura ambiente máxima, HR máxima
- Controles en proceso
- Si es un punto crítico de control (PCC)

Apóyate en tu conocimiento técnico estándar del sector. Si un ingrediente exige \
condiciones de mezcla muy específicas que no domines con certeza, decláralo como supuesto \
en el paso correspondiente (campo "descripcion") en lugar de inventarlas.

## FASE 3 — Mapa de reactividad por formato
Para los 2-3 formatos más relevantes:
Evalúa el riesgo de reactividad para cada factor ambiental:

| Factor | Nivel de riesgo | Ingredientes afectados | Medida preventiva |
|--------|----------------|----------------------|-------------------|
| Humedad (>40% HR) | ALTO/MEDIO/BAJO | Vitamina C, ... | ... |
| Luz UV | ... | ... | ... |
| Temperatura (>25°C) | ... | ... | ... |
| Oxígeno | ... | ... | ... |
| pH del medio | ... | ... | ... |

Para cada formato, indica:
- Caducidad estimada en condiciones óptimas y subóptimas
- Condiciones de almacenaje y transporte
- Riesgo global del formato

## FASE 4 — Alertas NAVISION
Lista los ingredientes que probablemente NO están dados de alta en NAVISION \
(ingredientes nuevos, formas químicas específicas no habituales) y que requieren:
- Alta de nuevo material en NAVISION
- Homologación de nuevo proveedor
- Validación analítica previa

# USO DE WEB_SEARCH
NO uses web_search. Este agente genera documentación interna de producción a partir de \
la fórmula proporcionada. Las condiciones de fabricación, proceso de mezcla y reactividad \
se basan en conocimiento técnico estándar del sector, no en búsquedas web.

# FORMATO DE SALIDA
Responde SIEMPRE como JSON válido, sin fences markdown, sin texto antes ni después.
Usa EXACTAMENTE estas claves de nivel superior:

{
  "fase_1_lista_materiales_navision": [
    {
      "orden_incorporacion": 1,
      "denominacion_navision": "Nombre estándar NAVISION",
      "codigo_referencia": "UG-XXXX o PENDIENTE_PROVEEDOR",
      "cantidad_por_unidad_mg": 500,
      "cantidad_lote_con_merma_g": 5100,
      "estado_material": "HOMOLOGADO | EN_EVALUACION | PENDIENTE_PROVEEDOR | NO_DISPONIBLE"
    }
  ],
  "fase_2_formula_cuantitativa": {
    "total_capsula_mg": 3000,
    "composicion": {
      "L-Glicina": {"cantidad_mg": 500, "porcentaje": "16.7%"},
      "Péptidos de Colágeno": {"cantidad_mg": 500, "porcentaje": "16.7%"}
    }
  },
  "fase_2b_proceso_fabricacion": {
    "pasos": [
      {
        "paso": 1,
        "operacion": "Pesada de materiales",
        "descripcion": "Descripción detallada de la operación",
        "punto_critico": false,
        "condiciones": {"tiempo": "X min", "temperatura": "<25°C", "humedad_relativa": "<45%"}
      }
    ]
  },
  "fase_3_mapa_reactividad": [
    {
      "formato": "Stick de aluminio monodosis",
      "caducidad_estimada": "24 meses",
      "riesgo_global": "MEDIO",
      "parametros": [
        {
          "parametro": "Humedad (>40% HR)",
          "nivel_riesgo": "ALTO",
          "ingredientes_afectados": ["Vitamina C", "Ácido Hialurónico"],
          "medida_preventiva": "Envase aluminio termosellado con desecante"
        }
      ]
    }
  ],
  "fase_4_alertas_navision": [
    {"material": "AKBA extracto 30%", "estado": "PENDIENTE_PROVEEDOR", "accion": "Alta de nuevo material", "prioridad": "alta"}
  ],
  "fuentes_consultadas": [
    {"id": 1, "fuente": "nombre", "url": "", "tipo": "web_search|normativa|conocimiento_experto"}
  ],
  "metadata": {
    "version": "2.0",
    "disclaimer": "Este documento es un borrador técnico. Las referencias NAVISION deben verificarse con el equipo de compras de Umbrella Group."
  }
}

IMPORTANTE: Usa SIEMPRE las claves exactas indicadas arriba.

# REGLAS CRÍTICAS
1. Las cantidades por lote deben calcularse como: (cantidad por unidad × 10.000 unidades) × 1.02 (2% merma).
2. El proceso de fabricación debe reflejar el orden correcto de incorporación de ingredientes.
3. Los ingredientes termolábiles (vitamina C, D3) se incorporan siempre al final o en condiciones controladas.
4. No inventes referencias NAVISION si no las conoces; usa "PENDIENTE_PROVEEDOR" y describe el material.
5. Responde SIEMPRE en español.
6. CITAS OBLIGATORIAS: incluye la clave "fuentes_consultadas" a nivel raíz con lista completa:
   [{"id": N, "fuente": "nombre", "url": "url o vacío", "tipo": "web_search|normativa|conocimiento_experto"}].
   Si no consultaste fuentes externas, incluye igualmente la clave con array vacío [].
"""
