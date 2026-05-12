"""Umbrella Dashboard — Análisis Regulatorio Inteligente."""

import json
import os
import sys
import threading
import time
from pathlib import Path
from queue import Queue, Empty

import streamlit as st

# Asegurar que la raíz del proyecto está en sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard.api.runner import AGENT_ORDER, run_pipeline
from dashboard.api.store import (
    init_db, create_run, update_run_status, save_agent_result,
    get_run, list_runs,
)
from dashboard.components.formula_input import render_formula_input
from dashboard.components.pipeline_strip import render_pipeline_strip
from dashboard.components.result_cards import render_result_cards
from dashboard.components.run_history import render_run_history
from dashboard.utils.formula_parser import rows_to_formula, validate_ingredient

st.set_page_config(
    page_title="Umbrella — Análisis Regulatorio",
    page_icon="🌂",
    layout="wide",
)

init_db()

# ── Estado de sesión ──────────────────────────────────────────────────
_defaults = {
    "pipeline_running": False,
    "agent_statuses": {a: "waiting" for a in AGENT_ORDER},
    "agent_results": {},
    "status_queue": None,
    "current_run_id": None,
}
for key, default in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Layout ────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Umbrella")
    st.caption("Análisis Regulatorio Inteligente")

    product_name, ingredients, analyze_clicked = render_formula_input()

    st.divider()
    render_run_history()

# Título principal
st.markdown("## Pipeline de Análisis")
render_pipeline_strip(st.session_state.agent_statuses)
st.markdown("---")
render_result_cards(st.session_state.agent_statuses, st.session_state.agent_results)

# ── Botón de descarga PDF ─────────────────────────────────────────────
all_completed = all(
    st.session_state.agent_statuses.get(a) == "completed"
    for a in AGENT_ORDER
)
if all_completed and st.session_state.agent_results:
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### ✅ Informe completo generado")
    with col2:
        report_md = _build_report_markdown(product_name, st.session_state.agent_results)
        st.download_button(
            "Descargar Informe (Markdown)",
            data=report_md,
            file_name=f"{product_name or 'informe'}_report.md",
            mime="text/markdown",
            type="primary",
            use_container_width=True,
        )

# ── Iniciar pipeline ──────────────────────────────────────────────────
if analyze_clicked and not st.session_state.pipeline_running:
    # Validar ingredientes
    errors = []
    valid_ingredients = []
    for ing in ingredients:
        if not ing["name"].strip():
            continue
        err = validate_ingredient(ing["name"], ing["dosage"], ing["unit"])
        if err:
            errors.append(f"{ing['name']}: {err}")
        else:
            valid_ingredients.append(ing)

    if errors:
        st.error("Errores en la fórmula:\n" + "\n".join(f"- {e}" for e in errors))
        st.stop()

    if not valid_ingredients:
        st.warning("Añade al menos un ingrediente.")
        st.stop()

    formula_text = rows_to_formula(product_name, valid_ingredients)
    run_id = create_run(product_name, formula_text)
    output_dir = os.path.join(PROJECT_ROOT, "outputs", f"run_{run_id}")
    update_run_status(run_id, "running")

    # Resetear estado
    st.session_state.agent_statuses = {a: "waiting" for a in AGENT_ORDER}
    st.session_state.agent_results = {}
    st.session_state.pipeline_running = True
    st.session_state.current_run_id = run_id

    # Crear queue y arrancar thread
    status_queue: Queue = Queue()
    st.session_state.status_queue = status_queue

    thread = threading.Thread(
        target=run_pipeline,
        args=(formula_text, output_dir, status_queue),
        daemon=True,
    )
    thread.start()

    # Guardar referencia al thread para join
    st.session_state._pipeline_thread = thread

    st.rerun()

# ── Polling de estado ─────────────────────────────────────────────────
if st.session_state.pipeline_running and st.session_state.status_queue:
    queue = st.session_state.status_queue
    updated = False

    while True:
        try:
            event = queue.get_nowait()
        except Empty:
            break

        if "agent" in event:
            agent = event["agent"]
            status = event["status"]
            st.session_state.agent_statuses[agent] = status

            if status == "completed":
                if "data" in event:
                    st.session_state.agent_results[agent] = event["data"]
                if event.get("output_md"):
                    st.session_state[f"{agent}_md"] = event["output_md"]

                # Persistir en SQLite
                run_id = st.session_state.current_run_id
                if run_id:
                    save_agent_result(
                        run_id, agent, "completed",
                        output_json=json.dumps(event.get("data", {}), ensure_ascii=False),
                        output_md=event.get("output_md"),
                        duration_s=event.get("duration_s"),
                    )
                updated = True

            elif status == "error":
                run_id = st.session_state.current_run_id
                if run_id:
                    save_agent_result(run_id, agent, "error")
                updated = True

        elif event.get("pipeline") == "completed":
            st.session_state.pipeline_running = False
            run_id = st.session_state.current_run_id
            if run_id:
                completed_count = sum(
                    1 for s in st.session_state.agent_statuses.values() if s == "completed"
                )
                final_status = "completed" if completed_count == len(AGENT_ORDER) else "error"
                update_run_status(run_id, final_status)
            updated = True

    if st.session_state.pipeline_running:
        time.sleep(2)
        st.rerun()
    elif updated:
        st.rerun()


def _build_report_markdown(product_name: str, results: dict) -> str:
    """Genera un informe consolidado en Markdown a partir de los resultados."""
    from datetime import datetime

    lines = [
        f"# Informe de Análisis Regulatorio",
        f"",
        f"**Producto:** {product_name}",
        f"**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"",
        "---",
        "",
    ]

    agent_labels = {
        "KIC": "KIC — Clasificación de Ingredientes",
        "Regulatorio": "Regulatorio — Validación Normativa",
        "Ficha Técnica": "Ficha Técnica",
        "Claims": "Claims — Declaraciones Regulatorias",
        "Etiqueta": "Etiqueta — Texto de Etiqueta",
        "Formatos": "Formatos — Formatos de Presentación",
        "Docs Internos": "Docs Internos — Documentación Interna",
        "QC": "QC — Plan de Control de Calidad",
    }

    for agent in AGENT_ORDER:
        data = results.get(agent)
        if not data:
            continue

        label = agent_labels.get(agent, agent)
        lines.append(f"## {label}")
        lines.append("")

        # Si hay markdown en session_state, usarlo
        md_content = st.session_state.get(f"{agent}_md")
        if md_content:
            lines.append(md_content)
        else:
            lines.append("```json")
            lines.append(json.dumps(data, indent=2, ensure_ascii=False))
            lines.append("```")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
