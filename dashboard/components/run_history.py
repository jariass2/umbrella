"""Run history matching the wireframe exactly."""

import streamlit as st

from dashboard.api.store import list_runs, get_run, load_run_results
from dashboard.api.runner import AGENT_ORDER


def render_run_history():
    """Renderiza el historial de runs en la sidebar con estilo wireframe."""
    st.markdown('<div class="history-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-title">Historial</div>', unsafe_allow_html=True)

    runs = list_runs(limit=15)
    if not runs:
        st.caption("No hay runs anteriores.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    status_icons = {"completed": "✅", "error": "❌", "running": "⏳"}

    for run in runs:
        icon = status_icons.get(run["status"], "⏳")
        # Calcular resumen
        from dashboard.api.store import get_agent_results
        results_raw = get_agent_results(run["id"])
        completed_count = sum(1 for r in results_raw if r["status"] == "completed")

        meta_text = f"{completed_count}/{len(AGENT_ORDER)} agentes"

        if st.button(
            f"{icon} {run['product_name']}",
            key=f"history_{run['id']}",
            use_container_width=True,
        ):
            _load_run(run["id"])

        st.markdown(
            f'<div style="margin-top:-8px;margin-bottom:8px;font-size:11px;color:#999;padding-left:4px;">'
            f'#{run["id"]} — {meta_text}</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.get("selected_run_id"):
        if st.button("Nueva fórmula", use_container_width=True, key="new_formula_btn"):
            st.session_state.selected_run_id = None
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def _load_run(run_id: int):
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
