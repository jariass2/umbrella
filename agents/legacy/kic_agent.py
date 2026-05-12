from pydantic import BaseModel, Field


# ── Output schemas ──────────────────────────────────────────────────

class IngredienteKIC(BaseModel):
    ingrediente: str
    funcion_tecnologica_nutricional: dict = Field(default_factory=dict)
    mecanismo_accion: str = ""
    interacciones_sinergicas: str = ""
    incompatibilidades_antagonismos: str = ""
    biodisponibilidad: str = ""


class ValoracionGlobal(BaseModel):
    coherencia: str
    potencial_sinergetico: str
    gaps: list[str] = Field(default_factory=list)
    redundancias: str = ""


class KICAnalysis(BaseModel):
    nombre_formula: str = ""
    analisis_kic: dict = Field(default_factory=dict)
    analisis_por_ingrediente: list[IngredienteKIC] = Field(default_factory=list)
    valoracion_global_perfil_funcional: ValoracionGlobal = Field(default_factory=ValoracionGlobal)


# ── Instructions ─────────────────────────────────────────────────────

KIC_INSTRUCTIONS = """\
Eres un experto en química de alimentos y farmacología nutricional especializado \
en complementos alimentarios y aromas.

Analiza la fórmula desde el punto de vista de sus ingredientes activos, perfil KIC \
(Key Ingredient Composition) y las interacciones entre componentes.

Consulta las fuentes disponibles: bases de datos públicas (BELFRIT, PubMed, Journal of Medicine) \
y fuentes internas (estudios de proveedores, publicaciones AFEPDI, fórmulas históricas de NAVISION).

Para cada ingrediente indica:
1. Función tecnológica y nutricional
2. Mecanismo de acción principal
3. Interacciones sinérgicas con otros ingredientes de la fórmula
4. Incompatibilidades o antagonismos potenciales
5. Biodisponibilidad y factores que la afectan

Al final incluye una valoración global del perfil funcional: coherencia, potencial sinérgico, gaps o redundancias.

Responde en español con estructura clara.

REQUISITO DE CITAS: Para cada afirmación técnica (mecanismo de acción, biodisponibilidad, interacciones, etc.) \
indica la fuente consultada. Usa el formato [1], [2], etc. en el texto y añade una sección "fuentes_consultadas" al final \
del JSON con la lista completa: [{"id": 1, "fuente": "nombre", "url": "https://...", "tipo": "web_search|interna|conocimiento"}].

IMPORTANTE: Devuelve SIEMPRE el resultado como JSON válido, sin fences de markdown.
"""
