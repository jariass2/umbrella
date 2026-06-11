"""Regresión: el endpoint /analyze debe rechazar input inválido con un 400
que lleve un mensaje visible para el usuario.

# Regression: ISSUE-001 — el envío del formulario vacío/ inválido fallaba en
# silencio. El backend ya devolvía el error con status 400, pero HTMX no hace
# swap de respuestas no-2xx, así que el usuario no veía nada (fix en
# dashboard/templates/index.html). Estos tests blindan el contrato del que
# depende ese fix de frontend: /analyze SIEMPRE responde 400 + mensaje ante
# input inválido.
# Found by /qa on 2026-06-02
# Report: .gstack/qa-reports/qa-report-localhost-8503-2026-06-02.md

Uso:
    python -m pytest tests/test_analyze_validation.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flask_app  # noqa: E402
from dashboard.api import store  # noqa: E402
from dashboard.utils.formula_parser import MAX_PRODUCT_NAME_LEN  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Test client de Flask con la DB apuntando a un sqlite temporal."""
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test_dashboard.db")
    store.init_db()
    flask_app.app.config.update(TESTING=True)
    with flask_app.app.test_client() as c:
        yield c


def test_formulario_vacio_devuelve_400_con_mensaje(client):
    resp = client.post("/analyze", data={})
    assert resp.status_code == 400
    body = resp.get_data(as_text=True)
    assert "Falta el nombre del producto" in body
    assert "error-msg" in body  # la clase que el frontend renderiza


def test_producto_sin_ingredientes_devuelve_400(client):
    resp = client.post("/analyze", data={"product_name": "Test QA Producto"})
    assert resp.status_code == 400
    body = resp.get_data(as_text=True)
    assert "Añade al menos un ingrediente" in body
    assert "warning-msg" in body


def test_ingrediente_sin_nombre_no_cuenta_como_valido(client):
    # Filas con nombre vacío se ignoran → no hay ingredientes válidos → 400.
    resp = client.post(
        "/analyze",
        data={"product_name": "Test", "ing_name": "", "ing_dosage": "10", "ing_unit": "mg"},
    )
    assert resp.status_code == 400
    assert "Añade al menos un ingrediente" in resp.get_data(as_text=True)


def test_nombre_de_producto_demasiado_largo_devuelve_400(client):
    largo = "x" * (MAX_PRODUCT_NAME_LEN + 1)
    resp = client.post(
        "/analyze",
        data={"product_name": largo, "ing_name": "Vit C", "ing_dosage": "80", "ing_unit": "mg"},
    )
    assert resp.status_code == 400
    assert "demasiado largo" in resp.get_data(as_text=True).lower()


# ── Regresión: sidebar OOB debe exponer la dosis de activo al recargar un
# run con formula_canonica.json (Fix 2026-06-10: el partial estaba desactualizado
# y load_run() no leía la canónica, así que el campo "Activo" aparecía vacío
# al hacer click en un run del historial). ────────────────────────────────

def test_load_run_rellena_campo_activo_desde_canonica(client, tmp_path):
    """Al recargar un run con formula_canonica.json, el OOB del sidebar debe
    pre-rellenar `name="ing_active"` con la dosis de activo."""
    # Crea un run y escribe su formula_canonica.json en el output_dir.
    formula_text = "Producto X\n- Magnesio Bisglicinato, 12% Mg: 833.33 mg\n- Boswellia, 30% AKBA: 166.67 mg"
    run_id = store.create_run("Producto X", formula_text)
    output_dir = tmp_path / f"run_{run_id}"
    output_dir.mkdir()
    store.set_run_output_dir(run_id, str(output_dir))
    canonica = {
        "product_name": "Producto X",
        "ingredients": [
            {"name": "Magnesio Bisglicinato, 12% Mg", "raw_mg": 833.33,
             "active_mg": 100.0, "active_name": "Mg", "pct_active": "12", "unit": "mg"},
            {"name": "Boswellia, 30% AKBA", "raw_mg": 166.67,
             "active_mg": 50.0, "active_name": "AKBA", "pct_active": "30", "unit": "mg"},
        ],
    }
    (output_dir / "formula_canonica.json").write_text(
        __import__("json").dumps(canonica, ensure_ascii=False), encoding="utf-8"
    )

    resp = client.get(f"/run/{run_id}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    # El partial OOB debe incluir los inputs `ing_active` con el valor de la
    # canónica — no un value vacío.
    assert 'name="ing_active"' in body
    assert 'value="100"' in body, "Dosis de activo del Mg (100mg) no se rellenó"
    assert 'value="50"' in body, "Dosis de activo del AKBA (50mg) no se rellenó"
    # Y los hidden de % y nombre de activo.
    assert 'name="ing_pct"' in body
    assert 'value="12"' in body
    assert 'name="ing_active_name"' in body


def test_load_run_sin_canonica_no_falla(client):
    """Run antiguo (pre-Fase 7, sin formula_canonica.json) debe cargar el
    sidebar sin error y con `ing_active` vacío — comportamiento aceptable."""
    formula_text = "Legacy\n- Vit C: 80 mg"
    run_id = store.create_run("Legacy", formula_text)

    resp = client.get(f"/run/{run_id}")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # El partial sigue exponiendo el campo Activo, simplemente sin valor.
    assert 'name="ing_active"' in body
    assert 'placeholder="Activo"' in body
