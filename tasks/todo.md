# Umbrella - Plan de Evolución

## Fase 1: Externalizar conocimiento (impacto alto, riesgo bajo)

- [ ] Auditar prompts de cada agente: clasificar líneas como "proceso" vs "conocimiento factual"
- [ ] Extraer normativa a `/knowledge/structured/regulatory/` (NRV, dosis máximas, BELFRIT, alérgenos, claims autorizadas, Novel Foods)
- [ ] Extraer datos de ingredientes a `/knowledge/structured/ingredients/` (clasificaciones, rangos de dosificación, interacciones, biodisponibilidad)
- [ ] Extraer referencias técnicas a `/knowledge/structured/technical/` (Ph. Eur., ICH, AOAC)
- [ ] Crear `/knowledge/proprietary/` con esquema para catálogo interno (fichas técnicas, proveedores, costes, BOMs históricas)
- [ ] Crear `/knowledge/templates/` con plantillas de documentos internos (fichas técnicas, etiquetas, checklists QA)
- [ ] Construir clase `KnowledgeBase` con `load_structured()` (Tier 1) y `search_documents()` (Tier 2)
- [ ] Conectar un agente piloto (KIC) a la KnowledgeBase, validar calidad de output
- [ ] Desplegar pgvector via docker-compose para documentos (Tier 2)
- [ ] Construir pipeline de ingesta de PDFs (`knowledge/ingest.py`)
- [ ] Desplegar a los 8 agentes uno a uno, validando cada uno
- [ ] Eliminar conocimiento embebido de prompts solo tras validación
- [ ] Añadir tests del dominio regulatorio (rangos de dosificación, claims válidas)

## Fase 2: Estructurar el repo ✅ (completado)

- [x] Crear estructura de carpetas `pipeline/`, `tools/`, `tests/`, `knowledge/`
- [x] Mover `test_v2.py` → `pipeline/orchestrator.py`, `config.py`, `report_composer.py`
- [x] Crear `tools/` y consolidar `monitored_tools.py`, `tavily_search.py`, `monitor.py`, `generate_md.py`
- [x] Crear `tests/` y mover tests individuales
- [x] Mover agentes v1 a `agents/legacy/`
- [x] Añadir `__init__.py` a todos los paquetes
- [x] Actualizar imports en pipeline, tools y tests
- [x] Actualizar README.md y umbrella.md con la nueva estructura
- [ ] Añadir `pyproject.toml` para gestión de dependencias

## Fase 3: Integración Navision / Business Central

- [ ] Construir `tools/navision_sync.py` — script batch que extrae catálogo de items, proveedores y costes de Navision → `/knowledge/proprietary/`
- [ ] Implementar `NavisionTool` (lectura): `search_items()`, `get_unit_cost()`, `get_stock()`
- [ ] Conectar KIC a NavisionTool — verificar disponibilidad de ingredientes contra catálogo real
- [ ] Conectar Docs Internos a NavisionTool — BOMs con códigos de artículo reales
- [ ] Implementar `create_bom_draft()` (escritura) con paso de revisión humana
- [ ] Conectar Formatos y QC a NavisionTool (costes, estado de materiales)

## Fase 4: Trazabilidad del razonamiento + API

### 4a. Trazabilidad de agentes (base de datos)

- [ ] Diseñar esquema `agent_runs` en PostgreSQL: `run_id`, `formula_input`, `agent_name`, `model_version`, `timestamp_start`, `timestamp_end`, `reasoning_chain` (JSONB), `sources_consulted` (JSONB), `output_generated` (TEXT), `status`
- [ ] Implementar `tools/traceability.py` — función `log_agent_run()` que persiste cada ejecución antes y después de cada agente
- [ ] Integrar `log_agent_run()` en `pipeline/orchestrator.py` como wrapper de cada agente del batch
- [ ] Añadir `reasoning_chain` al schema: capturar cada paso de razonamiento intermedio del agente (tool calls, retrieval results, decisiones)
- [ ] Persistir referencias RAG usadas: qué documentos de la KnowledgeBase consultó cada agente y con qué score de relevancia
- [ ] Crear índices en `agent_runs`: por `run_id`, por `agent_name`, por `timestamp_start` (para consultas de auditoría)
- [ ] Implementar `tools/traceability_query.py` — funciones `get_run_history()`, `get_agent_reasoning()`, `compare_runs()` para auditoría y debugging
- [ ] Añadir tests de integración: verificar que cada ejecución de agente escribe exactamente una fila en `agent_runs`
- [ ] Documentar esquema y queries de auditoría en `docs/traceability.md`

