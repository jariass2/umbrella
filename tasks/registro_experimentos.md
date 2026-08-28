# Registro de experimentos y decisiones técnicas

Bitácora de pruebas, benchmarks y decisiones de la fase de construcción/
sintonización del equipo de agentes. Se alimenta **a medida que se hacen las
pruebas**, para que al entregar la fase se pueda componer el documento de
"tareas realizadas" a partir de aquí.

Cada entrada sigue esta plantilla:

```
## AAAA-MM-DD — Título corto
**Tipo:** benchmark | fix | ajuste-prompt | upgrade | decisión
**Objetivo:** qué se quería resolver/medir.
**Método:** cómo se midió (fórmula, code path, contexto fijo, nº ejecuciones).
**Resultados:** datos/tabla.
**Decisión:** qué se hizo con el resultado.
**Artefactos:** archivos, scripts, commits, outputs.
```

> Regla: no borrar entradas. Si algo se revierte, se añade una entrada nueva
> que lo explique y enlaza a la anterior.

---

## 2026-06-29 — Parser FT PDF: ingredientes mayoritarios omitidos (Colágeno, Glicina)
**Tipo:** fix
**Objetivo:** el parser descartaba ingredientes cuya dosis de activo ≥ 1000 mg venía
sin separador de millar (`1250,000000`, `4500,000000`) → Colágeno y Glicina
desaparecían del informe.
**Método:** parse real del PDF `Formula 3 MIX 260025.pdf`; conteo de ingredientes
antes/después; verificación end-to-end vía endpoint `/parse-formula-pdf`.
**Resultados:** 15 → **17 ingredientes**. La regex `_NUM` solo admitía `\d{1,3}` antes
del decimal salvo agrupación con puntos de millar; la columna de activo escribe los
valores ≥1000 planos.
**Decisión:** regex `_NUM` acepta también dígitos sin agrupar. Sin regresión en el PDF
de referencia (`FT Formula 1 MIX 250188.pdf`, 12 ingredientes intactos).
**Artefactos:** `dashboard/utils/ft_pdf_parser.py`; commit `d052641`.

## 2026-06-29 — Tabla nutricional determinista + aptitud dietas
**Tipo:** fix
**Objetivo:** la tabla nutricional (LLM) salía incompleta (4/9 vit-min, proteína 0,
B12 0%) y la aptitud para dietas estaba hardcodeada ("Bajo petición" en todo).
**Método:** análisis del output del agente FT; reconstrucción determinista desde KIC +
canónica + VRN legal (Anexo XIII Reg. 1169/2011).
**Resultados:** 9/9 vit-min con dosis exacta y %VRN correcto (B12 0,375 µg / 15%);
proteína 5,75 g (Colágeno + Glicina); dietas Vegano/Vegetariano → "No apto" por origen
animal (colágeno).
**Decisión:** vit/min y %VRN se calculan (no se piden al LLM); macros del FT; aptitud
derivada de la fórmula. 62 tests OK.
**Artefactos:** `pipeline/report_composer.py`; commit `d052641`.

## 2026-07-03 — Tabla de costes por agente vacía
**Tipo:** fix
**Objetivo:** la columna "Coste est." del Anexo salía `—` en todos los agentes.
**Método:** inspección de `PRICING_PER_1M` vs modelos en uso; precios reales
consultados en la API pública de OpenRouter.
**Resultados:** la tabla de precios estaba obsoleta (mimo/kimi/gemini-flash); los
modelos reales (`minimax/minimax-m3`, `google/gemini-3.1-flash-lite`) no casaban →
(0,0). Precios OpenRouter: minimax-m3 `0.30/1.20`, gemini-3.1-flash-lite `0.25/1.50`.
**Decisión:** `PRICING_PER_1M` actualizado. Coste total del run: **$0.1116**.
**Artefactos:** `pipeline/report_composer.py`; commit `d052641`.

## 2026-07-03 — Upgrade Agno 2.5.11 → 2.6.21
**Tipo:** upgrade
**Objetivo:** evaluar e incorporar novedades de fiabilidad de Agno.
**Método:** revisión del changelog oficial 2.6.0–2.6.21; upgrade en `.venv`; verificación
de imports, `make_agent`, suite de tests y una ejecución real de un agente.
**Resultados:** bump menor dentro de `<3.0`, sin breaking changes que afecten el uso
(`Agent` + `OpenAILike` + Toolkits). Relevante: JSON instructions en follow-up de
providers `json_object` (2.6.14), fix de serialización no-ASCII (2.6.21). 62 tests OK;
ejecución real verifica `run()`/`content`/`metrics` + acentos preservados.
**Decisión:** adoptado. Pin subido a `agno>=2.6.21,<3.0`.
**Artefactos:** `requirements.txt`; commit `4aca3a3`.

## 2026-07-03 — Benchmark de modelos: KIC / Regulatorio / Claims
**Tipo:** benchmark
**Objetivo:** ¿conviene cambiar el modelo de los 3 agentes de razonamiento?
**Método:** code path real de producción (`_run_step`, con búsqueda y reintentos),
contexto upstream **fijo** (KIC/Reg de un run real) para aislar la variable "modelo".
1 fórmula (MIX 260025). Modelos: `minimax-m3` (actual) vs `gpt-5.4-mini` vs
`claude-haiku-4.5`. Costes recalculados con precios reales OpenRouter.
**Resultados:**

