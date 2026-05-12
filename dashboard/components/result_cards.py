"""Tarjetas expandibles con los resultados de cada agente."""

import json

import streamlit as st

from dashboard.api.runner import AGENT_ORDER

_AGENT_LABELS = {
    "KIC": "1. KIC — Clasificación de Ingredientes",
    "Regulatorio": "2. Regulatorio — Validación Normativa",
    "Ficha Técnica": "3. Ficha Técnica",
    "Claims": "4. Claims — Declaraciones Regulatorias",
    "Etiqueta": "5. Etiqueta — Texto de Etiqueta",
    "Formatos": "6. Formatos — Formatos de Presentación",
    "Docs Internos": "7. Docs Internos — Documentación Interna",
    "QC": "8. QC — Plan de Control de Calidad",
}


def _summarize(agent_name: str, data: dict) -> str:
    """Extrae un resumen de una línea del output del agente."""
    if not data:
        return "Sin resultados."

    # Intentar extraer un resumen genérico
    ingredients = data.get("fase_2_ingredientes") or data.get("ingredientes")
    if ingredients and isinstance(ingredients, list):
        count = len(ingredients)
        return f"{count} ingrediente{'s' if count != 1 else ''} procesado{'s' if count != 1 else ''}."

    parts = []
    for key in ["resumen", "summary", "resultado", "conclusion", "evaluacion_global"]:
        val = data.get(key)
        if val:
            if isinstance(val, dict):
                parts.append(json.dumps(val, ensure_ascii=False)[:200])
            else:
                parts.append(str(val)[:200])
    return parts[0] if parts else "Resultado disponible."


def render_result_cards(agent_statuses: dict, agent_results: dict):
    """Renderiza tarjetas expandibles con resultados por agente."""
    for agent in AGENT_ORDER:
        status = agent_statuses.get(agent, "waiting")
        label = _AGENT_LABELS.get(agent, agent)

        if status == "completed" and agent in agent_results:
            data = agent_results[agent]
            summary = _summarize(agent, data)

            with st.expander(f"✅ {label}", expanded=False):
                st.markdown(f"**Resumen:** {summary}")

                # Mostrar el markdown si está disponible
                md_key = f"{agent}_md"
                md_content = st.session_state.get(md_key)
                if md_content:
                    st.markdown("---")
                    st.markdown(md_content)

                # Botón de descarga JSON
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                st.download_button(
                    "Descargar JSON",
                    data=json_str,
                    file_name=f"{agent.lower().replace(' ', '_')}.json",
                    mime="application/json",
                    key=f"dl_json_{agent}",
                )

        elif status == "running":
            with st.expander(f"⏳ {label} — En ejecución...", expanded=False):
                st.info("Resultados disponibles al completar el agente.")

        elif status == "error":
            with st.expander(f"❌ {label} — Error", expanded=False):
                st.error("El agente falló durante la ejecución.")
