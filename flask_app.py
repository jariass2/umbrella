"""Umbrella Dashboard — Flask + HTMX."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue

from flask import Flask, render_template, request, redirect, url_for
from markupsafe import Markup

from dashboard.api.runner import AGENT_ORDER, run_pipeline
from dashboard.api.store import (
    init_db, create_run, update_run_status, save_agent_result,
    get_run, list_runs, get_agent_results, load_run_results,
    set_run_output_dir,
)
from dashboard.utils.formula_parser import VALID_UNITS, validate_ingredient, rows_to_formula

THIS_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(THIS_DIR / "dashboard" / "templates"),
    static_folder=str(THIS_DIR / "dashboard" / "static"),
)
app.secret_key = os.environ.get("FLASK_SECRET", "umbrella-dev-key")

PROJECT_ROOT = str(Path(__file__).resolve().parent)

AGENT_LABELS = {
    "KIC": "KIC — Clasificación de Ingredientes",
    "Regulatorio": "Regulatorio — Validación Normativa",
    "Ficha Técnica": "Ficha Técnica",
    "Claims": "Claims — Declaraciones Regulatorias",
    "Etiqueta": "Etiqueta — Texto de Etiqueta",
    "Formatos": "Formatos — Formatos de Presentación",
    "Docs Internos": "Docs Internos — Documentación Interna",
    "QC": "QC — Plan de Control de Calidad",
}

# DAG wave structure — mirrors pipeline/orchestrator.py execution order
AGENT_WAVES = [
    ["KIC", "Formatos", "Docs Internos", "QC"],  # Wave 1: parallel, no deps
    ["Regulatorio"],                               # Wave 2: after KIC
    ["Ficha Técnica", "Claims"],                   # Wave 3: parallel, after Regulatorio
    ["Etiqueta"],                                  # Wave 4: after Ficha Técnica + Claims
]

# Pipeline state: run_id -> Queue
_pipeline_queues: dict[int, Queue] = {}


def _summarize(agent: str, data: dict) -> str:
    if not data:
        return "Sin resultados."
    ingredients = data.get("fase_2_ingredientes") or data.get("ingredientes")
    if ingredients and isinstance(ingredients, list):
        count = len(ingredients)
        return f"{count} ingrediente{'s' if count != 1 else ''} procesado{'s' if count != 1 else ''}."
    for key in ["resumen", "summary", "resultado", "conclusion", "evaluacion_global"]:
        val = data.get(key)
        if val:
            if isinstance(val, dict):
                return json.dumps(val, ensure_ascii=False)[:200]
            return str(val)[:200]
    return "Resultado disponible."


def _build_report_markdown(product_name: str, results: dict, md_contents: dict) -> str:
    lines = [
        "# Informe de Análisis Regulatorio",
        "",
        f"**Producto:** {product_name}",
        f"**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "---",
        "",
    ]
    for agent in AGENT_ORDER:
        data = results.get(agent)
        if not data:
            continue
        lines.append(f"## {AGENT_LABELS.get(agent, agent)}")
        lines.append("")
        md = md_contents.get(agent)
        if md:
            lines.append(md)
        else:
            lines.append("```json")
            lines.append(json.dumps(data, indent=2, ensure_ascii=False))
            lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _get_main_context(run_id: int | None = None, pipeline_running: bool = False) -> dict:
    agent_statuses = {a: "waiting" for a in AGENT_ORDER}
    agent_results = {}
    md_contents = {}
    all_completed = False

    if run_id:
        raw_results = get_agent_results(run_id)
        for r in raw_results:
            agent = r["agent_name"]
            if r["status"] == "completed":
                agent_statuses[agent] = "completed"
                if r["output_json"]:
                    try:
                        agent_results[agent] = json.loads(r["output_json"])
                    except json.JSONDecodeError:
                        agent_results[agent] = {"raw": r["output_json"]}
                if r.get("output_md"):
                    md_contents[agent] = r["output_md"]
            elif r["status"] == "error":
                agent_statuses[agent] = "error"

        run_data = get_run(run_id)
        if run_data and run_data["status"] == "running":
            pipeline_running = True

    all_completed = all(s == "completed" for s in agent_statuses.values())

    return {
        "agent_order": AGENT_ORDER,
        "agent_waves": AGENT_WAVES,
        "agent_statuses": agent_statuses,
        "agent_results": agent_results,
        "md_contents": md_contents,
        "agent_labels": AGENT_LABELS,
        "all_completed": all_completed,
        "pipeline_running": pipeline_running,
        "run_id": run_id,
    }


_PIPELINE_TIMEOUT_S = 3600  # 1 hour hard limit per run


def _run_pipeline_and_save(formula_text: str, output_dir: str, run_id: int):
    queue = Queue()
    _pipeline_queues[run_id] = queue

    def _target():
        run_pipeline(formula_text, output_dir, queue)

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()

    # Consume queue events and save to DB.
    # Use a timeout so we don't block forever if the subprocess crashes hard
    # without emitting {"pipeline": "completed"}.
    completed_agents = set()
    deadline = threading.Event()
    timer = threading.Timer(_PIPELINE_TIMEOUT_S, deadline.set)
    timer.daemon = True
    timer.start()

    try:
        while not deadline.is_set():
            try:
                event = queue.get(timeout=5)
            except Exception:
                # queue.get timed out — check if worker thread is still alive
                if not thread.is_alive() and queue.empty():
                    break
                continue

            if "agent" in event:
                agent = event["agent"]
                status = event["status"]
                if status == "completed":
                    completed_agents.add(agent)
                    save_agent_result(
                        run_id, agent, "completed",
                        output_json=json.dumps(event.get("data", {}), ensure_ascii=False),
                        output_md=event.get("output_md"),
                        duration_s=event.get("duration_s"),
                    )
                elif status == "error":
                    save_agent_result(run_id, agent, "error")
            elif event.get("pipeline") == "completed":
                break
    finally:
        timer.cancel()

    # Determine final status
    final = "completed" if len(completed_agents) == len(AGENT_ORDER) else "error"
    update_run_status(run_id, final)
    _pipeline_queues.pop(run_id, None)


# ── Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    init_db()
    selected_run_id = request.args.get("run_id", type=int)

    runs = list_runs(limit=15)
    for r in runs:
        r["total_agents"] = len(AGENT_ORDER)

    ingredients = [{"name": "", "dosage": "", "unit": "mg"}]

    ctx = _get_main_context(selected_run_id)

    return render_template(
        "index.html",
        product_name="",
        ingredients=ingredients,
        units=VALID_UNITS,
        runs=runs,
        selected_run_id=selected_run_id,
        **ctx,
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    init_db()
    product_name = request.form.get("product_name", "").strip()
    names = request.form.getlist("ing_name")
    dosages = request.form.getlist("ing_dosage")
    units = request.form.getlist("ing_unit")

    errors = []
    valid_ingredients = []
    for name, dosage, unit in zip(names, dosages, units):
        if not name.strip():
            continue
        err = validate_ingredient(name, dosage, unit)
        if err:
            errors.append(f"{name}: {err}")
        else:
            valid_ingredients.append({"name": name, "dosage": dosage, "unit": unit})

    if errors:
        return f'<div class="error-msg">{"<br>".join(errors)}</div>'

    if not valid_ingredients:
        return '<div class="warning-msg">Añade al menos un ingrediente.</div>'

    formula_text = rows_to_formula(product_name, valid_ingredients)
    run_id = create_run(product_name, formula_text)
    output_dir = os.path.join(PROJECT_ROOT, "outputs", f"run_{run_id}")
    set_run_output_dir(run_id, output_dir)

    # Start pipeline in background
    thread = threading.Thread(
        target=_run_pipeline_and_save,
        args=(formula_text, output_dir, run_id),
        daemon=True,
    )
    thread.start()

    from flask import make_response
    resp = make_response("", 204)
    resp.headers["HX-Redirect"] = f"/?run_id={run_id}"
    return resp


@app.route("/pipeline-status/<int:run_id>")
def pipeline_status(run_id):
    ctx = _get_main_context(run_id)
    return render_template("partials/main_content.html", **ctx)


@app.route("/run/<int:run_id>")
def load_run(run_id):
    ctx = _get_main_context(run_id)
    return render_template("partials/main_content.html", **ctx)


_DEJAVU_SANS = str(Path(__file__).resolve().parent / "dashboard" / "static" / "fonts" / "DejaVuSans.ttf")
_DEJAVU_SANS_BOLD = str(Path(__file__).resolve().parent / "dashboard" / "static" / "fonts" / "DejaVuSans-Bold.ttf")


@app.route("/download/<int:run_id>")
def download_report(run_id):
    import markdown as md_lib
    from fpdf import FPDF
    from flask import Response

    run_data = get_run(run_id)
    if not run_data:
        return "Run not found", 404

    results = load_run_results(run_id)
    raw = get_agent_results(run_id)
    md_contents = {}
    for r in raw:
        if r.get("output_md"):
            md_contents[r["agent_name"]] = r["output_md"]

    md_text = _build_report_markdown(run_data["product_name"], results, md_contents)
    body_html = md_lib.markdown(md_text, extensions=["tables", "fenced_code"])

    class PDF(FPDF):
        def header(self):
            self.set_font("DejaVu", "", 8)
            self.set_text_color(156, 163, 175)
            self.cell(0, 8, "Umbrella — Análisis Regulatorio", align="L")
            self.ln(2)

        def footer(self):
            self.set_y(-15)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(156, 163, 175)
            self.cell(0, 10, f"Página {self.page_no()}", align="C")

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.add_font("DejaVu", "", _DEJAVU_SANS)
    pdf.add_font("DejaVu", "B", _DEJAVU_SANS_BOLD)
    pdf.set_margins(left=22, top=20, right=22)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.write_html(body_html)

    pdf_bytes = bytes(pdf.output())
    product = run_data["product_name"] or "informe"
    filename = f"{product}_informe_regulatorio.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


# Register template filter for summarize
@app.template_filter("summarize")
def summarize_filter(data):
    return Markup(_summarize("", data))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8503)