### 4b. API

- [ ] FastAPI con endpoint `/analyze-supplement`
- [ ] Endpoint `/runs/{run_id}` para consultar trazabilidad de una ejecución concreta
- [ ] Endpoint `/runs` con paginación para historial de ejecuciones

## Fase 5: Frontend con control de acceso por rol

### 5a. Autenticación y roles

- [ ] Definir matriz de roles y permisos por departamento:
  - `rol_formulacion` → acceso a outputs de KIC, Ficha Técnica, Formatos, Docs Internos
  - `rol_regulatorio` → acceso a outputs de Agente Regulatorio, Claims, trazabilidad normativa
  - `rol_calidad` → acceso a outputs de QC, trazabilidad completa del razonamiento de agentes
  - `rol_etiquetado` → acceso a outputs de Etiqueta, Claims
  - `rol_admin` → acceso completo a todos los outputs y logs del sistema
- [ ] Añadir tabla `users` en PostgreSQL: `user_id`, `email`, `role`, `department`, `created_at`
- [ ] Implementar autenticación con JWT (login, refresh token, logout)
- [ ] Añadir campo `visible_to_roles` (ARRAY) en `agent_runs` para filtrado por rol en queries
- [ ] Middleware de autorización en FastAPI: cada endpoint filtra resultados según el rol del token

### 5b. Frontend por rol

- [ ] Elegir stack: Next.js + Tailwind (ligero, SSR para datos sensibles)
- [ ] Página de login con autenticación JWT
- [ ] Dashboard general: lista de formulaciones ejecutadas con estado y fecha
- [ ] Vista de formulación: outputs agrupados por agente, solo los visibles al rol del usuario
- [ ] Vista de trazabilidad (solo `rol_calidad` y `rol_admin`): reasoning chain completo, fuentes RAG consultadas, versión del modelo
- [ ] Vista regulatoria (solo `rol_regulatorio` y `rol_admin`): claims validadas, normativa aplicada, referencias citadas
- [ ] Indicador visual claro cuando un output fue generado por IA vs. validado por humano
- [ ] Export a PDF por vista (para auditorías y revisiones internas)

### 5c. Infraestructura

