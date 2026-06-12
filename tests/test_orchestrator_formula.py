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

from pipeline.orchestrator import _enriquecer_formula, _api_error_envelope  # noqa: E402

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


def test_api_error_envelope_detecta_error_disfrazado_de_exito():
    # El cuerpo de error de mimo que se guardó como "éxito" en run_38.
    err = {"message": "Extra data: line 1 column 91 (char 90)",
           "type": "BadRequestError", "param": None, "code": 400}
    assert _api_error_envelope({"error": err, "_trazabilidad": {}}) == err
    # Un resultado válido NO es un sobre de error.
    assert _api_error_envelope({"parte_a_claims_regulatorios": {}}) is None
    # 'error' como string (campo legítimo de algún schema) tampoco.
    assert _api_error_envelope({"error": "ninguno"}) is None
    assert _api_error_envelope([1, 2]) is None


# ── Regresión: recorte de F y slim Regulatorio para Claims (QA 2026-06-12).
# Claims tarda 9+ min porque el input (47K tokens) se reinyecta en cada tool
# call del agent loop. La materia prima confidencial y la normativa detallada
# de Regulatorio son ruido para Claims. ───────────────────────────────────

from pipeline.orchestrator import _F_para_claims, ctx_claims  # noqa: E402


def test_F_para_claims_recorta_materia_prima(tmp_path):
    """Claims NO debe recibir la sección confidencial de materia prima.

    Verifica que la versión recortada de F solo contiene cabecera del
    producto + bloque de activos (sin la tabla de materia prima detallada).
    La instrucción de CONFIDENCIALIDAD se mantiene porque protege contra
    fugas de materia prima en el output del agente.
    """
    canonica = {
        "ingredients": [
            {"name": "Boswellia serrata Ext., 30% AKBA", "raw_mg": 166.67,
             "active_mg": 50.0, "active_name": "AKBA", "pct_active": "30", "unit": "mg"},
        ]
    }
    F_enriquecido = _enriquecer_formula(F, _canonica(tmp_path, canonica["ingredients"]))
    recortado = _F_para_claims(F_enriquecido)
    # El bloque de activos SÍ debe estar (es lo que Claims necesita).
    assert "50 mg de AKBA" in recortado
    # La materia prima detallada NO debe aparecer (es confidencial para Claims).
    assert "166.67mg" not in recortado
    assert "2.26mg" not in recortado
    # La instrucción de confidencialidad SÍ se mantiene (defensa en profundidad).
    assert "CONFIDENCIAL" in recortado


def test_F_para_claims_sin_canónica_devuelve_F(tmp_path):
    """Si no hay canónica (run antiguo), F no se modifica."""
    F_sin = "Producto\n- Vit C: 100 mg"
    assert _F_para_claims(F_sin) == F_sin


def test_ctx_claims_ultra_slim_sin_normativa_detalle():
    """El contexto Regulatorio para Claims no debe incluir normativa_aplicable,
    evaluacion_cuantitativa, advertencias_etiquetado ni condiciones — esos
    los construye Claims desde su propio conocimiento del Reg. UE 432/2012."""
    reg = {
        "clasificacion_producto": {"tipo": "complemento_alimentario"},
        "ingredientes": [{
            "nombre": "Vit C",
            "semaforo": "✅",
            "dictamen": "PERMITIDO",
            "normativa_aplicable": ["Reglamento CE 1924/2006", "RD 1487/2009"],
            "evaluacion_cuantitativa": {"dosis_formula": "100 mg"},
            "condiciones": "ninguna",
            "advertencias_etiquetado": "ninguna",
        }],
    }
    out = ctx_claims({"Regulatorio": reg})
    # Lo esencial: semáforo + dictamen (accionable para Claims).
    assert "PERMITIDO" in out
    assert "✅" in out
    # Lo descartable: normativa, condiciones, advertencias.
    assert "1924/2006" not in out
    assert "evaluacion_cuantitativa" not in out


if __name__ == "__main__":
    import tempfile
    for fn in (test_sin_canonica_devuelve_formula_intacta,
               test_canonica_sin_activos_no_modifica,
               test_enriquece_con_activo_y_framing,
               test_F_para_claims_recorta_materia_prima,
               test_F_para_claims_sin_canónica_devuelve_F,
               test_ctx_claims_ultra_slim_sin_normativa_detalle):
        with tempfile.TemporaryDirectory() as d:
            fn(Path(d))
        print(f"✅ {fn.__name__}")
    test_api_error_envelope_detecta_error_disfrazado_de_exito()
    print("✅ test_api_error_envelope_detecta_error_disfrazado_de_exito")
