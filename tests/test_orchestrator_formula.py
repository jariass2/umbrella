"""Tests del enriquecimiento de la fórmula con dosis de activo (Fase 7b.4).

`_enriquecer_formula` añade la dosis de ACTIVO (de `formula_canonica.json`, FT
PDF) + instrucción de confidencialidad al texto que reciben los agentes, sin
borrar las líneas originales (materia prima, que necesitan Docs/QC).

Uso:
    python -m pytest tests/test_orchestrator_formula.py -v
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.orchestrator import _enriquecer_formula  # noqa: E402

F = "MIX 250188 C\n\n- Boswellia serrata Ext., 30% AKBA: 166.67mg\n- Vit. B6 HCl: 2.26mg"


def _canonica(tmp_path, ings):
    (tmp_path / "formula_canonica.json").write_text(
        json.dumps({"ingredients": ings}), encoding="utf-8")
    return str(tmp_path)


def test_sin_canonica_devuelve_formula_intacta(tmp_path):
    assert _enriquecer_formula(F, str(tmp_path)) == F


def test_canonica_sin_activos_no_modifica(tmp_path):
    d = _canonica(tmp_path, [{"name": "X", "active_mg": None}])
    assert _enriquecer_formula(F, d) == F


def test_enriquece_con_activo_y_framing(tmp_path):
    d = _canonica(tmp_path, [
        {"name": "Boswellia serrata Ext., 30% AKBA", "active_mg": 50, "active_name": "AKBA", "unit": "mg"},
        {"name": "Vit. B6 HCl", "active_mg": 1.4, "active_name": "Vit. B6", "unit": "mg"},
    ])
    out = _enriquecer_formula(F, d)
    # Líneas originales conservadas (materia prima la necesitan Docs/QC).
    assert "166.67mg" in out
    # Dosis de activo añadida.
    assert "50 mg de AKBA" in out
    assert "1.4 mg de Vit. B6" in out
    # Framing de confidencialidad presente.
    assert "CONFIDENCIAL" in out
    assert "claims" in out.lower()


if __name__ == "__main__":
    import tempfile
    for fn in (test_sin_canonica_devuelve_formula_intacta,
               test_canonica_sin_activos_no_modifica,
               test_enriquece_con_activo_y_framing):
        with tempfile.TemporaryDirectory() as d:
            fn(Path(d))
        print(f"✅ {fn.__name__}")
