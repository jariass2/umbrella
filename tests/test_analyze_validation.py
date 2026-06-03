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
