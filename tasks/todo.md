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
