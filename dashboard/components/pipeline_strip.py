"""Pipeline strip matching the wireframe exactly."""

from __future__ import annotations

import streamlit as st

from dashboard.api.runner import AGENT_ORDER

_STATUS_CSS = {
    "waiting": ("status-waiting", "En espera"),
    "running": ("status-running", "Ejecutando..."),
    "completed": ("status-done", "Completado"),
    "error": ("status-error", "Error"),
}


def render_pipeline_strip(agent_statuses: dict[str, str]):
    """Renderiza las 8 tarjetas de agente como HTML inline."""
    cards_html = '<div class="pipeline-strip">'

    for agent in AGENT_ORDER:
        status = agent_statuses.get(agent, "waiting")
        css_class, label = _STATUS_CSS.get(status, _STATUS_CSS["waiting"])

        cards_html += (
            f'<div class="agent-card {css_class}">'
            f'<div class="agent-name">{agent}</div>'
            f'<div class="agent-status">{label}</div>'
            f'</div>'
        )

    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)
