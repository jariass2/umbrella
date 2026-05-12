# Umbrella Group — Pipeline de Agentes IA

Pipeline de 9 agentes especializados para el análisis y documentación de fórmulas de complementos alimentarios.

## Estructura del proyecto

```
umbrella/
├── agents/                  # Definiciones de agentes (v2 activos)
│   ├── kic_agent_v2.py
│   ├── regulatory_agent_v2.py
│   ├── ficha_tecnica_agente_v2.py
│   ├── claims_agent_v2.py
│   ├── etiqueta_agent_v2.py
│   ├── formatos_agent_v2.py
│   ├── docs_internos_agent_v2.py
│   ├── qc_agent_v2.py
│   ├── report_agent_v2.py
│   └── legacy/              # Agentes v1 (solo para referencia/tests)
├── pipeline/                # Orquestación y configuración
│   ├── orchestrator.py      # Pipeline principal (ejecutar desde aquí)
│   ├── config.py            # Configuración de modelos por agente
│   └── report_composer.py   # Composición del informe ejecutivo
├── tools/                   # Herramientas compartidas
│   ├── monitor.py           # Monitorización en terminal
│   ├── monitored_tools.py   # Wrappers con logging (DuckDuckGo, PubMed)
│   ├── tavily_search.py     # Búsqueda web alternativa
│   └── generate_md.py       # Generación de Markdown desde JSON
├── knowledge/               # Base de conocimiento externa (por implementar)
│   ├── regulatory/          # Directivas CE, reglamentos UE, AESAN, BELFRIT
│   ├── nutritional/         # Tablas NRV, alérgenos, conversiones
│   ├── ingredients/         # Clasificaciones, dosificaciones, interacciones
│   ├── technical/           # Ph. Eur., ICH, ISO, AOAC
│   ├── proprietary/         # Catálogo interno: fichas técnicas, costes, proveedores
│   └── templates/           # Plantillas de documentos internos
├── tests/                   # Tests individuales de agentes
├── outputs/v2/              # Resultados de ejecuciones
├── tasks/                   # Documentación de tareas
│   ├── todo.md              # Plan de evolución
│   ├── lessons.md           # Lecciones aprendidas
│   └── prompts_agentes.md   # Prompts detallados por agente
├── umbrella.md              # Arquitectura detallada y roadmap
├── .env.example
├── requirements.txt
└── README.md
```

## Agentes

| # | Agente | Descripción |
|---|--------|-------------|
| 1 | KIC | Análisis de composición clave de ingredientes (KIC) |
| 2 | Regulatorio | Validación regulatoria (EFSA, AESAN, Directiva 2002/46/CE) |
| 3 | Ficha Técnica | Ficha técnica completa para dossier ante AESAN |
| 4 | Claims | Claims regulatorios EU 432/2012 y selling points comerciales |
| 5 | Etiqueta | Texto completo de etiqueta conforme a Reglamento 1169/2011 |
| 6 | Formatos | Evaluación de formatos de presentación e innovación |
| 7 | Docs Internos | Lista de materiales NAVISION, proceso de fabricación, mapa de reactividad |
| 8 | QC | Plan de control de calidad (FTIR, granulometría, densidad, pH, estabilidad ICH Q1A) |
| 9 | Informe | Síntesis ejecutiva: veredicto de viabilidad, alertas, inconsistencias entre agentes y próximos pasos |

### Grafo de dependencias

Cada agente recibe **solo el contexto que necesita** (dependencias mínimas):

```
┌─ KIC (fórmula) ──→ Regulatorio ──→ Ficha Técnica ──┐
│                                                      ├→ Etiqueta
│  Formatos (fórmula)                                  │  ↑
│  Docs Internos (fórmula)                             Claims ─┘
│  QC (fórmula)
└─ (todos en paralelo, Batch 1)
```

### Ejecución paralela por batches

| Batch | Agentes | Dependencias |
|-------|---------|--------------|
| 1 | KIC + Formatos + Docs Internos + QC | Solo fórmula (4 en paralelo) |
| 2 | Regulatorio | KIC |
| 3 | Ficha Técnica + Claims | KIC + Regulatorio (paralelo) |
| 4 | Etiqueta | Claims + Ficha Técnica |

