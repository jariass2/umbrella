# Pipeline Multi-Agente — Umbrella Group

Sistema autónomo de **8 agentes especializados** que analiza fórmulas de complementos alimentarios, ejecutando búsqueda web en tiempo real contra bases regulatorias (EFSA, AESAN, BELFRIT, Novel Foods) y fuentes internas (NAVISION, AFEPDI).

## Arquitectura

```
CLI / API (futuro)  ──►  Pipeline secuencial
                             │
            ┌────────────────────────────────────────┘
            │
  ┌─────────┼──────────────────────────────────────────────┐
  │         ▼                                              │
  │  Ag.1 KIC ──► Ag.2 Regulatorio ──► Ag.3 Ficha técnica  │
  │       │              │                    │             │
  │       ▼              ▼                    ▼             │
  │  Ag.4 Claims ──► Ag.5 Etiqueta ──► Ag.6 Formatos      │
  │       │              │                    │             │
  │       ▼              ▼                    ▼             │
  │  Ag.7 Docs internos ──► Ag.8 QC interno                │
  │                              │                          │
  │                              ▼                          │
  │                    resultado.json + callback            │
  └──────────────────────────────────────────────────────────┘
            │                    │
  ┌────────┘                    └────────┐
  ▼                                      ▼
Web Search                            MCP Interno
├─ EFSA Journal                       ├─ NAVISION (L.M., históricos)
├─ Novel Food Catalogue               ├─ Estudios proveedores
├─ BELFRIT botanical list             ├─ Publicaciones AFEPDI
├─ EU Register claims                 └─ Ingredientes homologados
├─ PubMed / J. of Medicine
└─ AESAN
```

## Los 8 agentes

| # | Agente | Qué hace | Fuentes |
|---|--------|----------|---------|
| 1 | **Análisis KIC** | Activos, IQC, sinergias, biodisponibilidad | BELFRIT, PubMed, AFEPDI, EFSA |
| 2 | **Validación regulatoria** | Semáforo ✅⚠️❌ por ingrediente | EFSA, Novel Foods, AESAN, BELFRIT |
| 3 | **Ficha técnica** | Composición, alérgenos, nutricional UE | Web + datos internos |
| 4 | **Claims + diferenciación** | Claims Reg. 1924/2006, innovación vs. mercado, PPT | EU Register, competidores |
| 5 | **Etiqueta tipo** | Texto completo cara principal/secundaria/lateral | Reg. 1169/2011 |
| 6 | **Formatos e innovación** | Sticks/cáps./vial + reactividad + target | Tendencias mercado |
| 7 | **Documentación interna** | L.M. NAVISION, fórmula cuantitativa, proceso fabricación | NAVISION (MCP) |
| 8 | **QC interno** | FTIR, granulometría, densidad, pH, estabilidad | ICH, Ph. Eur. |

## Estructura del proyecto

```
umbrella/
├── agents/                  # Definiciones de agentes
│   ├── *_agent_v2.py        # Agentes activos (v2)
│   └── legacy/              # Agentes v1 (referencia)
├── pipeline/                # Orquestación
│   ├── orchestrator.py      # Pipeline principal
│   ├── config.py            # Configuración por agente
│   └── report_composer.py   # Informe ejecutivo
├── tools/                   # Herramientas compartidas
│   ├── monitor.py           # Monitorización terminal
│   ├── monitored_tools.py   # DuckDuckGo/PubMed con logging
│   ├── tavily_search.py     # Búsqueda alternativa
│   └── generate_md.py       # Backfill JSON → Markdown
├── knowledge/               # Base de conocimiento (por implementar)
│   ├── regulatory/
│   ├── nutritional/
│   ├── ingredients/
│   ├── technical/
│   ├── proprietary/
│   └── templates/
├── tests/                   # Tests individuales
├── outputs/v2/              # Resultados
└── tasks/                   # Documentación
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con claves API
```

## Ejecución

```bash
# Pipeline completo
python pipeline/orchestrator.py

# Tests individuales
python tests/test_kic.py
python tests/test_regulatory.py
python tests/test_ficha_tecnica.py
```

## Costes estimados

| Agente | Turnos | Coste aprox. |
|--------|--------|-------------|
| KIC | 12-18 | ~$0.05 |
| Regulatorio | 15-22 | ~$0.07 |
| Ficha técnica | 8-15 | ~$0.04 |
| Claims + diferenciación | 15-22 | ~$0.07 |
| Etiqueta tipo | 10-18 | ~$0.05 |
| Formatos + innovación | 8-15 | ~$0.04 |
| Docs internos (L.M.) | 8-15 | ~$0.04 |
| QC interno | 10-18 | ~$0.05 |
| **TOTAL (8 agentes)** | **86-143** | **~$0.30-0.50** |

## Outputs generados

| Output | Generado por | Formato final |
|--------|-------------|--------------|
| Dossier completo | Todos | `.docx` (vía n8n o post-proceso) |
| PPT comercial | Agente 4 | `.pptx` (plantilla Umbrella Group) |
| Etiqueta tipo | Agente 5 | Texto maquetable |
| Ficha técnica | Agente 3 | `.docx` / `.pdf` |
| L.M. NAVISION | Agente 7 | `.xlsx` / importación ERP |
| Fórmula cuantitativa | Agente 7 | Tabla estructurada |
| Plan QC | Agente 8 | `.docx` / `.pdf` |
| Mapa reactividad | Agentes 6+8 | Tabla/gráfica |

## Roadmap

### Fase 1: Externalizar conocimiento
- Extraer normativa, tablas NRV, clasificaciones de ingredientes de los prompts a `/knowledge/`
- Crear catálogo propietario de ingredientes
- Crear plantillas de documentos internos

### Fase 2: Estructurar repo ✅ (completado)
- Separación clara: `agents/`, `pipeline/`, `tools/`, `tests/`
- Agentes legacy en `agents/legacy/`

### Fase 3: Persistencia (pendiente)
- Postgres para historial de ejecuciones
- Sincronización batch Navision → Postgres

### Fase 4: API + Navision (pendiente)
- FastAPI con endpoint `/analyze-supplement`
- Tools de consulta en tiempo real a Navision

### Fase 5: Docker + Frontend (pendiente)
- Containerización para despliegue
- UI cuando haya usuarios finales
