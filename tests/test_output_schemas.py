"""Valida el contrato real entre cada agente y `report_composer.py`.

Dos niveles de garantía:

1. Contrato OPERACIONAL (`test_agent_output_contract`): comprueba que las claves
   por fase que `report_composer.py` realmente lee están presentes. Faltar una =
   hueco en el informe ejecutivo final.

2. Schema PYDANTIC (`test_agent_output_pydantic_schema`): tras Sprint 1.1 los
   schemas (`KICAnalysis`, `FichaTecnica`, etc.) están realineados con la
   estructura por fases del prompt, así que un `model_validate` es ahora una
   prueba real (no un falso verde como antes). Esto detecta drift de tipos:
   por ejemplo, que `ventajas_clave` empiece a llegar como `int`.

Uso:
    python -m pytest tests/test_output_schemas.py -v
    python tests/test_output_schemas.py   # CLI sin pytest
"""

import json
import sys
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None  # type: ignore[assignment]

# Asegura imports de `agents.*` cuando se ejecuta como script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel  # noqa: E402

from agents.kic_agent_v2 import KICAnalysis  # noqa: E402
from agents.ficha_tecnica_agente_v2 import FichaTecnica  # noqa: E402
from agents.claims_agent_v2 import ClaimsAnalysis  # noqa: E402
from agents.etiqueta_agent_v2 import EtiquetaAnalysis  # noqa: E402
from agents.formatos_agent_v2 import FormatosAnalysis  # noqa: E402
from agents.docs_internos_agent_v2 import DocsInternosAnalysis  # noqa: E402
from agents.qc_agent_v2 import PlanQCAnalysis  # noqa: E402

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs" / "v2"

# Schemas realineados (Sprint 1.1). Regulatorio no tiene modelo Pydantic.
AGENT_PYDANTIC_MODELS: dict[str, type[BaseModel]] = {
    "KIC":           KICAnalysis,
    "Ficha Técnica": FichaTecnica,
    "Claims":        ClaimsAnalysis,
    "Etiqueta":      EtiquetaAnalysis,
    "Formatos":      FormatosAnalysis,
    "Docs Internos": DocsInternosAnalysis,
    "QC":            PlanQCAnalysis,
}

# Claves que `report_composer.py` lee por agente. Faltar una = hueco en el informe.
# Extraído de `pipeline/report_composer.py` (grep fase_N_*).
AGENT_CONTRACT: dict[str, tuple[str, set[str]]] = {
    "KIC": ("agente_1_kic_v2.json", {
        "fase_1_clasificacion",
        "fase_2_ingredientes",
        "fase_4_valoracion_global",
        "fuentes_consultadas",
    }),
    "Regulatorio": ("agente_2_regulatorio_v2.json", {
        "ingredientes",
        "evaluacion_global",
    }),
    "Ficha Técnica": ("agente_3_ficha_técnica_v2.json", {
        "fase_1_identificacion",
        "fase_2_composicion",
        "fase_3_informacion_nutricional",
        "fase_4_alergenos",
        "fase_6_conservacion_vida_util",
        "fase_7_modo_empleo_advertencias",
    }),
    "Claims": ("agente_4_claims_v2.json", {
        "parte_a_claims_regulatorios",
        "parte_b_selling_points_comerciales",
    }),
    "Etiqueta": ("agente_5_etiqueta_v2.json", {
        "fase_2_texto_por_caras",
        "fase_3_tabla_nutricional_completa",
        "fase_4_lista_ingredientes_completa",
    }),
    "Formatos": ("agente_6_formatos_v2.json", {
        "fase_1_evaluacion_formatos",
        "fase_4_recomendacion_final",
    }),
    "Docs Internos": ("agente_7_docs_internos_v2.json", {
        "fase_1_lista_materiales_navision",
        "fase_2_formula_cuantitativa",
    }),
    "QC": ("agente_8_qc_v2.json", {
        "fase_1_ftir",
        "fase_7_plan_estabilidad",
    }),
}


def _check(agent_key: str, filename: str, required_keys: set[str]) -> list[str]:
    """Devuelve lista de errores para un agente. Vacía si todo OK."""
    path = OUTPUTS_DIR / filename
    if not path.exists():
        return [f"sin output ({filename})"]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not data:
        return ["JSON vacío o no es dict"]
    missing = required_keys - set(data.keys())
    return [f"falta clave: {k}" for k in sorted(missing)]


_CASES = [(k, v[0], v[1]) for k, v in AGENT_CONTRACT.items()]


def _decorator():
    if pytest is None:
        return lambda fn: fn
    return pytest.mark.parametrize(
        "agent_key,filename,required_keys", _CASES,
        ids=[c[0] for c in _CASES],
    )


@_decorator()
def test_agent_output_contract(agent_key: str, filename: str,
                               required_keys: set[str]):
    errors = _check(agent_key, filename, required_keys)
    if not errors:
        return
    path = OUTPUTS_DIR / filename
    if not path.exists() and pytest is not None:
        pytest.skip(errors[0])
        return
    msg = f"{agent_key} ({filename}):\n  - " + "\n  - ".join(errors)
    if pytest is not None:
        pytest.fail(msg)
    else:
        raise AssertionError(msg)


_PYDANTIC_CASES = [
    (k, AGENT_CONTRACT[k][0], cls)
    for k, cls in AGENT_PYDANTIC_MODELS.items()
]


def _decorator_pydantic():
    if pytest is None:
        return lambda fn: fn
    return pytest.mark.parametrize(
        "agent_key,filename,model_cls", _PYDANTIC_CASES,
        ids=[c[0] for c in _PYDANTIC_CASES],
    )


@_decorator_pydantic()
def test_agent_output_pydantic_schema(agent_key: str, filename: str,
                                      model_cls: type[BaseModel]):
    """Tras Sprint 1.1 los schemas mapean 1-a-1 con el output del prompt:
    `model_validate` es una garantía real, no un falso verde."""
    path = OUTPUTS_DIR / filename
    if not path.exists():
        if pytest is not None:
            pytest.skip(f"sin output ({filename})")
            return
        raise AssertionError(f"sin output ({filename})")
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    # Si esto lanza ValidationError, el LLM ha derivado del contrato
    # y hay que corregir prompt o schema.
    model_cls.model_validate(raw)


def _cli() -> int:
    fails = 0

    print("\n── Contrato operacional (claves por fase) ──")
    for agent_key, filename, required_keys in _CASES:
        errors = _check(agent_key, filename, required_keys)
        if not errors:
            print(f"✅ {agent_key}: contrato OK ({len(required_keys)} claves)")
            continue
        if errors == [f"sin output ({filename})"]:
            print(f"⏭️  {agent_key}: {errors[0]}")
            continue
        fails += 1
        print(f"❌ {agent_key}:")
        for e in errors:
            print(f"     {e}")

    print("\n── Schemas Pydantic realineados ──")
    for agent_key, filename, model_cls in _PYDANTIC_CASES:
        path = OUTPUTS_DIR / filename
        if not path.exists():
            print(f"⏭️  {agent_key}: sin output ({filename})")
            continue
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            model_cls.model_validate(raw)
            print(f"✅ {agent_key}: schema {model_cls.__name__} OK")
        except Exception as e:
            fails += 1
            msg = str(e).replace("\n", " ")[:300]
            print(f"❌ {agent_key} ({model_cls.__name__}): {msg}")

    return fails


if __name__ == "__main__":
    sys.exit(_cli())