- [ ] Dockerizar: contenedores para API (FastAPI), frontend (Next.js), PostgreSQL, pgvector
- [ ] `docker-compose.yml` con variables de entorno por entorno (dev / prod)
- [ ] Configurar HTTPS para el frontend (Let's Encrypt o certificado interno)

---

## Fase 6: Reestructurar el informe a 6 bloques + eliminar repeticiones (feedback Xavier, 2026-05-29)

**Problema:** "Repetim masses coses". 8 agentes independientes re-derivan datos a nivel ingrediente y `report_composer.py` los apila → la tabla de ingredientes sale 4-5×, advertencias 3×, claims 2×, mejoras 2× (casi literal entre KIC y Regulatorio).

**Principio rector:** una sola fuente canónica por dato en el informe. El compositor decide el "hogar" de cada dato y las demás secciones lo referencian, no lo reimprimen. La reorganización es casi toda en `report_composer.py` — los 8 agentes y sus prompts NO se tocan en la Fase 6a.

**Índice objetivo (Xavier):**
1. Fórmula Cuantitativa · 2. Ficha Técnica · 3. Información de Marketing · 4. Doc. Interna de Producción · 5. Plan de Calidad · 6. Portfolio recomendado

### 6a. Refactor del compositor — dedup + reorden (sin tocar agentes) — ✅ COMPLETADO (2026-05-29)

- [x] **Tabla maestra de ingredientes** (foco nº1): `fmt_tabla_maestra(kic, reg, ft)` fusiona por ingrediente KIC + Regulatorio + Ficha Técnica en UNA tabla: `Ingrediente · Dosis · % NRV/VRN · Forma química · Biodisponibilidad · Reg.`. Cruce por nombre normalizado (`_norm`: lower/sin acentos/sin paréntesis). De paso, arreglado el bug del doble `%%` (`_fmt_pct`).
- [x] Eliminadas las tablas de ingredientes duplicadas de Regulatorio y de Ficha Técnica "Composición" (esta última → "ver tabla maestra").
- [x] **Bloque 1 "Fórmula Cuantitativa"** = tabla maestra + `fmt_analisis_ingredientes` (detalle/mecanismo/interacciones/coherencia) + `fmt_validacion_regulatoria` (viabilidad + bloqueantes + estatus normativo por ingrediente + advertencias) + `fmt_propuestas_mejora`.
- [x] **Fusionadas las propuestas de mejora** de KIC + Regulatorio en `fmt_propuestas_mejora` con dedup por prefijo normalizado. NOTA: la dedup por prefijo NO captura solapamiento semántico (KIC ya lista "gap: ausencia vit. C" y "sugerencia: añadir vit. C"); fix real → prompt de KIC en Fase 6c, o dedup semántica.
- [x] **Nutricional una sola vez:** vive en Ficha Técnica (bloque 2). Eliminadas las 2 tablas nutricionales de `fmt_etiqueta` (cabeceras `% VRN/VRD`: 14 líneas → 2).
- [x] **Advertencias una sola vez:** canónicas en Validación Regulatoria (bloque 1). Eliminada la lista duplicada en Ficha Técnica "Modo de empleo".
- [x] **Reordenado `compose_informe`** a los 6 bloques; índice de portada y anchors actualizados.
- [x] Añadido `tests/test_report_composer.py` (6 bloques en orden, tabla ingredientes 1×, nutricional ≤1×, sin `%%`). Suite: 19/19 verde.
- [x] Regenerado `outputs/v2/informe_ejecutivo.md` desde los JSON existentes (sin LLM); anexo real injertado. 1094 → 1024 líneas.

**Candidatos de dedup pendientes (no críticos):** solapamiento semántico gap/sugerencia en Propuestas de mejora; "### Fórmula cuantitativa" del BOM NAVISION (bloque 4) vs tabla maestra (bloque 1) — son distintos (BOM con merma ×10.000) pero conviene revisar.

### 6b. Bloque 2 — Ficha Técnica formato objetivo (adjuntos recibidos 2026-05-29)

Formato objetivo = `FT Formula 1 MIX 250188.pdf` (plantilla estándar Umbrella, 6 págs). Ver [[docs-referencia-umbrella]]. Estructura a replicar:
1. **ACTIVE CLAIMS TABLE**: cabecera (Company/VAT/MIX/Customer/Version/Dose `1680 mg / 3 Cap "00"`/Packaging/Overdosage/Control Release) + tabla `Active Claim · Qty/Dose · Units · %NRV · Limits o Recom./Day · Max Units/Day`.
2. **INGREDIENTS TABLE**: lista por orden de peso + carriers + excipientes minoritarios + Annex III REG 1334/2008.
3. **NUTRITIONAL INFORMATION**: `Single Portion · Max Daily Dose · per 100 · %Kcal` + SHELF LIFE + REACTIVITY (Maillard/Oxidación/Fotosensibilidad/REDOX/Heat) + MICROBIOLOGY + OSMOLARITY.
4. **IDENTIFICATION/Specification**: FTIR, densidad, humedad, solubilidad, pH, granulometría, microbiología, % tipos de aditivo, certificados, food grade, límites contaminantes, GMO, TSE/BSE.
5. **ALLERGEN TABLE** (14 alérgenos YES/NO) + **SUITABLE DIETS** (Veg/Vegan/GlutenFree/SugarFree/Kosher/Halal/Bio + Status + Certification).
6. **PREMIX PRODUCT DATA**: shelf life, package sizes, storage, transport, first aid, logos.

- [x] **Decisión tomada:** el COMPOSITOR renderiza las 6 secciones cruzando JSON (ft+qc+kic+reg+clm), sin tocar agentes ni re-ejecutar LLMs. Campos de fabricación ausentes → "pendiente de muestra de producción" / "Verificar" / "Bajo petición" (no se inventan), igual que el PDF real.
- [x] `fmt_ficha_tecnica(ft, qc, kic, reg, clm)` reescrita con las 6 secciones: 1) Identificación + cabecera fabricante + tabla activos + **posibles claims por ingrediente** (= "Colección de Claims vs Ingredientes" de Xavier); 2) Ingredientes por orden de peso; 3) Nutricional + vida útil + reactividad cualitativa (de KIC) + microbiología (de QC); 4) Especificaciones físico-químicas (FT fase_5) + identidad FTIR (QC) + food-grade/GMO/TSE boilerplate; 5) Alérgenos (narrativa + tabla 14 Anexo II "Verificar") + aptitud dietética; 6) Conservación/transporte/modo de empleo.
- [x] Constantes de plantilla en `report_composer.py`: `FT_FABRICANTE` (Umbrella F&FI, VAT, dirección, RGSEAA, web), `ALERGENOS_ANEXO_II` (14), `FT_DIETAS`, boilerplate FOOD_GRADE/GMO/TSE/TRANSPORTE.
- [x] Tests añadidos (6 secciones FT, cabecera fabricante, 14 alérgenos, sin "meses meses"). Suite: **22/22 verde**. De paso arreglado bug preexistente "meses meses" en plan de estabilidad QC.

