"""Result cards matching the wireframe exactly."""

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
    if not data:
        return "Sin resultados."

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
    """Renderiza tarjetas de resultado con estilo wireframe."""
    html = '<div class="results-container">'

    for agent in AGENT_ORDER:
        status = agent_statuses.get(agent, "waiting")
        label = _AGENT_LABELS.get(agent, agent)

        if status == "completed" and agent in agent_results:
            data = agent_results[agent]
            summary = _summarize(agent, data)

            # Badge: OK o WARN si hay avisos
            warnings = data.get("avisos") or data.get("warnings") or data.get("advertencias")
            if warnings and isinstance(warnings, list) and len(warnings) > 0:
                badge = f'<span class="badge badge-warn">{len(warnings)} avisos</span>'
            else:
                badge = '<span class="badge badge-ok">OK</span>'

            html += (
                f'<div class="result-card">'
                f'<div class="result-header">'
                f'<h3>{label}</h3>'
                f'{badge}'
                f'</div>'
                f'<div class="result-body">'
            )

            # Contenido markdown si está disponible
            md_content = st.session_state.get(f"{agent}_md")
            if md_content:
                html += md_content
            else:
                html += summary

            html += '</div></div>'

        elif status == "running":
            html += (
                f'<div class="result-card">'
                f'<div class="result-header" style="opacity:0.5">'
                f'<h3>{label} — En ejecución...</h3>'
                f'</div>'
                f'<div class="result-body collapsed">'
                f'<span class="placeholder-text">Resultados disponibles al completar el agente.</span>'
                f'</div></div>'
            )

        elif status == "error":
            html += (
                f'<div class="result-card">'
                f'<div class="result-header">'
                f'<h3>{label}</h3>'
                f'<span class="badge badge-error">Error</span>'
                f'</div>'
                f'<div class="result-body">'
                f'El agente falló durante la ejecución.'
                f'</div></div>'
            )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Botones de descarga JSON (Streamlit nativo para funcionalidad)
    completed_agents = [
        a for a in AGENT_ORDER
        if agent_statuses.get(a) == "completed" and a in agent_results
    ]
    if completed_agents:
        cols = st.columns(len(completed_agents))
        for i, agent in enumerate(completed_agents):
            data = agent_results[agent]
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            with cols[i]:
                st.download_button(
                    f"{agent} JSON",
                    data=json_str,
                    file_name=f"{agent.lower().replace(' ', '_')}.json",
                    mime="application/json",
                    key=f"dl_json_{agent}",
                    use_container_width=True,
                )
