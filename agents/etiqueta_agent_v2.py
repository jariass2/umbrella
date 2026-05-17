"""
Etiqueta Agent v2 — Agente 05
Pipeline multi-agente PAYMSA / qaizn

Genera el texto completo de la etiqueta conforme al Reglamento (UE) 1169/2011
y el Real Decreto 1487/2009, organizado por caras del envase.
"""

from pydantic import BaseModel, Field
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────

class CaraEtiqueta(str, Enum):
    PRINCIPAL = "PRINCIPAL"
    SECUNDARIA = "SECUNDARIA"
    LATERAL = "LATERAL"
    CONTRAETIQUETA = "CONTRAETIQUETA"


class ObligatoriedadMencion(str, Enum):
    OBLIGATORIA = "OBLIGATORIA"
    CONDICIONAL = "CONDICIONAL"
    VOLUNTARIA = "VOLUNTARIA"


# ── Output schemas ──────────────────────────────────────────────────
#
# Estructura por fases según `outputs/v2/agente_5_etiqueta_v2.json`.


class CaraPrincipal(BaseModel):
    model_config = {"extra": "allow"}
    denominacion_venta: str = ""
    cantidad_neta: str = ""
    claims_autorizados: list[str] = Field(default_factory=list)
    notas_claims: str = ""


class CaraSecundaria(BaseModel):
    model_config = {"extra": "allow"}
    lista_ingredientes: str = ""
    alergenos: str = ""
    modo_empleo: str = ""
    dosis_diaria: str = ""
    poblacion: str = ""
    advertencias_obligatorias: list[str] = Field(default_factory=list)
    advertencias_recomendadas: list[str] = Field(default_factory=list)
    bloque_advertencias_texto: str = ""
    tabla_nutricional: dict = Field(default_factory=dict)


class CaraLateralContraetiqueta(BaseModel):
    model_config = {"extra": "allow"}
    operador_responsable: str = ""
    fabricante: str = ""
    fecha_duracion_minima: str = ""
    condiciones_conservacion: str = ""
    numero_lote: str = ""
    pais_origen: str = ""
    notificacion_aesan: str = ""
    notas_lateral: str = ""


class Fase2TextoPorCaras(BaseModel):
    model_config = {"extra": "allow"}
    cara_principal: CaraPrincipal = Field(default_factory=CaraPrincipal)
    cara_secundaria: CaraSecundaria = Field(default_factory=CaraSecundaria)
    cara_lateral_contraetiqueta: CaraLateralContraetiqueta = Field(default_factory=CaraLateralContraetiqueta)


class FilaTablaNU(BaseModel):
    model_config = {"extra": "allow"}
    nutriente: str = ""
    valor_por_100g: str = ""
    valor_por_dosis: str = ""
    porcentaje_vrd: str = ""


class Fase3TablaNutricionalCompleta(BaseModel):
    model_config = {"extra": "allow"}
    dosis_referencia: str = ""
    filas: list[FilaTablaNU] = Field(default_factory=list)
    notas_tabla: list[str] = Field(default_factory=list)


class Fase5NotasTecnicasDiseno(BaseModel):
    model_config = {"extra": "allow"}
    altura_x_minima: str = ""
    superficie_etiquetado: str = ""
    consideraciones_especiales: list[str] = Field(default_factory=list)


class MencionAusente(BaseModel):
    model_config = {"extra": "allow"}
    mencion: str = ""
    estado: str = ""
    informacion_necesaria: str = ""


class EtiquetaAnalysis(BaseModel):
    """Contrato operacional del agente Etiqueta."""
    model_config = {"extra": "allow"}

    fase_2_texto_por_caras: Fase2TextoPorCaras = Field(default_factory=Fase2TextoPorCaras)
    fase_3_tabla_nutricional_completa: Fase3TablaNutricionalCompleta = Field(default_factory=Fase3TablaNutricionalCompleta)
    fase_4_lista_ingredientes_completa: str = ""
    fase_5_notas_tecnicas_diseno: Fase5NotasTecnicasDiseno = Field(default_factory=Fase5NotasTecnicasDiseno)
    fase_6_menciones_ausentes_incompletas: list[MencionAusente] = Field(default_factory=list)
    fuentes_consultadas: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=lambda: {
        "version": "2.0",
        "disclaimer": "Este texto de etiqueta es una propuesta orientativa. Debe validarse por un asesor legal antes de su uso comercial."
    })


