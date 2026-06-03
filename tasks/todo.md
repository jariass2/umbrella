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

- [x] **Segmentos de mercado** (2026-05-29): Claims extendido con `parte_f_segmentos_mercado` (modelo `SegmentoMercado`, prompt FASE 6, v2.1.0). Compositor `fmt_segmentos`: tabla estructurada si existe, si no cae a `publico_objetivo_*` (hoy) con nota de pendiente.
- [x] **Formatos × Segmentos (matriz)** (2026-05-29): Formatos extendido con `matriz_formato_segmento` (modelo `FilaMatrizFormatoSegmento`, prompt FASE 5, v2.1.0, incluye `es_innovacion`). Compositor `fmt_formatos_segmentos`: matriz completa si existe, si no deriva una inicial de formato óptimo/alternativo. Bloque 3 ahora en orden Xavier: Claims → Segmentos → Formatos+Matriz → Etiqueta. PENDIENTE: contenido rico al re-ejecutar el pipeline. Tests 31/31.
- [x] **Etiqueta visual cara frontal / caras laterales** — IMPLEMENTADO (2026-05-29). `fmt_etiqueta` reescrita al layout de Xavier (espejo de "Immunara*"): **Cara frontal** (obligatorio: marca, "En base a:", dosis/cantidad neta, "Complemento alimenticio"; opcional: logos) + **Caras laterales** (obligatorio: lista ingredientes con nota de alérgenos en negrita, advertencias/frases obligatorias, operador/fabricado por/distribuido por, peso neto·lote·caducidad, logo Ecoembes; opcional: tabla nutricional→Bloque 2, claims→Bloque 3, código barras/QR).
- [x] **Bilingüe ES+EN:** el compositor renderiza panel ES (desde datos) + panel EN (desde campos `_en`). Agente Etiqueta extendido (FASE 7, prompt v2.1.0) para emitir `denominacion_venta_en`, `cantidad_neta_en`, `lista_ingredientes_en`, `alergenos_en`, `modo_empleo_en`, `dosis_diaria_en`, `advertencias_obligatorias_en`. **PENDIENTE DE VERIFICAR:** el contenido EN variable se poblará al **re-ejecutar el pipeline** (cambio de prompt no testeable offline). Hoy el panel EN muestra frases legales fijas + nota "regenerar". Tests del compositor: 24/24 verde.

**Pendiente 6c (mejora):** poner alérgenos en negrita inline (hoy el agente los pone en campo aparte narrativo); tabla `Ingredientes · 3 caps · %VRN · 6 caps · %VRN` estilo Immunara como opción visual.

### 6d. Bloque 6 — Portfolio recomendado (Agente 9 nuevo) — IMPLEMENTADO 2026-05-29

Decisión: **agente LLM nuevo** (Agente 9). Implementado:
- [x] `agents/portfolio_agent_v2.py`: schema `PortfolioAnalysis` (fase_1_posicionamiento, fase_2_extensiones_linea, fase_3_productos_complementarios, fase_4_gama_recomendada) + prompt (estratégico, sin web_search, como Formatos). Prompt v1.0.0.
- [x] Config: `AGENT_PREFIXES[9] = AGENT_9_PORTFOLIO` + alias `"Portfolio"`.
- [x] Orquestador: import, AGENT_OUTPUT_MODELS, AGENT_PROMPT_VERSIONS, submit en Wave 1 (desde la fórmula, sin deps, paralelo con Formatos/Docs/QC), collect, `agent_models` y contador finales dinámicos.
- [x] Compositor: `fmt_portfolio` renderiza el Bloque 6 (posicionamiento + extensiones de línea + complementarios + gama/roadmap); fallback si no hay JSON; anexo incluye Agente 9.
- [x] Tests: render con muestra + fallback. Suite 26/26 verde.

**PENDIENTE DE VERIFICAR:** la calidad del output del LLM solo se ve al **re-ejecutar el pipeline** (no testeable offline). Hoy el Bloque 6 muestra el aviso de "ejecuta con el Agente 9".

**Orden sugerido:** 6a primero (resuelve ~80% de la queja de Xavier sin tocar LLMs ni esperar adjuntos) → 6b/6c/6d cuando lleguen los adjuntos y la decisión del portfolio.

## Fase 7: Confidencialidad de dosis + depuración de datos (feedback Xavier ronda 2, 2026-06-02)

**Feedback (traducido del catalán):**
1. Estructura "molt millor" ✅ pero hay que **depurar los datos que salen**.
2. 🔴 **La dosis cuantitativa es SECRETA y no debe aparecer nunca** ("o estem fotuts"). Distinguir **fórmula cuantitativa** (secreta) de **claims de activos** (público). Ref: `Excel Tabla Cuantitativa.xlsm`.
3. Propuestas de innovación demasiado "locas" (ej. gominolas = chuches, contra el concepto de complemento). Menor.