**Pendiente 6b (mejora, no bloqueante):** reactividad real (QC `fase_3_mapa_reactividad` vino vacío en el run de ejemplo); SHELF LIFE/REACTIVITY como gráfico de barras (ahora cualitativo); aptitud dietética derivada en vez de "Bajo petición" fijo.

### 6c. Bloque 3 — Información de Marketing (requiere capacidades nuevas)

- [ ] **Segmentos de mercado**: hoy solo existe `publico_objetivo_principal/secundario` (strings) en Claims. Decidir: enriquecer el prompt de Claims para emitir segmentos estructurados, o nuevo mini-agente de segmentación.
- [ ] **Formatos × Segmentos (matriz)**: hoy Formatos recomienda 1 formato óptimo, no una matriz. Ampliar el prompt/esquema de Formatos para emitir `matriz_formato_segmento` (qué formato encaja con qué segmento, incluyendo formatos de innovación).
- [x] **Etiqueta visual cara frontal / caras laterales** — IMPLEMENTADO (2026-05-29). `fmt_etiqueta` reescrita al layout de Xavier (espejo de "Immunara*"): **Cara frontal** (obligatorio: marca, "En base a:", dosis/cantidad neta, "Complemento alimenticio"; opcional: logos) + **Caras laterales** (obligatorio: lista ingredientes con nota de alérgenos en negrita, advertencias/frases obligatorias, operador/fabricado por/distribuido por, peso neto·lote·caducidad, logo Ecoembes; opcional: tabla nutricional→Bloque 2, claims→Bloque 3, código barras/QR).
- [x] **Bilingüe ES+EN:** el compositor renderiza panel ES (desde datos) + panel EN (desde campos `_en`). Agente Etiqueta extendido (FASE 7, prompt v2.1.0) para emitir `denominacion_venta_en`, `cantidad_neta_en`, `lista_ingredientes_en`, `alergenos_en`, `modo_empleo_en`, `dosis_diaria_en`, `advertencias_obligatorias_en`. **PENDIENTE DE VERIFICAR:** el contenido EN variable se poblará al **re-ejecutar el pipeline** (cambio de prompt no testeable offline). Hoy el panel EN muestra frases legales fijas + nota "regenerar". Tests del compositor: 24/24 verde.

**Pendiente 6c (mejora):** poner alérgenos en negrita inline (hoy el agente los pone en campo aparte narrativo); tabla `Ingredientes · 3 caps · %VRN · 6 caps · %VRN` estilo Immunara como opción visual.

### 6d. Bloque 6 — Portfolio recomendado (capacidad nueva)

- [ ] **[DECISIÓN Xavier]** ¿9º agente que propone productos complementarios al cliente, o cierre heurístico sobre lo ya analizado? No existe nada hoy.

**Orden sugerido:** 6a primero (resuelve ~80% de la queja de Xavier sin tocar LLMs ni esperar adjuntos) → 6b/6c/6d cuando lleguen los adjuntos y la decisión del portfolio.