Los resultados se guardan en `outputs/v2/` como `.json` (para la cadena) y `.md` (para lectura humana).
El agente 9 genera además `outputs/v2/informe_ejecutivo.md` como documento final de entrega.

## Instalación

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y rellena las claves
```

## Ejecución

```bash
# Pipeline completo
python pipeline/orchestrator.py

# Test individual de un agente
python tests/test_kic.py
```

## Configuración de modelos

Cada agente puede usar un modelo de lenguaje diferente. La configuración se gestiona en el fichero `.env`.

### Configuración por defecto

Todos los agentes usan los valores `DEFAULT_*` si no tienen configuración propia:

```env
DEFAULT_MODEL=glm-5-turbo
DEFAULT_BASE_URL=https://api.z.ai/api/coding/paas/v4
DEFAULT_API_KEY=sk-...
```

### Configuración individual por agente

Para ajustar un agente específico, define sus variables en `.env`:

```env
# Agente 1 con GPT-4o en OpenAI
AGENT_1_KIC_MODEL=gpt-4o
AGENT_1_KIC_BASE_URL=https://api.openai.com/v1
AGENT_1_KIC_API_KEY=sk-...

# Agente 3 con Claude en Anthropic (via proxy OpenAI-compatible)
AGENT_3_FT_MODEL=claude-opus-4-6
AGENT_3_FT_BASE_URL=https://...
AGENT_3_FT_API_KEY=sk-ant-...
```

### Variables disponibles por agente

| Variable | Descripción |
|----------|-------------|
| `AGENT_N_XXX_MODEL` | ID del modelo (ej: `gpt-4o`, `glm-5-turbo`) |
| `AGENT_N_XXX_BASE_URL` | Endpoint base de la API (compatible con OpenAI) |
| `AGENT_N_XXX_API_KEY` | Clave de API |

Prefijos disponibles: `AGENT_1_KIC`, `AGENT_2_REG`, `AGENT_3_FT`, `AGENT_4_CLAIMS`, `AGENT_5_ETIQUETA`, `AGENT_6_FORMATOS`, `AGENT_7_DOCS`, `AGENT_8_QC`.

### Prioridad de resolución

```
AGENT_N_XXX_*  →  DEFAULT_*  →  ZAI_API_KEY (legacy)
```

Al iniciar el pipeline se imprime un resumen de la configuración activa de cada agente.

## Outputs

Cada ejecución genera en `outputs/v2/`:

```
agente_1_kic_v2.json / .md
agente_2_regulatorio_v2.json / .md
agente_3_ficha_técnica_v2.json / .md
agente_4_claims_v2.json / .md
agente_5_etiqueta_v2.json / .md
agente_6_formatos_v2.json / .md
agente_7_docs_internos_v2.json / .md
agente_8_qc_v2.json / .md
informe_ejecutivo.md    ← Informe final compuesto (sin LLM)
```

## Política de Web Search

Los agentes usan `DuckDuckGoTools` con criterio estricto para minimizar latencia
y saturación de contexto:

| Agente | Política | Máx. búsquedas |
|--------|----------|---------------|
| KIC | Solo ingredientes poco comunes o biodisponibilidad dudosa | 2 |
| Regulatorio | Solo estado regulatorio incierto (ej: AKBA/Boswellia) | 2 |
| Ficha Técnica | No busca datos estándar | 1 |
| Claims | No busca por ingrediente individual | 2 |
| Etiqueta | No usa web search (consume datos upstream) | 0 |
| Formatos | Solo tendencias de mercado | 1 |
| Docs Internos | No usa web search (consumo datos upstream) | 0 |
| QC | Solo picos FTIR inusuales | 1 |

**Total máximo:** ~9 búsquedas en todo el pipeline (vs. ~25-30 sin restricción).

## Claves JSON — Contrato entre agentes y report_composer

Cada agente genera un JSON con claves específicas que `pipeline/report_composer.py` consume
para componer el informe final. Las claves primarias esperadas son:

| Agente | Clave raíz | Sub-claves principales |
|--------|-----------|----------------------|
| KIC | `fase_1_clasificacion` | `tipo_producto`, `objetivo_funcional_principal` |
| KIC | `fase_2_ingredientes` | `ingrediente`, `dosis_formula_mg`, `porcentaje_nrv`, `biodisponibilidad`, `mecanismo_accion` |
| KIC | `fase_3_interacciones_cruzadas` | `par_ingredientes`, `tipo_interaccion`, `relevancia_clinica` |
| KIC | `fase_4_valoracion_global` | `coherencia_funcional`, `potencial_sinergetico`, `gaps_funcionales` |
| Regulatorio | `ingredientes` | `nombre`, `semaforo`, `normativa_aplicable`, `condiciones` |
| Regulatorio | `evaluacion_global` | `viabilidad`, `bloqueantes`, `modificaciones_recomendadas` |
| Ficha Técnica | `fase_1_identificacion` | `denominacion_legal`, `tipo_producto`, `forma_presentacion` |
| Ficha Técnica | `fase_2_composicion` | `ingredientes_activos` → `nombre_ingrediente`, `cantidad_por_dosis` |
| Ficha Técnica | `fase_3_informacion_nutricional` | `tabla_nutricional` / `tabla_nutricional_por_dosis` |
| Ficha Técnica | `fase_4_alergenos` | `presentes`, `trazas`, `declaracion_etiqueta` |
| Ficha Técnica | `fase_6_conservacion_vida_util` | `condiciones_conservacion`, `vida_util_estimada` |
| Ficha Técnica | `fase_7_modo_empleo_advertencias` | `modo_empleo`, `dosis_maxima`, `advertencias_obligatorias` |
| Claims | `parte_a_claims_regulatorios` | `claims_por_ingrediente`, `claim_compuesto_triple_inmunitario` |
| Claims | `parte_b_selling_points_comerciales` | `selling_points` |
| Claims | `parte_e_advertencias_legales` | `claims_prohibidos` |
| Etiqueta | `fase_2_texto_por_caras` | `cara_principal`, `cara_secundaria`, `cara_lateral_contraetiqueta` |
| Etiqueta | `fase_3_tabla_nutricional_completa` | `dosis_referencia`, `filas` |
| Etiqueta | `fase_4_lista_ingredientes_completa` | _(string)_ |
| Etiqueta | `fase_5_notas_tecnicas_diseno` | `altura_x_minima`, `consideraciones_especiales` |
| Etiqueta | `fase_6_menciones_ausentes_incompletas` | _(list)_ |
| Formatos | `fase_1_evaluacion_formatos` | `tabla_comparativa_resumen` |
| Formatos | `fase_3_innovacion_ingredientes` | `propuesta_innovacion`, `ingredientes_diferenciadores` |
| Formatos | `fase_4_recomendacion_final` | `formato_optimo`, `formato_alternativo` |
| Docs Internos | `fase_1_lista_materiales_navision` | _(list de materiales)_ |
| Docs Internos | `fase_2_formula_cuantitativa` | `total_capsula_mg`, `composicion` |
| Docs Internos | `fase_2b_proceso_fabricacion` | `pasos` |
| Docs Internos | `fase_3_mapa_reactividad` | _(list)_ |
| Docs Internos | `fase_4_alertas_navision` | _(list)_ |
| QC | `fase_1_ftir` ... `fase_5_aspecto_organoleptico` | `_objetivo`, `metodologia_general` |
| QC | `fase_6_ensayos_analiticos_adicionales` | _(dict por categoría)_ |
| QC | `fase_7_plan_estabilidad` | `zona_climatica`, `condiciones_estudio`, `cronograma_estudio` |
| QC | `fase_8_resumen_ejecutivo` | _(string o dict)_ |

Todas las claves incluyen `fuentes_consultadas` (list) y `metadata` (dict) a nivel raíz.
El `pipeline/report_composer.py` tiene fallbacks defensivos (`.get()` con alternativas) para
campos que el LLM pueda nombrar ligeramente distinto.
