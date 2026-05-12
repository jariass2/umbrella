"""Historial de runs en la sidebar."""

import streamlit as st

from dashboard.api.store import list_runs, get_run, load_run_results
from dashboard.api.runner import AGENT_ORDER


def render_run_history():
    """Renderiza el historial de runs en la sidebar."""
    st.markdown("### Historial")

    runs = list_runs(limit=15)
    if not runs:
        st.caption("No hay runs anteriores.")
        return

    for run in runs:
        status_icon = "✅" if run["status"] == "completed" else ("❌" if run["status"] == "error" else "⏳")
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(
                f"{status_icon} {run['product_name']}",
                key=f"history_{run['id']}",
                use_container_width=True,
            ):
                _load_run(run["id"])
        with col2:
            st.caption(f"#{run['id']}")

    # Botón para limpiar selección
    if st.session_state.get("selected_run_id"):
        if st.button("Nueva formula", use_container_width=True):
            st.session_state.selected_run_id = None
            st.rerun()


def _load_run(run_id: int):
    """Carga un run del historial en la sesión actual."""
    run = get_run(run_id)
    if not run:
        return

    results = load_run_results(run_id)
    agent_statuses = {}
    agent_results = {}

    for agent in AGENT_ORDER:
        if agent in results:
            agent_statuses[agent] = "completed"
            agent_results[agent] = results[agent]
        else:
            agent_statuses[agent] = "waiting"

    st.session_state.agent_statuses = agent_statuses
    st.session_state.agent_results = agent_results
    st.session_state.selected_run_id = run_id
    st.session_state.pipeline_running = False
    st.rerun()
