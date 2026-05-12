"""Strip horizontal con tarjetas de estado de los 8 agentes."""

import streamlit as st

from dashboard.api.runner import AGENT_ORDER

# Colores por estado
_STATUS_COLORS = {
    "waiting": ("#f0f0f0", "#999999"),
    "running": ("#e8f0f5", "#457b9d"),
    "completed": ("#e6f5f3", "#2a9d8f"),
    "error": ("#fce4e4", "#d32f2f"),
}

_STATUS_LABELS = {
    "waiting": "En espera",
    "running": "Ejecutando...",
    "completed": "Completado",
    "error": "Error",
}


def render_pipeline_strip(agent_statuses: dict[str, str]):
    """Renderiza las 8 tarjetas de estado de agentes en una fila."""
    cols = st.columns(len(AGENT_ORDER))
    for i, agent in enumerate(AGENT_ORDER):
        status = agent_statuses.get(agent, "waiting")
        bg_color, text_color = _STATUS_COLORS.get(status, _STATUS_COLORS["waiting"])
        label = _STATUS_LABELS.get(status, status)

        with cols[i]:
            st.markdown(
                f'<div style="background:{bg_color};border:2px solid {text_color};'
                f'border-radius:8px;padding:12px 6px;text-align:center;">'
                f'<div style="font-weight:600;font-size:12px;color:#333;margin-bottom:4px;">{agent}</div>'
                f'<div style="font-size:10px;color:{text_color};text-transform:uppercase;'
                f'letter-spacing:0.3px;">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
