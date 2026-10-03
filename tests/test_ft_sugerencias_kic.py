"""La ficha técnica pide y publica sus sugerencias sobre los datos de entrada.

El campo existía en el schema y el prompt no lo pedía: ningún run lo devolvía
y cada ejecución levantaba el aviso «no incluye sugerencias mejora ficha kic».
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.ficha_tecnica_agente_v2 import FICHA_TECNICA_INSTRUCTIONS, FichaTecnica  # noqa: E402
from pipeline.report_composer import fmt_propuestas_mejora  # noqa: E402


def test_prompt_pide_la_clave():
    assert '"sugerencias_mejora_ficha_kic"' in FICHA_TECNICA_INSTRUCTIONS
    assert "FASE 9" in FICHA_TECNICA_INSTRUCTIONS


def test_schema_acepta_lista_y_dict():
    FichaTecnica.model_validate({"sugerencias_mejora_ficha_kic": [{"sugerencia": "x"}]})
    FichaTecnica.model_validate({"sugerencias_mejora_ficha_kic": {"sugerencia": "x"}})


def test_el_informe_publica_las_sugerencias():
    ft = {"sugerencias_mejora_ficha_kic": [{
        "sugerencia": "Especie del extracto de bambú sin acreditar",
        "detalle": "Condiciona el estatus Novel Food",
        "accion_sugerida": "Pedir certificado de especie al proveedor"}]}
    out = "\n".join(fmt_propuestas_mejora({}, {}, ft))
    assert "Datos de entrada a completar" in out and "bambú" in out