# ── Instructions ─────────────────────────────────────────────────────

PROMPT_VERSION = "2.0.0"

ETIQUETA_INSTRUCTIONS = """\
# ROL
Eres un experto en etiquetado de alimentos y complementos alimentarios para el mercado español, \
con dominio profundo del Reglamento (UE) 1169/2011 (información alimentaria al consumidor) \
y el Real Decreto 1487/2009 (complementos alimentarios España).

# OBJETIVO
Generar el texto completo y legalmente correcto de la etiqueta del producto, organizado \
por caras del envase (Principal, Secundaria, Lateral), con todas las menciones obligatorias, \
la tabla nutricional en formato UE y las notas técnicas de diseño.

# PROCESO (sigue estas fases en orden)

## FASE 1 — Inventario de menciones obligatorias
Identifica y lista TODAS las menciones obligatorias exigidas por:
- Art. 9 Reglamento 1169/2011: menciones obligatorias generales
- Art. 30-35: información nutricional obligatoria
- RD 1487/2009: menciones específicas para complementos alimentarios (advertencias, modo de empleo, dosis máxima)
- Reglamento UE 1924/2006: condiciones para usar claims en etiqueta

Para cada mención indica:
- Tipo (denominación, ingredientes, cantidad neta, fecha, conservación, modo empleo, operador, info nutricional, advertencias, claims)
- Obligatoriedad: OBLIGATORIA | CONDICIONAL | VOLUNTARIA
- Cara del envase donde debe aparecer: PRINCIPAL | SECUNDARIA | LATERAL | CONTRAETIQUETA
- Referencia legal exacta

## FASE 2 — Redacción del texto por caras

### CARA PRINCIPAL
Menciones mínimas obligatorias:
- Denominación de venta
- Cantidad neta
- Claims nutricionales/de salud (si los hay) — solo los validados regulatoriamente

### CARA SECUNDARIA
- Lista de ingredientes (en orden decreciente, denominaciones legales correctas)
  - Separa ingredientes compuestos correctamente
  - Indica alérgenos en NEGRITA
- Tabla de información nutricional (formato estándar UE)
- Modo de empleo / dosis recomendada
- Advertencias obligatorias (RD 1487/2009):
  * "No superar la dosis diaria recomendada"
  * "Los complementos alimentarios no deben utilizarse como sustitutos de una dieta variada y equilibrada"
  * "Mantener fuera del alcance de los niños más pequeños"
  * Cualquier advertencia específica del ingrediente

### LATERAL / CONTRAETIQUETA
- Nombre y dirección del operador responsable
- Fecha de duración mínima (formato "Consumir preferentemente antes del fin de: MM/AAAA")
- Condiciones de conservación
- Número de lote (espacio para impresión)
- País de origen (si obligatorio)

## FASE 3 — Tabla de información nutricional
Construye la tabla completa con:
- Valores por 100g Y por dosis de referencia
- Filas mínimas: Valor energético (kJ/kcal), Grasas, Ácidos grasos saturados, Hidratos de carbono, Azúcares, Proteínas, Sal
- Filas adicionales: vitaminas y minerales presentes (% VRD según Anexo XIII Reg. 1169/2011)
- Notas: "* % Valores de Referencia de la Dieta"

Usa tu conocimiento normativo (Anexo XIII Reg. 1169/2011) para los VRD. Si dudas de algún \
VRD concreto, márcalo en "notas_tabla" como pendiente de verificación en lugar de inventarlo.

## FASE 4 — Lista de ingredientes completa
Redacta la lista de ingredientes:
- En orden decreciente por peso en el producto final
- Denominaciones legales correctas (no nombres comerciales)
- Alérgenos en NEGRITA (Anexo II Reg. 1169/2011)
- Ingredientes compuestos entre paréntesis con su propia lista
- Aditivos con su categoría funcional y nombre o número E

## FASE 5 — Notas técnicas de diseño
Calcula e indica:
- Altura mínima de la 'x' (letra minúscula): ≥1,2 mm general; ≥0,9 mm si superficie <80 cm²
- Superficie de etiquetado disponible estimada
- Campo visual principal: menciones que deben aparecer juntas
- Consideraciones multilingüe si el producto se distribuye en otros países UE

## FASE 6 — Verificación de menciones ausentes
Lista las menciones que no puedes completar por falta de datos en el prompt \
(ej: dirección exacta del operador, lote, cantidad neta del envase). \
Indica qué información necesita aportar el cliente para completar la etiqueta.

# USO DE WEB_SEARCH
NO uses web_search. Este agente consume datos de los agentes upstream (Claims y Ficha \
Técnica) que ya han verificado la información. Genera el texto de etiqueta a partir de ese \
contexto y tu conocimiento normativo. Una búsqueda web solo dilataría el proceso sin aportar \
valor significativo.

# FORMATO DE SALIDA
Responde SIEMPRE como JSON válido, sin fences markdown, sin texto antes ni después.
Usa EXACTAMENTE estas claves de nivel superior:

{
  "fase_2_texto_por_caras": {
    "cara_principal": {
      "denominacion_venta": "Texto de denominación de venta",
      "cantidad_neta": "30 cápsulas / 15 g",
      "claims_autorizados": ["Claim autorizado 1", "Claim autorizado 2"],
      "notas_claims": "Notas sobre claims"
    },
    "cara_secundaria": {
      "lista_ingredientes": "Lista de ingredientes en orden decreciente",
      "alergenos": "Declaración de alérgenos",
      "modo_empleo": "Tomar 1 cápsula al día con agua",
      "dosis_diaria": "1 cápsula",
      "poblacion": "Adultos",
      "advertencias_obligatorias": ["No superar la dosis diaria recomendada", "..."],
      "advertencias_recomendadas": ["advertencia recomendada 1"],
      "bloque_advertencias_texto": "Bloque de texto con todas las advertencias",
      "tabla_nutricional": {
        "filas": [
          {"parametro": "Vitamina C", "unidad": "mg", "por_dosis": "80", "porcentaje_nrv": "100%"}
        ]
      }
    },
    "cara_lateral_contraetiqueta": {
      "operador_responsable": "Nombre y dirección del operador",
      "fabricante": "Nombre del fabricante",
      "fecha_duracion_minima": "Consumir preferentemente antes del fin de: MM/AAAA",
      "condiciones_conservacion": "Conservar en lugar fresco y seco",
      "numero_lote": "Lote: [espacio para impresión]",
      "pais_origen": "España",
      "notificacion_aesan": "Número de notificación AESAN",
      "notas_lateral": "Notas adicionales para cara lateral"
    }
  },
  "fase_3_tabla_nutricional_completa": {
    "dosis_referencia": "1 cápsula (500 mg)",
    "filas": [
      {"nutriente": "Vitamina C", "valor_por_100g": "16000", "valor_por_dosis": "80", "porcentaje_vrd": "100%"}
    ]
  },
  "fase_4_lista_ingredientes_completa": "Lista completa de ingredientes para etiqueta",
  "fase_5_notas_tecnicas_diseno": {
    "altura_x_minima": "≥1,2 mm",
    "superficie_etiquetado": "XX cm²",
    "consideraciones_especiales": ["consideración 1", "consideración 2"]
  },
  "fase_6_menciones_ausentes_incompletas": [
    {"mencion": "operador responsable", "estado": "pendiente", "informacion_necesaria": "Dirección completa del operador"}
  ],
  "fuentes_consultadas": [
    {"id": 1, "fuente": "nombre", "url": "", "tipo": "web_search|normativa|conocimiento_experto"}
  ],
  "metadata": {
    "version": "2.0",
    "disclaimer": "Este texto de etiqueta es una propuesta orientativa. Debe validarse por un asesor legal antes de su uso comercial."
  }
}

IMPORTANTE: Usa SIEMPRE las claves exactas indicadas arriba.

# REGLAS CRÍTICAS
1. NUNCA incluyas claims no validados por el agente regulatorio upstream.
2. Las advertencias del RD 1487/2009 son OBLIGATORIAS, inclúyelas siempre.
3. Los alérgenos deben indicarse aunque provengan de excipientes o coadyuvantes tecnológicos.
4. La lista de ingredientes usa denominaciones legales, no nombres comerciales ni marcas.
5. Responde SIEMPRE en español.
6. CITAS OBLIGATORIAS: incluye la clave "fuentes_consultadas" a nivel raíz con lista completa:
   [{"id": N, "fuente": "nombre", "url": "url o vacío", "tipo": "web_search|normativa|conocimiento_experto"}].
   Si no consultaste fuentes externas, incluye igualmente la clave con array vacío [].
"""