**Hallazgo del Excel (`Full1`):** dos columnas distintas que el report colapsa hoy en una:
- `Dosis` = mg de **materia prima en la fórmula** (833,33mg Magchel, 166,67mg Boswellia, 80mg AstaMarine) → **SECRETO** (revela receta/blend/coste).
- `Dosis Actiu` / `Claim Actiu` = **activo aportado** (100mg Mg, 50mg AKBA, 2mg astaxantina, 75mg curcuminoides) → **público** ("En base Claim Actiu"). `Dosis Actiu = Dosis × %Actiu/100`.
- El Excel ya tiene cabeceras `Forma Química · Biodisponibilidad · REGA` (vacías) → Xavier lo trata como la tabla maestra canónica.

**Problema en código:** `dosis_formula_mg` (la dosis secreta) se imprime 3× en bloques cliente:
- Cabecera "Fórmula analizada" (echo del input, `report_composer.py`).
- Bloque 1 tabla maestra, col `Dosis` (`report_composer.py:192`).
- Bloque 2 "Tabla de activos por dosis" (`report_composer.py:536`).
El modelo `IngredienteKIC` (`kic_agent_v2.py:96`) NO tiene campos de activo (`%actiu`, `nom_actiu`, `dosis_actiu`).

### 7a. Quitar la dosis secreta de los bloques cliente (CRÍTICO, sin tocar LLMs) — ✅ PARCIAL (2026-06-02)
- [x] Helper `_dosis_activo(ing)` + `_parse_pct_activo(nombre)` en composer: calcula `dosis_actiu = dosis_formula_mg × %actiu` (%actiu parseado del nombre, ej. "30% AKBA"); si no se puede, "—". Puente hasta 7b. Verificado vs Excel: cuadra 8/12 (Mg→100, AKBA→50, curcuminoides→75, astax→2, PEA→150, MCT→80, Digezyme→75, manzanilla→1.2).
- [x] Bloque 1 tabla maestra (`fmt_tabla_maestra`): col `Dosis`→`Dosis de activo` + `% NRV/VRN`. Ya no imprime `dosis_formula_mg`. Nota al pie `NOTA_DOSIS_ACTIVO`.
- [x] Bloque 2 "Tabla de activos por dosis" (`fmt_ficha_tecnica`): ídem, dosis de activo + nota.
- [x] Echo "Fórmula analizada" (mg exactos) eliminado de la cabecera → sustituido por aviso de confidencialidad que remite a bloques 4-5.
- [x] La fórmula cuantitativa completa (mg materia prima) ya vivía en Bloque 4 (Doc. Interna, datos NAVISION) y Bloque 5 (Plan de Calidad). Confirmado que solo aparece ahí.
- [x] Tests: 5 nuevos (`_parse_pct_activo`, `_dosis_activo` no expone materia prima, header "Dosis de activo", sin "## Fórmula analizada", nota confidencialidad). Suite 40/40.
- [ ] **PENDIENTE (fuga en texto libre de agentes, → 7b):** mg de materia prima siguen incrustados en texto LLM de bloques 1-3: advertencias KIC ("80 mg x 2.5%"), propuestas de mejora ("150 mg PEA", "extracto a 160-480 mg"), y etiquetas de la tabla de claims del agente Claims ("- 150 mg", "- 80 mg ingrediente"). No se arregla limpio en el composer; requiere ajustar prompts (expresar siempre en activo) o un scrub. Bambú diverge (nombre 85% sílice vs Excel 39,73% silicio).
- [ ] Regenerar `outputs/run_36/informe_ejecutivo.md` desde JSON cuando se valide (no sobrescrito aún; artefacto histórico).

### 7b. Ingesta del FT PDF con dosis activa → dashboard (DESBLOQUEADO 2026-06-03)
**Resuelto:** Xavier envía una **versión del FT PDF con la dosis activa añadida** (`…/Frmules per Validar/FT Formula 1 MIX 250188 (1).pdf`, 3/6). Formato canónico:
- Nombre codifica activo y %: "Boswellia serrata Ext., **30% AKBA**", "Bamboo Extract (85% Silica), **39,73% Silicon**".
- Columna **dosis activa** (`mg/3 Cap`, "Main Active or Excipient") = PÚBLICA. Última columna `mg/3 Cap` = **materia prima** = SECRETA.
- B6 = caso especial: activo declarado 1,40 ≠ 2,26×80,5% (sobredosado de vitamina). **DECISIÓN del usuario: mostrar SIEMPRE el valor de Xavier** → no calcular, leer del PDF.
- Parser de-riesgado con `pypdfium2` (ya instalado): regex `código · nombre · 7 columnas numéricas`; activo=col 1, materia prima=col 5. 12/12 filas OK.

