"""Regresión: cargar una fórmula nueva debe resetear el DAG de agentes.

# Regression: al arrastrar un FT PDF mientras se veía un run anterior
# completado, el DAG de agentes seguía mostrando los estados (en verde) del
# run viejo — los agentes de aquella fórmula, no de la nueva. El cliente ahora
# llama a GET /reset-pipeline al cargar la fórmula, que devuelve el partial
# main_content en estado 'sin run' (todos en espera). Estos tests blindan ese
# contrato:
#   - 200 y contiene los 9 agentes todos en espera
#   - sin run → sin barra de descarga ni poll de estado
#
# Uso:
#   python -m pytest tests/test_reset_pipeline.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import flask_app  # noqa: E402
from dashboard.api import store  # noqa: E402
from dashboard.api.runner import AGENT_ORDER  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "test_dashboard.db")
    store.init_db()
    flask_app.app.config.update(TESTING=True)
    with flask_app.app.test_client() as c:
        yield c


def test_reset_pipeline_devuelve_todos_en_espera(client):
    resp = client.get("/reset-pipeline")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)

    # Ningún agente puede verse como completado/ejecutando/error.
    assert "status-completed" not in body
    assert "status-running" not in body
    assert "status-error" not in body
    # Todos los agentes presentes y en espera.
    assert body.count("status-waiting") == len(AGENT_ORDER)


def test_reset_pipeline_no_tiene_descarga_ni_poll(client):
    """Estado 'sin run': nada de barra de descarga ni poll cada 2s."""
    body = client.get("/reset-pipeline").get_data(as_text=True)
    assert "btn-download" not in body        # sin /download/...
    assert "pipeline-status" not in body     # sin hx-get de poll
    assert "Detener análisis" not in body    # sin .stop-bar
