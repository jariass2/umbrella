"""Regresión: un run nuevo no debe heredar outputs de agentes de un run
previo que compartiera el mismo output_dir.

# Regression: al "Analizar Fórmula", todos los agentes se ponían en verde de
# inmediato como si se hubieran ejecutado al instante. Causa raíz: run_pipeline
# decide que un agente está "completed" por la mera existencia de su JSON en
# output_dir, y nada limpiaba los ficheros stale de runs previos. El bucle de
# polling los leía en el primer ciclo (0.5s) y los daba por buenos.
# Evidencia: outputs/run_46/ contenía agente_4_claims_v2.json y
# agente_5_etiqueta_v2.json con mtime de 5 días antes — Claims ni siquiera
# llegó a terminar en ese run (pipeline.log: "esperando slot").
#
# Uso:
#   python -m pytest tests/test_runner_purge_stale.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.api.runner import _AGENT_FILENAME, _purge_stale_agent_outputs


def test_purge_removes_stale_agent_outputs_but_keeps_inputs(tmp_path: Path):
    """El purge borra JSON/MD de agentes stale y conserva las entradas."""
    # Un agente stale de un run previo (lo que disparaba el bug).
    stale_json = tmp_path / "agente_4_claims_v2.json"
    stale_md = tmp_path / "agente_4_claims_v2.md"
    stale_json.write_text('{"error": "stale"}', encoding="utf-8")
    stale_md.write_text("# stale", encoding="utf-8")

    # Entradas que SÍ debe conservar (las escribe /analyze y lee el orchestrator).
    canonica = tmp_path / "formula_canonica.json"
    formula_input = tmp_path / "formula_input.txt"
    canonica.write_text('{"product_name": "X", "ingredients": []}', encoding="utf-8")
    formula_input.write_text("X 100 mg", encoding="utf-8")

    removed = _purge_stale_agent_outputs(str(tmp_path))

    assert not stale_json.exists(), "el JSON stale sobrevivió → bug de verde instantáneo"
    assert not stale_md.exists(), "el MD stale sobrevivió"
    assert canonica.exists(), "formula_canonica.json es entrada: NO debe borrarse"
    assert formula_input.exists(), "formula_input.txt es entrada: NO debe borrarse"
    assert removed == 2


def test_purge_covers_all_agents(tmp_path: Path):
    """Cualquier agente puede dejar ficheros stale; el purge cubre los 9."""
    for filename in _AGENT_FILENAME.values():
        (tmp_path / f"{filename}.json").write_text("{}", encoding="utf-8")
        (tmp_path / f"{filename}.md").write_text("# x", encoding="utf-8")

    removed = _purge_stale_agent_outputs(str(tmp_path))

    leftover = [p.name for p in tmp_path.glob("agente_*")]
    assert leftover == [], f"quedaron ficheros de agente sin purgar: {leftover}"
    assert removed == 2 * len(_AGENT_FILENAME)


def test_purge_on_clean_dir_is_noop(tmp_path: Path):
    """Un dir limpio (run de verdad) no rompe nada: 0 borrados, sin errores."""
    removed = _purge_stale_agent_outputs(str(tmp_path))
    assert removed == 0