**Arquitectura (artefacto canónico):** el dato activo del PDF debe llegar al composer. El pipeline hoy: form rows → `rows_to_formula` → texto → agentes extraen dosis → composer. Plan: PDF → parser → datos canónicos persistidos como `formula_canonica.json` en el `output_dir` del run; el composer lo lee como autoritativo (sustituye el puente `_dosis_activo` de 7a cuando existe); la materia prima sigue solo en bloques 4-5.

- [x] **7b.1 Parser** `dashboard/utils/ft_pdf_parser.py`: `parse_ft_pdf(bytes|path) -> {product_name, dosage, version, ingredients:[{code, name, active_name, pct_active, active_mg, raw_mg, unit}]}` con `pypdfium2`. Tests `tests/test_ft_pdf_parser.py` (12 ingredientes, B6 1,40, bambú 4,00/silicio); se omiten si el PDF no está (no se commitea, es confidencial). 2026-06-03.
- [x] **7b.2 Dashboard drag-and-drop**: zona de arrastre + `<input file>` en `index.html` + endpoint `POST /parse-formula-pdf` (devuelve JSON) que parsea y **pre-rellena** las filas (nombre + materia prima + **activo visible** + ocultos active_name/pct). Campo "Activo" añadido a la fila. CSS `.pdf-drop`. Verificado con test_client (12 ingredientes). 2026-06-03.
- [x] **7b.3 Artefacto canónico + composer**: `/analyze` lee `ing_active`/`ing_active_name`/`ing_pct`, construye y escribe `formula_canonica.json` en `output_dir`. Composer: `_load_canonica` + `_alinear_canonica` (empareja por índice, KIC conserva orden) + `_dosis_activo(ing, canonical)` usa el dato del PDF como autoritativo, si no cae al puente 7a. Nota al pie cambia a "según la ficha de fórmula". Tests: B6→1,40, bambú→4,00, nunca materia prima. Suite 48/48. 2026-06-03.
- [ ] **7b.4 (después)** Pasar la dosis activa también a los AGENTES (regulatorio/claims razonan sobre activo, no extracto) vía texto de fórmula enriquecido. Cierra de paso las fugas de mg en texto libre.

### 7c. Depurar datos sucios del output (punto 1) — ✅ PARCIAL (2026-06-02)
- [x] **Bug render dict**: helper `_spec_val` formatea `{'valor':…, 'metodo':…}` como "valor *(método: …)*" en sección 4 de `fmt_ficha_tecnica`. Test `test_spec_val_dict_no_crudo`.
- [x] **`N/A%`** literal en columna %VRN → `_fmt_pct` devuelve "—" para N/A/NA/none. Test `test_fmt_pct_na_no_imprime_porcentaje`.
- [x] **Magnesio**: con 7a (dosis de activo) la tabla muestra solo 100 mg de Mg; desaparece la ambigüedad 833.33 vs 100.
- [ ] **Incoherencia cúrcuma** `<95%` vs `95%`: es texto libre cruzado entre agentes KIC (`<95%`) y Claims (`95%`) → no reconciliable en composer. Defer a 7b (prompts).

### 7d. Filtro de coherencia en propuestas de formato (punto 3, menor)
- [ ] `formatos_agent_v2`: marcar propuestas disruptivas (`es_innovacion=true`) en sección aparte "exploratorias" o excluir formatos incompatibles con complemento alimentario (gominolas/chuches). Ajuste de prompt o filtro en `fmt_formatos`.

**Orden:** 7a (resuelve el riesgo de IP, sin re-run) → 7c (bugs seguros) → 7b (decisión de arquitectura) → 7d (cosmético).

## Estado global (2026-05-29)
6a ✅ · 6b ✅ · 6c ✅ (EN pendiente de re-run) · 6d ✅ (pendiente de re-run). Limpieza: Report Agent (antiguo "Agente 09") retirado; el "Agente 9" ahora es Portfolio.
**Siguiente:** re-ejecutar el pipeline para poblar EN de etiqueta + Bloque 6 Portfolio; capacidades de marketing del Bloque 3 (segmentos, formatos×segmentos).

**Orden sugerido:** 6a primero (resuelve ~80% de la queja de Xavier sin tocar LLMs ni esperar adjuntos) → 6b/6c/6d cuando lleguen los adjuntos y la decisión del portfolio.
