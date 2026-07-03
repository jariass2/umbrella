"""Benchmark A/B de modelos en los 3 agentes de razonamiento (KIC, Regulatorio,
Claims), aislando la variable 'modelo' con contexto upstream fijo.

Uso:
    .venv/bin/python scripts/bench_models.py

No toca .env: sobrescribe {PREFIX}_MODEL en os.environ por ejecución (mismo
seam que producción: get_agent_config lee la env var primero).
"""
from __future__ import annotations

import json
import os
import time
import traceback

RUN = "outputs/run_mix260025_fix"          # fuente de fórmula + contexto upstream fijo
OUTDIR = "outputs/bench_models"
os.makedirs(OUTDIR, exist_ok=True)

# Modelos a comparar (IDs OpenRouter). El primero es el baseline actual.
MODELS = ["minimax/minimax-m3", "openai/gpt-5.4-mini", "anthropic/claude-haiku-4.5"]

# (clave, label, nº prefijo, instrucciones, builder de prompt)
from pipeline import orchestrator as O
from pipeline.config import AGENT_PREFIXES
from pipeline.report_composer import _lookup_price

F = open(f"{RUN}/formula.txt", encoding="utf-8").read()
kic_fixed = json.load(open(f"{RUN}/agente_1_kic_v2.json", encoding="utf-8"))
reg_fixed = json.load(open(f"{RUN}/agente_2_regulatorio_v2.json", encoding="utf-8"))

AGENTS = [
    ("KIC", "Agente 1: KIC v2", 1, O.KIC_INSTRUCTIONS,
     lambda: f"Analiza la siguiente fórmula:\n\n{F}"),
    ("Regulatorio", "Agente 2: Regulatorio v2", 2, O.REGULATORY_INSTRUCTIONS,
     lambda: f"Valida regulatoriamente la siguiente fórmula:\n\n{F}\n\n{O.ctx_reg({'KIC': kic_fixed})}"),
    ("Claims", "Agente 4: Claims v2", 4, O.CLAIMS_INSTRUCTIONS,
     lambda: f"Genera los claims regulatorios y selling points del siguiente producto:\n\n{O._F_para_claims(F)}\n\n{O.ctx_claims({'Regulatorio': reg_fixed})}"),
]


def _n_ingredientes(key: str, data: dict) -> int:
    if key == "KIC":
        return len(data.get("fase_2_ingredientes", []) or [])
    if key == "Regulatorio":
        return len(data.get("ingredientes", []) or [])
    if key == "Claims":
        for k in ("claims_autorizados", "claims", "fase_2_claims", "selling_points"):
            v = data.get(k)
            if isinstance(v, list):
                return len(v)
    return 0


def _n_fuentes(data: dict) -> int:
    v = data.get("fuentes_consultadas") or data.get("fuentes") or []
    return len(v) if isinstance(v, list) else 0


def _schema_errors(key: str, data: dict) -> int | str:
    model = O.AGENT_OUTPUT_MODELS.get(key)
    if model is None:
        return "—"
    try:
        model.model_validate(data)
        return 0
    except Exception as e:
        # nº de errores de validación pydantic si están disponibles
        errs = getattr(e, "errors", None)
        try:
            return len(errs()) if callable(errs) else "err"
        except Exception:
            return "err"


results = []
for key, label, pfx_n, instr, build_prompt in AGENTS:
    prefix = AGENT_PREFIXES[pfx_n]
    prompt = build_prompt()
    for model in MODELS:
        os.environ[f"{prefix}_MODEL"] = model
        tag = f"{key}__{model.replace('/', '_')}"
        print(f"\n{'='*70}\n▶ {key}  |  {model}\n{'='*70}", flush=True)
        row = {"agente": key, "modelo": model}
        t0 = time.time()
        try:
            _, data, _, elapsed = O._run_step(key, label, pfx_n, instr, prompt)
            tr = data.get("_trazabilidad", {}) if isinstance(data, dict) else {}
            in_t = tr.get("input_tokens", 0) or 0
            out_t = tr.get("output_tokens", 0) or 0
            p_in, p_out = _lookup_price(model)
            cost = in_t / 1e6 * p_in + out_t / 1e6 * p_out
            row.update({
                "ok": bool(data),
                "json_ok": isinstance(data, dict) and "_error" not in data,
                "schema_err": _schema_errors(key, data),
                "n_ingr_claims": _n_ingredientes(key, data),
                "n_fuentes": _n_fuentes(data),
                "in_tok": in_t, "out_tok": out_t,
                "coste_usd": round(cost, 5),
                "attempts": tr.get("attempts", "?"),
                "latencia_s": round(elapsed, 1),
            })
            json.dump(data, open(f"{OUTDIR}/{tag}.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
        except Exception as e:
            row.update({"ok": False, "error": f"{type(e).__name__}: {e}"[:200],
                        "latencia_s": round(time.time() - t0, 1)})
            print("❌", traceback.format_exc()[:800], flush=True)
        results.append(row)
        json.dump(results, open(f"{OUTDIR}/_results.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

print("\n\n" + "#" * 70 + "\nRESULTADOS\n" + "#" * 70)
hdr = ["agente", "modelo", "ok", "schema_err", "n_ingr_claims", "n_fuentes",
       "in_tok", "out_tok", "coste_usd", "latencia_s", "attempts"]
print(" | ".join(hdr))
for r in results:
    print(" | ".join(str(r.get(h, "—")) for h in hdr))
print("\n✅ Detalle por modelo en", OUTDIR)
