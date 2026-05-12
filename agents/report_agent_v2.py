"""
Report Agent v2 — Agente 09
Pipeline multi-agente PAYMSA / qaizn

Sintetiza los outputs de los 8 agentes anteriores en un informe ejecutivo completo:
  - Resumen ejecutivo del producto
  - Viabilidad regulatoria y alertas
  - Perfil funcional y diferenciadores clave
  - Resumen de claims autorizados
  - Propuesta de etiqueta y formato recomendado
  - Plan de producción y QC en síntesis
  - Matriz de riesgos y próximos pasos
"""

from pydantic import BaseModel, Field
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────

class NivelRiesgo(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class EstadoViabilidad(str, Enum):
    VIABLE = "VIABLE"
    VIABLE_CON_CONDICIONES = "VIABLE_CON_CONDICIONES"
    REQUIERE_REVISION = "REQUIERE_REVISION"
    NO_VIABLE = "NO_VIABLE"


class PrioridadAccion(str, Enum):
    INMEDIATA = "INMEDIATA"
    CORTO_PLAZO = "CORTO_PLAZO"
    MEDIO_PLAZO = "MEDIO_PLAZO"
    LARGO_PLAZO = "LARGO_PLAZO"


# ── Output schemas ──────────────────────────────────────────────────

class ResumenEjecutivo(BaseModel):
    nombre_producto: str
    descripcion_breve: str = Field(description="2-3 frases que describen el producto y su propuesta de valor")
    clasificacion: str = Field(description="Tipo de producto: complemento alimentario, alimento funcional, etc.")
    objetivo_funcional: str = Field(description="Para qué sirve el producto según el análisis KIC")
    veredicto_global: EstadoViabilidad
    justificacion_veredicto: str = Field(description="Razón principal del veredicto global")


class HallazgoAgente(BaseModel):
    agente: str = Field(description="Nombre del agente que generó el hallazgo")
    hallazgo: str = Field(description="Conclusión más importante del agente")
    impacto: str = Field(description="Qué implica este hallazgo para el producto o el proceso")


class AlertaRiesgo(BaseModel):
    descripcion: str
    nivel: NivelRiesgo
    origen: str = Field(description="Agente o área que detectó el riesgo")
    accion_recomendada: str


class Inconsistencia(BaseModel):
    descripcion: str = Field(description="Contradicción o tensión entre dos o más agentes")
    agentes_implicados: list[str]
    resolucion_sugerida: str


class ProximoPaso(BaseModel):
    accion: str
    responsable: str = Field(description="Quién debe ejecutar: equipo técnico, legal, producción, marketing, etc.")
    prioridad: PrioridadAccion
    dependencias: list[str] = Field(default_factory=list, description="Otros pasos o validaciones previas necesarias")


class SintesissRegulatorio(BaseModel):
    viabilidad: EstadoViabilidad
    ingredientes_problematicos: list[str] = Field(default_factory=list)
    condiciones_criticas: list[str] = Field(default_factory=list, description="Condiciones que deben cumplirse para comercializar")
    tramites_necesarios: list[str] = Field(default_factory=list, description="Notificaciones, autorizaciones o registros necesarios")


class SintesisComercial(BaseModel):
    formato_recomendado: str
    claims_principales: list[str] = Field(description="Los 3-5 claims más potentes y seguros para usar")
    selling_points_top: list[str] = Field(description="Los 3 argumentos comerciales más diferenciadores")
    target_primario: str
    posicionamiento: str


class SintesisProduccionQC(BaseModel):
    formato_fabricacion: str
    puntos_criticos_produccion: list[str]
    ensayos_criticos_qc: list[str] = Field(description="Los ensayos QC más importantes para este producto")
    vida_util_estimada: str
    alertas_navision: list[str] = Field(default_factory=list)


class InformeEjecutivo(BaseModel):
    """Output completo del agente de informe."""
    resumen_ejecutivo: ResumenEjecutivo
    hallazgos_por_agente: list[HallazgoAgente] = Field(default_factory=list)
    sintesis_regulatoria: SintesissRegulatorio
    sintesis_comercial: SintesisComercial
    sintesis_produccion_qc: SintesisProduccionQC
    alertas_y_riesgos: list[AlertaRiesgo] = Field(default_factory=list)
    inconsistencias_detectadas: list[Inconsistencia] = Field(default_factory=list)
    proximos_pasos: list[ProximoPaso] = Field(default_factory=list)
    conclusion_final: str = Field(description="Párrafo de conclusión ejecutiva dirigido a dirección o cliente")
    fuentes_consultadas: list[dict] = Field(
        default_factory=list,
        description="Lista de fuentes: [{id, fuente, url, tipo}]"
    )
    metadata: dict = Field(default_factory=lambda: {
        "version": "2.0",
        "disclaimer": "Este informe es un resumen sintético generado automáticamente. Las decisiones comerciales y regulatorias deben validarse por expertos humanos."
    })


# ── Instructions ─────────────────────────────────────────────────────

REPORT_INSTRUCTIONS = """\
# ROL
Eres un consultor senior especializado en desarrollo de producto de complementos alimentarios. \
Tu rol es sintetizar el trabajo de un equipo de 8 agentes especializados en un informe ejecutivo \
claro, accionable y sin redundancias, apto para presentar a dirección o al cliente.

# OBJETIVO
Generar un informe ejecutivo completo que:
1. Sintetice los hallazgos clave de cada agente
2. Emita un veredicto global de viabilidad del producto
3. Identifique alertas, riesgos e inconsistencias entre agentes
4. Proponga los próximos pasos concretos con responsables y prioridades

# PROCESO (sigue estas fases en orden)

## FASE 1 — Lectura crítica de todos los agentes
Lee los outputs de los 8 agentes. Para cada uno extrae:
- El hallazgo más importante
- Su impacto en el producto o en el proceso
- Cualquier alerta o condición crítica

No copies bloques enteros de texto. Sintetiza con criterio.

## FASE 2 — Veredicto global de viabilidad
Con la visión de conjunto, emite un veredicto:
- VIABLE: el producto puede comercializarse sin cambios significativos
- VIABLE_CON_CONDICIONES: viable si se cumplen las condiciones identificadas
- REQUIERE_REVISION: hay problemas que deben resolverse antes de avanzar
- NO_VIABLE: existen impedimentos regulatorios o técnicos insalvables

Justifica el veredicto con los 2-3 factores más determinantes.

## FASE 3 — Síntesis regulatoria
Resume el estado regulatorio:
- Viabilidad de comercialización en España/UE
- Ingredientes problemáticos o condicionados (si los hay)
- Condiciones críticas que deben cumplirse (dosis máximas, advertencias, etc.)
- Trámites necesarios: notificación AESAN, registro, etc.

## FASE 4 — Síntesis comercial
Selecciona lo más accionable para marketing y ventas:
- Formato recomendado (del agente 6)
- Los 3-5 claims más potentes y seguros para usar en packaging/web
- Los 3 selling points más diferenciadores
- Target primario y posicionamiento en una frase

## FASE 5 — Síntesis de producción y QC
Resume lo esencial para el equipo de producción:
- Formato de fabricación y puntos críticos del proceso
- Ensayos QC más importantes para este producto específico
- Vida útil estimada
- Alertas NAVISION pendientes

## FASE 6 — Matriz de alertas y riesgos
Lista todas las alertas detectadas entre agentes, clasificadas por nivel:
- CRÍTICO: bloquea el lanzamiento
- ALTO: requiere acción antes de comercializar
- MEDIO: gestionar durante el desarrollo
- BAJO: a tener en cuenta, no urgente

## FASE 7 — Inconsistencias entre agentes
Detecta contradicciones o tensiones entre los outputs de distintos agentes. Ejemplos:
- El agente KIC sugiere una dosis pero el regulatorio la limita
- El agente de formatos recomienda un formato que el agente de QC señala como problemático
- Un claim que aparece en el agente de claims pero no está validado en el regulatorio

Para cada inconsistencia propón una resolución.

## FASE 8 — Próximos pasos
Define una hoja de ruta concreta con acciones, responsables y prioridades:
- INMEDIATA: antes de cualquier avance
- CORTO_PLAZO: en las próximas 2-4 semanas
- MEDIO_PLAZO: en los próximos 1-3 meses
- LARGO_PLAZO: estudios de estabilidad, registros, etc.

## FASE 9 — Conclusión ejecutiva
Escribe un párrafo final de 3-5 frases dirigido a dirección o al cliente, que:
- Resuma el estado del producto en una frase
- Destaque el mayor riesgo y la mayor oportunidad
- Indique la acción más urgente

# FORMATO DE SALIDA
Responde SIEMPRE como JSON válido, sin fences markdown, sin texto antes ni después.
Ajústate al schema InformeEjecutivo del pipeline.

# REGLAS CRÍTICAS
1. NO copies bloques de texto de los agentes anteriores. Sintetiza con criterio.
2. El veredicto global debe ser coherente con los hallazgos regulatorios y técnicos.
3. Los próximos pasos deben ser concretos y accionables (no "revisar el tema regulatorio").
4. Si hay inconsistencias entre agentes, señálalas explícitamente.
5. La conclusión final debe poder leerse de forma independiente, sin necesidad de leer el informe completo.
6. Responde SIEMPRE en español.
7. CITAS OBLIGATORIAS: incluye la clave "fuentes_consultadas" a nivel raíz:
   [{"id": N, "fuente": "nombre", "url": "url o vacío", "tipo": "web_search|normativa|conocimiento_experto"}].
   Si no consultaste fuentes externas, incluye igualmente la clave con array vacío [].
"""