| Agente | Modelo | Cobertura | Fuentes | Schema | Coste | Latencia |
|---|---|---|---|---|---|---|
| KIC | minimax-m3 | 17 ingr, NRV correcto | 5 | drift(8)¹ | $0.024 | 252s |
| KIC | gpt-5.4-mini | 17 ingr | 5 | 0 | $0.039 | 55s |
| KIC | claude-haiku-4.5 | 17 ingr | 7 | 0 | $0.079 | 89s |
| Regulatorio | minimax-m3 | 17 semáforos | 7 | — | $0.023 | 248s |
| Regulatorio | gpt-5.4-mini | 17 semáforos | 5 | — | $0.037 | 51s |
| Regulatorio | claude-haiku-4.5 | 17 semáforos | 7 | — | $0.086 | 99s |
| Claims | minimax-m3 | 12 claims (acotado) | 8 | 0 | $0.027 | 302s |
| Claims | gpt-5.4-mini | 17 claims (sobre-claim) | **2** ⚠️ | 0 | $0.054 | 77s |
| Claims | claude-haiku-4.5 | 12 claims | 7 | 0 | $0.147 | 149s |

Coste 3 agentes: minimax-m3 **$0.074** · gpt-5.4-mini $0.130 · claude-haiku-4.5 $0.311.
¹ drift absorbido por la validación defensiva del orquestador.

Hallazgo cualitativo (revisado en el contenido): minimax-m3 cita umbrales exactos y
más regs; gpt-5.4-mini **sobre-claim** (claims hasta para aromas/colorante) con solo 2
fuentes → peor para lo regulatorio pese a "más" claims; claude-haiku-4.5 casi igual a
minimax, esquema limpio, más rápido, 4× coste.
**Decisión:** mantener `minimax-m3` en los 3 (mejor calidad/coste; drift no afecta al
informe final). `claude-haiku-4.5` = alternativa si se prioriza velocidad. **No** usar
gpt-5.4-mini en agentes regulatorios.
**Artefactos:** `scripts/bench_models.py`; `outputs/bench_models/`; commit `e0d8756`.

## 2026-07-03 — Benchmark de modelos: Ficha Técnica / QC (flash-lite vs minimax-m3)
**Tipo:** benchmark
**Objetivo:** ¿tiene sentido subir los agentes de flash-lite a minimax-m3?
**Método:** igual que arriba (code path real, contexto fijo, 1 fórmula). Sin búsqueda
(estos agentes no buscan).
**Resultados:**

| Agente | Modelo | Cobertura técnica | Fuentes | Coste | Latencia |
|---|---|---|---|---|---|
| Ficha Técnica | flash-lite | 2 specs (pH, humedad) | 2 | $0.008 | 11s |
| Ficha Técnica | **minimax-m3** | **9 specs** (aw, granulometría, densidad…) | 12 | $0.027 | 209s |
| QC | flash-lite | 7 ensayos | 3 | $0.004 | 8s |
| QC | **minimax-m3** | **22 ensayos** (cuantif. por activo + estabilidad) | 12 | $0.018 | 169s |

El "más" es sustancia real (verificado en contenido): actividad de agua, granulometría,
cuantificación analítica por cada activo. Latencia oculta bajo la ruta crítica (FT<Claims,
QC<KIC).
**Decisión:** subir FT y QC a minimax-m3 (ver decisión global siguiente).
**Artefactos:** `scripts/bench_ft_qc.py`; `outputs/bench_ft_qc/`; commit `e0d8756`.

## 2026-07-03 — Decisión: configuración calidad-máxima (9× minimax-m3) + validación
**Tipo:** decisión
**Objetivo:** con prioridad calidad > velocidad (coste no es restricción), fijar modelo
por agente.
**Método:** recomendación agente por agente a partir de los benchmarks (medido en KIC/
Reg/Claims/FT/QC; inferido en Etiqueta/Formatos/Docs); aplicación en `.env`; validación
end-to-end del pipeline completo sobre MIX 260025.
**Resultados:** los 9 agentes en `minimax/minimax-m3`. Run de validación: **9/9 OK**, sin
regresiones (Colágeno/Glicina, proteína 5,8 g, "No apto", costes). Trade-off medido vs
config mixta anterior:

| | Mixta (flash-lite) | Calidad-máx (9× minimax) | Δ |
|---|---|---|---|
| Tiempo total | 12m 13s | 17m 27s | +43% |
| Coste/informe | $0.1116 | $0.2544 | +128% |

Sobrecoste por **más contenido** (FT 39k tokens salida vs 3k; Docs 35k vs 2k), no por
precio. Docs Internos se disparó (446s / 35k) por contención de endpoint → candidato a
revertir a flash-lite si se quiere recortar sin tocar calidad de cara al cliente.
**Decisión:** config calidad-máxima adoptada en `.env` (gitignorado; backup
`.env.bak.20260703-114826`). Pendiente opcional: revertir solo Docs.
**Artefactos:** `outputs/run_mix260025_qmax/` (informe + PDF 65 págs).

---

## Pendientes de documentar (cuando se hagan)
- Ajuste de prompts por agente (antes/después, con métrica de mejora).
- Benchmark en 2ª/3ª fórmula (confirmar minimax vs haiku y los "[inferido]").
- Integración KB interno / NAVISION (cuando existan).
