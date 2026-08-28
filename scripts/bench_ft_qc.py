"""Benchmark FT (Ficha Técnica) y QC: gemini-flash-lite vs minimax-m3.

Aísla la variable 'modelo' con contexto upstream fijo (KIC+Reg de un run real).
Mismo code path de producción (_run_step, sin search — estos agentes no buscan).
"""
from __future__ import annotations
import json, os, time, traceback

RUN = "outputs/run_mix260025_fix"
OUTDIR = "outputs/bench_ft_qc"
os.makedirs(OUTDIR, exist_ok=True)

MODELS = ["google/gemini-3.1-flash-lite", "minimax/minimax-m3"]  # actual vs candidato

from pipeline import orchestrator as O
from pipeline.config import AGENT_PREFIXES

F = open(f"{RUN}/formula.txt", encoding="utf-8").read()
kic_fixed = json.load(open(f"{RUN}/agente_1_kic_v2.json", encoding="utf-8"))
reg_fixed = json.load(open(f"{RUN}/agente_2_regulatorio_v2.json", encoding="utf-8"))

PRICE = {"google/gemini-3.1-flash-lite": (0.25, 1.50), "minimax/minimax-m3": (0.30, 1.20)}

AGENTS = [
    ("Ficha Técnica", "Agente 3: Ficha Técnica v2", 3, O.FICHA_TECNICA_INSTRUCTIONS,
     lambda: f"Genera la ficha técnica completa del siguiente producto:\n\n{F}\n\n{O.ctx_ft({'KIC': kic_fixed, 'Regulatorio': reg_fixed})}"),
    ("QC", "Agente 8: QC v2", 8, O.QC_INSTRUCTIONS,
     lambda: f"Define el plan de control de calidad del siguiente producto:\n\n{F}"),
]


def _nonempty_phases(d: dict) -> int:
    return sum(1 for k, v in d.items() if k.startswith("fase_") and v)


def cov(key: str, d: dict) -> str:
    if key == "Ficha Técnica":
        fases = _nonempty_phases(d)
        esp = d.get("fase_5_especificaciones_tecnicas", {}) or {}
        fq = esp.get("especificaciones_fisicoquimicas", {}) or {}
        mb = esp.get("especificaciones_microbiologicas", {}) or {}
        n_specs = (len(fq) if isinstance(fq, dict) else 0) + (len(mb) if isinstance(mb, dict) else 0)
        nut = d.get("fase_3_informacion_nutricional", {}) or {}
        vm = (nut.get("tabla_nutricional_por_dosis", {}) or {}).get("vitaminas_minerales", {}) or {}
        return f"{fases}/8 fases · {n_specs} specs · {len(vm)} vit/min"
    if key == "QC":
        fases = _nonempty_phases(d)
        f6 = d.get("fase_6_ensayos_analiticos_adicionales", {}) or {}
        f7 = d.get("fase_7_plan_estabilidad", {}) or {}
        items = 0
        for src in (f6, f7):
            if isinstance(src, dict):
                for v in src.values():
                    if isinstance(v, list):
                        items += len(v)
        return f"{fases}/8 fases · {items} ensayos/criterios"
    return "?"


def schema_err(key, d):
    m = O.AGENT_OUTPUT_MODELS.get(key)
    if m is None:
        return "—"
    try:
        m.model_validate(d); return 0
    except Exception as e:
        errs = getattr(e, "errors", None)
        try: return len(errs()) if callable(errs) else "err"
        except Exception: return "err"


results = []
for key, label, pfx_n, instr, build in AGENTS:
    prefix = AGENT_PREFIXES[pfx_n]
    prompt = build()
    for model in MODELS:
        os.environ[f"{prefix}_MODEL"] = model
        print(f"\n{'='*70}\n▶ {key}  |  {model}\n{'='*70}", flush=True)
        row = {"agente": key, "modelo": model}
        t0 = time.time()
        try:
            _, data, _, elapsed = O._run_step(key, label, pfx_n, instr, prompt)
            tr = data.get("_trazabilidad", {}) if isinstance(data, dict) else {}
            it, ot = tr.get("input_tokens", 0) or 0, tr.get("output_tokens", 0) or 0
            pin, pout = PRICE[model]
            row.update({
                "ok": bool(data), "schema_err": schema_err(key, data),
                "cobertura": cov(key, data),
                "fuentes": len(data.get("fuentes_consultadas", []) or []),
                "in_tok": it, "out_tok": ot,
                "coste_usd": round(it/1e6*pin + ot/1e6*pout, 5),
                "latencia_s": round(elapsed, 1), "attempts": tr.get("attempts", "?"),
            })
            json.dump(data, open(f"{OUTDIR}/{key.replace(' ','_')}__{model.replace('/','_')}.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
        except Exception as e:
            row.update({"ok": False, "error": f"{type(e).__name__}: {e}"[:200], "latencia_s": round(time.time()-t0, 1)})
            print("❌", traceback.format_exc()[:800], flush=True)
        results.append(row)
        json.dump(results, open(f"{OUTDIR}/_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("\n\n" + "#"*70 + "\nRESULTADOS FT / QC\n" + "#"*70)
for r in results:
    print(f"{r['agente']:15} {r['modelo']:30} ok={r.get('ok')} sch={r.get('schema_err')} "
          f"cob=[{r.get('cobertura')}] fnt={r.get('fuentes')} "
          f"tok={r.get('in_tok')}/{r.get('out_tok')} ${r.get('coste_usd')} {r.get('latencia_s')}s")
    if r.get("error"): print("   ERROR:", r["error"])
print("\n✅ Detalle en", OUTDIR)
