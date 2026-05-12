---
name: Diagnostico CrewAI vs Agno
description: Analisis comparativo de CrewAI y Agno para implementar el pipeline multi-agente de Umbrella Group (8 agentes secuenciales)
type: project
---

# Diagnostico: CrewAI vs Agno para Pipeline Umbrella Group

## Contexto
Pipeline de 8 agentes especializados para analisis de formulas de complementos alimentarios.
- Entrada: formula via webhook (n8n → FastAPI)
- Ejecucion: secuencial, 8 agentes
- Herramientas: web search (EFSA, PubMed, AESAN, BELFRIT) + MCP interno (NAVISION, AFEPDI)
- Salida: resultado.json + callback a n8n
- Coste estimado: ~$0.30-0.50 por ejecucion completa

## Decision: Agno

**Why:** Async-first, background runs con structured output, MCP robusto (allow_partial_failure), Knowledge base integrada (Qdrant para RAG con PDFs proveedores), AgentOS con FastAPI y session management.

**How to apply:** El pipeline se mapea como Workflow con Steps secuenciales. Cada Step tiene un Agent especializado. El servidor FastAPI se monta con AgentOS. Callbacks a n8n como post-hook del workflow.

## Mapeo de arquitectura

```
Step("kic", agent=kic_agent) → Step("regulatory", agent=regulatory_agent) → ...
Workflow(steps=[...], db=AsyncMongoDb(...))
```

## Lo que ninguno tiene nativo

- **Ejecucion parcial** (`"agents": ["kic", "regulatory"]`) — Filtrar tasks/agents antes de crear workflow. Trivial.
- **Cost tracking por agente** — Extraer usage metrics de cada task individualmente.

## Ventajas de CrewAI (si se reconsidera)

- Webhooks nativos por task y crew completo (para progreso intermedio a n8n)
- `output_json` en Tasks mas sencillo
- Modelo mental mas simple (Agent → Task → Crew)

## Web Search: DuckDuckGo

**Decision:** Usar `DuckDuckGoTools` de Agno. Sin API key, gratuito.
**Why:** El usuario prefiere no depender de APIs de terceros con coste.
**Trade-off:** Devuelve HTML crudo que el agente parsea, anade tokens por llamada. Aceptable para fuentes regulatorias especificas.

## Fichero de referencia

- Spec original: `umbrella.md` (raiz del proyecto)
