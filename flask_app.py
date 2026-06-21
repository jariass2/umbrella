"""Umbrella Dashboard — Flask + HTMX."""

from __future__ import annotations

import json
import os
import secrets
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue

from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from markupsafe import Markup

from dashboard.api.runner import AGENT_ORDER, run_pipeline
from dashboard.api.store import (
    init_db, create_run, update_run_status, save_agent_result,
    get_run, list_runs, get_agent_results, load_run_results,
    set_run_output_dir, delete_run,
)
from dashboard.utils.formula_parser import (
    VALID_UNITS, validate_ingredient, rows_to_formula, parse_formula,
    MAX_PRODUCT_NAME_LEN, MAX_INGREDIENTS,
)
from dashboard.utils.ft_pdf_parser import parse_ft_pdf

THIS_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(THIS_DIR / "dashboard" / "templates"),
    static_folder=str(THIS_DIR / "dashboard" / "static"),
)
_secret = os.environ.get("FLASK_SECRET")
if not _secret:
    if os.environ.get("FLASK_ENV") == "production":
        raise RuntimeError("FLASK_SECRET must be set in production")
    _secret = secrets.token_hex(32)
app.secret_key = _secret

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
    "Portfolio": "Portfolio — Gama Recomendada",
}

# DAG wave structure — mirrors pipeline/orchestrator.py execution order
AGENT_WAVES = [
    ["KIC", "Formatos", "Docs Internos", "QC", "Portfolio"],  # Wave 1: parallel, no deps
    ["Regulatorio"],                               # Wave 2: after KIC
    ["Ficha Técnica", "Claims"],                   # Wave 3: parallel, after Regulatorio
    ["Etiqueta"],                                  # Wave 4: after Ficha Técnica + Claims
]

# Pipeline state: run_id -> Queue
_pipeline_queues: dict[int, Queue] = {}
_pipeline_procs: dict[int, int] = {}          # run_id -> subprocess PID
_cancelled_runs: set[int] = set()             # run_ids stopped by user
_running_agents: dict[int, set[str]] = {}     # run_id -> agents currently executing


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


def _agent_headline(agent: str, data: dict) -> str:
    """Línea corta de resumen para el header de cada card (agente concreto)."""
    if not data:
        return ""
    try:
        if agent == "KIC":
            ings = data.get("fase_2_ingredientes") or []
            return f"{len(ings)} ingredientes clasificados" if ings else ""
        if agent == "Regulatorio":
            ings = data.get("ingredientes") or []
            ev = data.get("evaluacion_global") or {}
            viab = ev.get("viabilidad") if isinstance(ev, dict) else None
            parts = []
            if ings: parts.append(f"{len(ings)} ingredientes evaluados")
            if viab: parts.append(f"viabilidad: {viab}")
            return " · ".join(parts)
        if agent == "Ficha Técnica":
            comp = data.get("fase_2_composicion") or []
            aler = data.get("fase_4_alergenos") or []
            parts = []
            if isinstance(comp, list) and comp: parts.append(f"{len(comp)} componentes")
            if isinstance(aler, list): parts.append(f"{len(aler)} alérgenos")
            return " · ".join(parts)
        if agent == "Claims":
            a = data.get("parte_a_claims_regulatorios") or {}
            claims_ing = a.get("claims_por_ingrediente") if isinstance(a, dict) else None
            n_claims = len(claims_ing) if isinstance(claims_ing, list) else 0
            sps = data.get("parte_b_selling_points_comerciales") or []
            n_sps = len(sps) if isinstance(sps, list) else 0
            parts = []
            if n_claims: parts.append(f"{n_claims} claims")
            if n_sps: parts.append(f"{n_sps} selling points")
            return " · ".join(parts)
        if agent == "Etiqueta":
            ing_list = data.get("fase_4_lista_ingredientes_completa") or []
            menc = data.get("fase_6_menciones_ausentes_incompletas") or []
            n_ing = len(ing_list) if isinstance(ing_list, list) else 0
            n_menc = len(menc) if isinstance(menc, list) else 0
            parts = []
            if n_ing: parts.append(f"{n_ing} ingredientes en etiqueta")
            if n_menc: parts.append(f"{n_menc} menciones pendientes")
            return " · ".join(parts)
        if agent == "Formatos":
            rec = data.get("fase_4_recomendacion_final") or {}
            opt = rec.get("formato_optimo") if isinstance(rec, dict) else None
            if isinstance(opt, dict):
                f = opt.get("formato") or opt.get("nombre") or opt.get("tipo")
                if f: return f"Formato óptimo: {f}"
            elif isinstance(opt, str):
                return f"Formato óptimo: {opt}"
            return ""
        if agent == "Docs Internos":
            mat = data.get("fase_1_lista_materiales_navision") or []
            alertas = data.get("fase_4_alertas_navision") or []
            parts = []
            if isinstance(mat, list) and mat: parts.append(f"{len(mat)} materiales")
            if isinstance(alertas, list) and alertas: parts.append(f"{len(alertas)} alertas")
            return " · ".join(parts)
        if agent == "QC":
            ensayos = data.get("fase_6_ensayos_analiticos_adicionales") or []
            n = len(ensayos) if isinstance(ensayos, list) else 0
            return f"{n} ensayos QC adicionales" if n else "Plan QC generado"
        if agent == "Portfolio":
            ext = data.get("fase_2_extensiones_linea") or []
            comp = data.get("fase_3_productos_complementarios") or []
            n = (len(ext) if isinstance(ext, list) else 0) + (len(comp) if isinstance(comp, list) else 0)
            return f"{n} productos propuestos" if n else "Portfolio generado"
    except Exception:
        return ""
    return ""


# ── Compact summary renderer (HTML) — replaces verbose MD dump in cards ────
def _esc(v) -> str:
    """Escape a value for safe HTML insertion. Returns '—' for empty values."""
    from markupsafe import escape
    if v is None or v == "" or v == "-":
        return "—"
    return str(escape(v))


def _truncate(s: str, n: int = 140) -> str:
    s = str(s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _render_kic(data: dict) -> str:
    fase1 = data.get("fase_1_clasificacion") or {}
    ings = data.get("fase_2_ingredientes") or []
    val = data.get("fase_4_valoracion_global") or {}
    parts = []

    if isinstance(fase1, dict):
        tipo = fase1.get("tipo_producto")
        obj = fase1.get("objetivo_funcional_principal")
        if tipo or obj:
            kv = []
            if tipo: kv.append(f'<tr><th>Tipo</th><td>{_esc(tipo)}</td></tr>')
            if obj: kv.append(f'<tr><th>Objetivo</th><td>{_esc(_truncate(obj, 220))}</td></tr>')
            parts.append(f'<table class="summary-kv">{"".join(kv)}</table>')

    if isinstance(ings, list) and ings:
        rows = []
        for ing in ings:
            if not isinstance(ing, dict):
                continue
            nombre = ing.get("ingrediente", "—")
            tipo = ing.get("tipologia", "—")
            dosis = ing.get("dosis_formula_mg")
            unidad = ing.get("dosis_formula_unidad") or "mg"
            dosis_str = f"{dosis} {unidad}" if dosis not in (None, "") else "—"
            nrv = ing.get("porcentaje_nrv") or "—"
            biod = ing.get("biodisponibilidad")
            if isinstance(biod, dict):
                biod = biod.get("nivel") or biod.get("valor") or "—"
            biod_str = _truncate(str(biod or "—"), 60)
            rows.append(
                f'<tr><td>{_esc(nombre)}</td><td>{_esc(tipo)}</td>'
                f'<td>{_esc(dosis_str)}</td><td>{_esc(nrv)}</td><td>{_esc(biod_str)}</td></tr>'
            )
        n = len(ings)
        parts.append(
            f'<p class="summary-intro">{n} ingrediente{"s" if n != 1 else ""} clasificado{"s" if n != 1 else ""}.</p>'
            '<table class="summary-table"><thead><tr>'
            '<th>Ingrediente</th><th>Tipología</th><th>Dosis</th>'
            '<th>% NRV</th><th>Biodisponibilidad</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )

    if isinstance(val, dict):
        coh = val.get("coherencia_funcional")
        pot = val.get("potencial_sinergetico")
        if coh or pot:
            inner = ""
            if coh: inner += f'<p><b>Coherencia funcional:</b> {_esc(coh)}</p>'
            if pot: inner += f'<p>{_esc(_truncate(pot, 280))}</p>'
            parts.append(f'<div class="summary-block"><div class="summary-sub">Valoración global</div>{inner}</div>')

    return "".join(parts) or '<p class="summary-empty">Sin clasificación.</p>'


def _render_regulatorio(data: dict) -> str:
    ev = data.get("evaluacion_global") or {}
    viab = ev.get("viabilidad") if isinstance(ev, dict) else None
    resumen = ev.get("resumen") if isinstance(ev, dict) else None
    blocked = ev.get("bloqueantes") if isinstance(ev, dict) else None
    badge_cls = {
        "VIABLE": "badge-ok",
        "VIABLE_CON_MODIFICACIONES": "badge-warn",
        "VIABLE_CON_CONDICIONES": "badge-warn",
        "NO_VIABLE": "badge-err",
    }.get(viab or "", "badge-dim")

    parts = []
    if viab or resumen:
        head = ""
        if viab:
            head = f'<span class="badge {badge_cls}">{_esc(viab)}</span> '
        if resumen:
            head += _esc(_truncate(resumen, 280))
        parts.append(f'<p class="summary-intro">{head}</p>')

    sem_map = {
        "verde": "summary-yes",
        "VERDE": "summary-yes",
        "ámbar": "summary-warn",
        "AMBAR": "summary-warn",
        "amarillo": "summary-warn",
        "rojo": "summary-warn",
        "ROJO": "summary-warn",
    }

    ings = data.get("ingredientes") or []
    rows = []
    if isinstance(ings, list):
        for ing in ings:
            if not isinstance(ing, dict):
                continue
            nombre = ing.get("nombre", "—")
            sem = ing.get("semaforo") or "—"
            sem_cls = sem_map.get(str(sem).lower(), "summary-dim")
            dictamen = _truncate(ing.get("dictamen") or "", 160)
            ec = ing.get("evaluacion_cuantitativa") or {}
            dosis = ec.get("dosis_formula") if isinstance(ec, dict) else None
            rows.append(
                f'<tr><td>{_esc(nombre)}</td>'
                f'<td class="{sem_cls}">{_esc(sem)}</td>'
                f'<td>{_esc(dosis or "—")}</td>'
                f'<td>{_esc(dictamen)}</td></tr>'
            )
    if rows:
        parts.append(
            '<table class="summary-table"><thead><tr>'
            '<th>Ingrediente</th><th>Semáforo</th><th>Dosis</th><th>Dictamen</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )

    if isinstance(blocked, list) and blocked:
        items = "".join(f'<li>{_esc(_truncate(str(b), 200))}</li>' for b in blocked[:6])
        parts.append(f'<div class="summary-block"><div class="summary-sub">Bloqueantes</div><ul>{items}</ul></div>')

    if isinstance(ev, dict):
        mods = ev.get("modificaciones_recomendadas")
        if isinstance(mods, list) and mods:
            items = "".join(f'<li>{_esc(_truncate(str(m), 200))}</li>' for m in mods[:6])
            parts.append(f'<div class="summary-block"><div class="summary-sub">Modificaciones recomendadas</div><ul>{items}</ul></div>')

    return "".join(parts) or '<p class="summary-empty">Sin evaluación.</p>'


def _render_ficha_tecnica(data: dict) -> str:
    ide = data.get("fase_1_identificacion") or {}
    comp = data.get("fase_2_composicion") or {}
    parts = []

    kv_rows = []
    if isinstance(ide, dict):
        for k, label in [
            ("nombre_comercial", "Nombre comercial"),
            ("denominacion_legal", "Denominación legal"),
            ("forma_presentacion", "Forma"),
            ("peso_neto", "Peso neto"),
            ("publico_objetivo", "Público objetivo"),
        ]:
            v = ide.get(k)
            if v:
                kv_rows.append(f'<tr><th>{_esc(label)}</th><td>{_esc(_truncate(str(v), 160))}</td></tr>')
    if kv_rows:
        parts.append(f'<table class="summary-kv">{"".join(kv_rows)}</table>')

    ings_act = comp.get("ingredientes_activos") if isinstance(comp, dict) else None
    if isinstance(ings_act, list) and ings_act:
        rows = []
        for ing in ings_act:
            if not isinstance(ing, dict):
                continue
            cant = ing.get("cantidad_por_dosis") or "—"
            sem = ing.get("semaforo_regulatorio") or "—"
            rows.append(
                f'<tr><td>{_esc(ing.get("nombre_ingrediente", "—"))}</td>'
                f'<td>{_esc(ing.get("forma_quimica") or "—")}</td>'
                f'<td>{_esc(cant)}</td>'
                f'<td>{_esc(ing.get("porcentaje_nrv") or "—")}</td>'
                f'<td>{_esc(sem)}</td></tr>'
            )
        parts.append(
            f'<p class="summary-intro">{len(ings_act)} ingredientes activos.</p>'
            '<table class="summary-table"><thead><tr>'
            '<th>Ingrediente</th><th>Forma química</th><th>Cant./dosis</th>'
            '<th>% NRV</th><th>Semáforo</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )

    lista = comp.get("lista_ingredientes_etiqueta") if isinstance(comp, dict) else None
    if lista:
        parts.append(
            '<div class="summary-block"><div class="summary-sub">Lista de ingredientes (INCI)</div>'
            f'<p class="summary-inci">{_esc(_truncate(str(lista), 600))}</p></div>'
        )

    return "".join(parts) or '<p class="summary-empty">Sin ficha técnica.</p>'


_SIN_CLAIM_MARKERS = (
    "ninguno autorizado", "no autorizado", "sin claim", "n/a", "no aplica",
    "en espera", "pendiente", "on hold",
)
_EN_ESPERA_LABEL = "En espera (botánico)"


def _es_claim_vacio(texto) -> bool:
    """True si el 'claim' indica que NO hay claim autorizado (botánico en espera
    EFSA), en vez de un claim real."""
    if not texto:
        return True
    low = str(texto).lower()
    return any(m in low for m in _SIN_CLAIM_MARKERS)


def _render_claims(data: dict) -> str:
    pa = data.get("parte_a_claims_regulatorios") or {}
    pb_root = data.get("parte_b_selling_points_comerciales") or {}
    parts = []

    if isinstance(pa, dict):
        resumen = pa.get("resumen_ejecutivo")
        compuesto = pa.get("claim_compuesto_sugerido") or {}
        if resumen:
            parts.append(f'<p class="summary-intro">{_esc(_truncate(resumen, 280))}</p>')
        if isinstance(compuesto, dict):
            txt = compuesto.get("texto_sugerido_etiqueta")
            if txt:
                parts.append(
                    '<div class="summary-block"><div class="summary-sub">Claim compuesto sugerido</div>'
                    f'<p>« {_esc(_truncate(txt, 300))} »</p></div>'
                )

    claims_ing = pa.get("claims_por_ingrediente") if isinstance(pa, dict) else []
    rows = []
    if isinstance(claims_ing, list):
        for c in claims_ing:
            if not isinstance(c, dict):
                continue
            ing = c.get("ingrediente", "—")
            claims = c.get("claims") or []
            if isinstance(claims, list) and claims:
                first = claims[0]
                if isinstance(first, dict):
                    claim_text = first.get("texto_claim") or first.get("texto") or first.get("claim") or str(first)
                else:
                    claim_text = str(first)
                if _es_claim_vacio(claim_text):
                    rows.append(f'<tr><td>{_esc(ing)}</td><td class="summary-dim">{_EN_ESPERA_LABEL}</td></tr>')
                else:
                    n_extra = len(claims) - 1
                    more = f' <span class="summary-dim">(+{n_extra})</span>' if n_extra > 0 else ""
                    rows.append(
                        f'<tr><td>{_esc(ing)}</td><td>{_esc(_truncate(claim_text, 160))}{more}</td></tr>'
                    )
            else:
                rows.append(f'<tr><td>{_esc(ing)}</td><td class="summary-dim">{_EN_ESPERA_LABEL}</td></tr>')

    if rows:
        parts.append(
            '<table class="summary-table"><thead><tr>'
            '<th>Ingrediente</th><th>Claim regulatorio principal</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>'
        )

    sps = pb_root.get("selling_points") if isinstance(pb_root, dict) else (pb_root if isinstance(pb_root, list) else [])
    if isinstance(sps, list) and sps:
        items = []
        for sp in sps[:8]:
            if isinstance(sp, dict):
                t = sp.get("titular_corto_packaging") or sp.get("texto") or sp.get("claim") or ""
            else:
                t = str(sp)
            if t:
                items.append(f'<li>{_esc(_truncate(t, 160))}</li>')
        if items:
            parts.append(f'<div class="summary-block"><div class="summary-sub">Selling points</div><ul>{"".join(items)}</ul></div>')

    return "".join(parts) or '<p class="summary-empty">Sin claims.</p>'


def _render_etiqueta(data: dict) -> str:
    parts = []
    fase2 = data.get("fase_2_texto_por_caras") or {}
    cara_p = fase2.get("cara_principal") if isinstance(fase2, dict) else None
    if isinstance(cara_p, dict):
        kv = []
        for k, label in [
            ("nombre_comercial", "Nombre comercial"),
            ("denominacion_venta", "Denominación de venta"),
            ("cantidad_neta", "Cantidad neta"),
        ]:
            v = cara_p.get(k)
            if v:
                kv.append(f'<tr><th>{_esc(label)}</th><td>{_esc(_truncate(str(v), 200))}</td></tr>')
        if kv:
            parts.append(f'<table class="summary-kv">{"".join(kv)}</table>')

    ing_list = data.get("fase_4_lista_ingredientes_completa")
    if ing_list:
        if isinstance(ing_list, list):
            items = []
            for x in ing_list[:30]:
                if isinstance(x, dict):
                    items.append(x.get("ingrediente") or x.get("nombre") or x.get("texto") or "")
                else:
                    items.append(str(x))
            txt = ", ".join(i for i in items if i)
        else:
            txt = str(ing_list)
        if txt:
            parts.append(
                '<div class="summary-block"><div class="summary-sub">Lista de ingredientes</div>'
                f'<p class="summary-inci">{_esc(_truncate(txt, 600))}</p></div>'
            )

    menc = data.get("fase_6_menciones_ausentes_incompletas") or []
    if isinstance(menc, list) and menc:
        rows = []
        for m in menc:
            if not isinstance(m, dict):
                continue
            estado = m.get("estado") or "—"
            est_low = str(estado).lower()
            col = "summary-yes" if est_low in ("ok", "completo") else "summary-warn"
            rows.append(
                f'<tr><td>{_esc(m.get("mencion", "—"))}</td>'
                f'<td class="{col}">{_esc(estado)}</td>'
                f'<td>{_esc(_truncate(m.get("informacion_necesaria") or "", 160))}</td></tr>'
            )
        if rows:
            parts.append(
                '<div class="summary-block"><div class="summary-sub">Menciones pendientes</div>'
                '<table class="summary-table"><thead><tr>'
                '<th>Mención</th><th>Estado</th><th>Información necesaria</th>'
                '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
            )

    return "".join(parts) or '<p class="summary-empty">Sin contenido de etiqueta.</p>'


def _render_formatos(data: dict) -> str:
    parts = []
    f4 = data.get("fase_4_recomendacion_final") or {}
    if isinstance(f4, dict):
        opt = f4.get("formato_optimo") or f4.get("formato_recomendado")
        if isinstance(opt, dict):
            nombre = opt.get("nombre") or opt.get("formato") or "—"
            just = opt.get("justificacion_tecnica") or opt.get("justificacion") or opt.get("razon") or ""
            com = opt.get("justificacion_comercial") or ""
            inner = f'<div class="summary-headline">{_esc(nombre)}</div>'
            if just: inner += f'<p>{_esc(_truncate(just, 280))}</p>'
            if com: inner += f'<p class="summary-dim">{_esc(_truncate(com, 240))}</p>'
            parts.append(
                f'<div class="summary-block"><div class="summary-sub">Formato recomendado</div>{inner}</div>'
            )
        elif isinstance(opt, str) and opt:
            parts.append(f'<div class="summary-headline">{_esc(opt)}</div>')

    f1 = data.get("fase_1_evaluacion_formatos") or {}
    tabla = f1.get("tabla_comparativa_resumen") if isinstance(f1, dict) else (f1 if isinstance(f1, list) else None)
    if isinstance(tabla, list) and tabla:
        rows = []
        for f in tabla:
            if not isinstance(f, dict):
                continue
            score = f.get("puntuacion") or f.get("score") or "—"
            ventajas = f.get("ventajas_clave") or f.get("ventajas") or ""
            desventajas = f.get("desventajas_clave") or f.get("desventajas") or ""
            if isinstance(ventajas, list): ventajas = "; ".join(str(x) for x in ventajas)
            if isinstance(desventajas, list): desventajas = "; ".join(str(x) for x in desventajas)
            rows.append(
                f'<tr><td>{_esc(f.get("formato", "—"))}</td>'
                f'<td>{_esc(score)}</td>'
                f'<td>{_esc(f.get("coste") or "—")}</td>'
                f'<td>{_esc(_truncate(ventajas, 120))}</td>'
                f'<td>{_esc(_truncate(desventajas, 120))}</td></tr>'
            )
        if rows:
            parts.append(
                '<div class="summary-block"><div class="summary-sub">Formatos evaluados</div>'
                '<table class="summary-table"><thead><tr>'
                '<th>Formato</th><th>Score</th><th>Coste</th><th>Ventajas</th><th>Desventajas</th>'
                '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
            )
    return "".join(parts) or '<p class="summary-empty">Sin recomendación de formato.</p>'


def _render_docs_internos(data: dict) -> str:
    mat = data.get("fase_1_lista_materiales_navision") or []
    alertas = data.get("fase_4_alertas_navision") or []
    formula = data.get("fase_2_formula_cuantitativa") or {}
    parts = []

    if isinstance(formula, dict):
        total = formula.get("total_capsula_mg") or formula.get("total_mg")
        if total:
            parts.append(f'<p class="summary-intro">Total por unidad: <b>{_esc(total)} mg</b></p>')

    if isinstance(mat, list) and mat:
        rows = []
        for m in mat:
            if not isinstance(m, dict):
                continue
            est = m.get("estado_material") or "—"
            est_cls = "summary-yes" if str(est).lower() in ("ok", "disponible", "aprobado") else "summary-warn"
            rows.append(
                f'<tr><td>{_esc(m.get("denominacion_navision", "—"))}</td>'
                f'<td><code>{_esc(m.get("codigo_referencia") or "—")}</code></td>'
                f'<td>{_esc(m.get("cantidad_por_unidad_mg") or "—")} mg</td>'
                f'<td class="{est_cls}">{_esc(est)}</td></tr>'
            )
        if rows:
            parts.append(
                f'<div class="summary-block"><div class="summary-sub">Materiales Navision ({len(mat)})</div>'
                '<table class="summary-table"><thead><tr>'
                '<th>Denominación</th><th>Código</th><th>Cant./unidad</th><th>Estado</th>'
                '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
            )

    if isinstance(alertas, list) and alertas:
        rows = []
        for a in alertas:
            if not isinstance(a, dict):
                continue
            pri = a.get("prioridad") or "—"
            pri_cls = "summary-warn" if str(pri).lower() in ("alta", "critica", "high") else "summary-dim"
            rows.append(
                f'<tr><td>{_esc(a.get("material") or "—")}</td>'
                f'<td>{_esc(a.get("estado") or "—")}</td>'
                f'<td>{_esc(_truncate(a.get("accion") or "", 160))}</td>'
                f'<td class="{pri_cls}">{_esc(pri)}</td></tr>'
            )
        if rows:
            parts.append(
                f'<div class="summary-block"><div class="summary-sub">Alertas Navision ({len(alertas)})</div>'
                '<table class="summary-table"><thead><tr>'
                '<th>Material</th><th>Estado</th><th>Acción</th><th>Prioridad</th>'
                '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
            )
    return "".join(parts) or '<p class="summary-empty">Sin documentación interna.</p>'


def _render_qc(data: dict) -> str:
    parts = []
    resumen = data.get("fase_8_resumen_ejecutivo")
    if isinstance(resumen, dict):
        resumen = resumen.get("resumen") or resumen.get("conclusion") or ""
    if isinstance(resumen, str) and resumen:
        parts.append(f'<p class="summary-intro">{_esc(_truncate(resumen, 320))}</p>')

    ensayos = data.get("fase_6_ensayos_analiticos_adicionales")
    cuant = None
    if isinstance(ensayos, dict):
        cuant = ensayos.get("cuantificacion_activos")
    elif isinstance(ensayos, list):
        cuant = ensayos
    if isinstance(cuant, list) and cuant:
        rows = []
        for e in cuant[:12]:
            if not isinstance(e, dict):
                continue
            rows.append(
                f'<tr><td>{_esc(e.get("parametro") or e.get("ensayo") or e.get("nombre") or "—")}</td>'
                f'<td>{_esc(_truncate(e.get("metodo") or "—", 90))}</td>'
                f'<td>{_esc(_truncate(e.get("especificacion") or "—", 80))}</td>'
                f'<td>{_esc(e.get("frecuencia") or "—")}</td></tr>'
            )
        if rows:
            extra = len(cuant) - len(rows)
            more = f' <span class="summary-dim">(+{extra} más)</span>' if extra > 0 else ""
            parts.append(
                f'<div class="summary-block"><div class="summary-sub">Cuantificación de activos ({len(cuant)}){more}</div>'
                '<table class="summary-table"><thead><tr>'
                '<th>Parámetro</th><th>Método</th><th>Especificación</th><th>Frec.</th>'
                '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
            )

    estab = data.get("fase_7_plan_estabilidad") or {}
    if isinstance(estab, dict):
        zona = estab.get("zona_climatica")
        n_lotes = estab.get("numero_lotes")
        vida = estab.get("vida_util_estimada") or {}
        meses = vida.get("objetivo_meses") if isinstance(vida, dict) else None
        alcanz = vida.get("alcanzable") if isinstance(vida, dict) else None
        kv = []
        if meses:
            check = '<span class="summary-yes">✓</span>' if alcanz else ''
            kv.append(f'<tr><th>Vida útil objetivo</th><td>{_esc(meses)} meses {check}</td></tr>')
        if zona: kv.append(f'<tr><th>Zona climática</th><td>{_esc(zona)}</td></tr>')
        if n_lotes: kv.append(f'<tr><th>Nº de lotes</th><td>{_esc(n_lotes)}</td></tr>')
        if kv:
            parts.append(
                '<div class="summary-block"><div class="summary-sub">Plan de estabilidad</div>'
                f'<table class="summary-kv">{"".join(kv)}</table></div>'
            )

    return "".join(parts) or '<p class="summary-empty">Sin plan QC.</p>'


def _render_portfolio(data: dict) -> str:
    parts = []
    pos = data.get("fase_1_posicionamiento") or {}
    if isinstance(pos, dict):
        if pos.get("producto_ancla"):
            parts.append(f'<div class="summary-headline">{_esc(pos["producto_ancla"])}</div>')
        if pos.get("propuesta_valor"):
            parts.append(f'<p class="summary-intro">{_esc(_truncate(str(pos["propuesta_valor"]), 160))}</p>')

    def _tabla(items, titulo, col_rel, key_rel):
        if not isinstance(items, list) or not items:
            return
        rows = []
        for p in items:
            if not isinstance(p, dict):
                continue
            ing = p.get("ingredientes_clave") or []
            ing = "; ".join(str(x) for x in ing) if isinstance(ing, list) else str(ing)
            rows.append(
                f'<tr><td>{_esc(p.get("nombre", "—"))}</td>'
                f'<td>{_esc(_truncate(str(p.get(key_rel, "")), 110))}</td>'
                f'<td>{_esc(p.get("segmento_objetivo") or "—")}</td>'
                f'<td>{_esc(p.get("formato_sugerido") or "—")}</td></tr>'
            )
        parts.append(
            f'<div class="summary-block"><div class="summary-sub">{titulo}</div>'
            '<table class="summary-table"><thead><tr>'
            f'<th>Producto</th><th>{col_rel}</th><th>Segmento</th><th>Formato</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>'
        )

    _tabla(data.get("fase_2_extensiones_linea"), "Extensiones de línea", "Diferencia", "diferencia_vs_ancla")
    _tabla(data.get("fase_3_productos_complementarios"), "Productos complementarios", "Sinergia", "sinergia_con_ancla")

    gama = data.get("fase_4_gama_recomendada") or {}
    if isinstance(gama, dict):
        sec = gama.get("secuencia_lanzamiento") or []
        if isinstance(sec, list) and sec:
            items = "".join(f'<li>{_esc(s)}</li>' for s in sec)
            parts.append(f'<div class="summary-block"><div class="summary-sub">Gama recomendada</div><ul>{items}</ul></div>')

    return "".join(parts) or '<p class="summary-empty">Sin portfolio.</p>'


_SUMMARY_RENDERERS = {
    "KIC": _render_kic,
    "Regulatorio": _render_regulatorio,
    "Ficha Técnica": _render_ficha_tecnica,
    "Claims": _render_claims,
    "Etiqueta": _render_etiqueta,
    "Formatos": _render_formatos,
    "Docs Internos": _render_docs_internos,
    "QC": _render_qc,
    "Portfolio": _render_portfolio,
}


def _render_summary(agent: str, data: dict) -> Markup:
    """Compact card summary HTML built from the agent JSON (not the verbose MD)."""
    if not data or not isinstance(data, dict):
        return Markup('<p class="summary-empty">Sin resultados.</p>')
    fn = _SUMMARY_RENDERERS.get(agent)
    if not fn:
        return Markup(_summarize(agent, data))
    try:
        return Markup(fn(data))
    except Exception as e:
        return Markup(f'<p class="summary-empty">Error al renderizar sumario: {_esc(str(e))}</p>')


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
                        parsed = json.loads(r["output_json"])
                    except json.JSONDecodeError:
                        parsed = {"raw": r["output_json"]}
                    agent_results[agent] = parsed if isinstance(parsed, dict) else {"_raw_list": parsed}
                if r.get("output_md"):
                    md_contents[agent] = r["output_md"]
            elif r["status"] == "error":
                agent_statuses[agent] = "error"

        run_data = get_run(run_id)
        if run_data and run_data["status"] == "running":
            if run_id in _pipeline_queues:
                pipeline_running = True
                # Superponer estado "running" desde memoria (no persiste en DB)
                for agent in _running_agents.get(run_id, set()):
                    if agent_statuses.get(agent) == "waiting":
                        agent_statuses[agent] = "running"
            else:
                # Proceso muerto sin actualizar DB — corregir estado
                update_run_status(run_id, "error")

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

            if event.get("type") == "process":
                _pipeline_procs[run_id] = event["pid"]
                continue

            if "agent" in event:
                agent = event["agent"]
                status = event["status"]
                if status == "running":
                    _running_agents.setdefault(run_id, set()).add(agent)
                elif status == "completed":
                    _running_agents.get(run_id, set()).discard(agent)
                    completed_agents.add(agent)
                    save_agent_result(
                        run_id, agent, "completed",
                        output_json=json.dumps(event.get("data", {}), ensure_ascii=False),
                        output_md=event.get("output_md"),
                        duration_s=event.get("duration_s"),
                    )
                elif status == "error":
                    _running_agents.get(run_id, set()).discard(agent)
                    save_agent_result(run_id, agent, "error")
            elif event.get("pipeline") == "completed":
                break
    finally:
        timer.cancel()

    # Determine final status
    if run_id in _cancelled_runs:
        final = "cancelled"
        _cancelled_runs.discard(run_id)
    elif len(completed_agents) == len(AGENT_ORDER):
        final = "completed"
    else:
        final = "error"
    update_run_status(run_id, final)
    _pipeline_queues.pop(run_id, None)
    _pipeline_procs.pop(run_id, None)
    _running_agents.pop(run_id, None)


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


def _fmt_num(v) -> str:
    """1660.0 -> '1660', 166.666 -> '166.67'. Para pre-rellenar el formulario."""
    try:
        return f"{float(v):.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return ""


@app.route("/parse-formula-pdf", methods=["POST"])
def parse_formula_pdf():
    """Parsea un FT PDF arrastrado y devuelve JSON para pre-rellenar el formulario.

    La dosis que se muestra como 'Dosis' es la de materia prima (interna); la
    dosis de activo va aparte. Ambas viajan al /analyze para la fórmula canónica.
    """
    f = request.files.get("pdf")
    if not f or not f.filename:
        return jsonify({"error": "No se recibió ningún PDF."}), 400
    try:
        data = parse_ft_pdf(f.read())
    except Exception as exc:  # parser robusto, pero el PDF puede no ser del formato
        return jsonify({"error": f"No se pudo leer el PDF: {exc}"}), 400

    ingredients = [{
        "name": ing["name"],
        "dosage": _fmt_num(ing["raw_mg"]),      # materia prima (interna)
        "active": _fmt_num(ing["active_mg"]),   # dosis de activo (pública)
        "active_name": ing.get("active_name", ""),
        "pct": ing.get("pct_active", ""),
        "unit": ing.get("unit", "mg"),
    } for ing in data.get("ingredients", [])]

    return jsonify({
        "product_name": data.get("product_name", ""),
        "ingredients": ingredients,
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    init_db()
    product_name = request.form.get("product_name", "").strip()
    names = request.form.getlist("ing_name")
    dosages = request.form.getlist("ing_dosage")
    units = request.form.getlist("ing_unit")
    actives = request.form.getlist("ing_active")
    active_names = request.form.getlist("ing_active_name")
    pcts = request.form.getlist("ing_pct")

    def _at(lst, i):
        return lst[i] if i < len(lst) else ""

    errors = []
    if not product_name:
        errors.append("Falta el nombre del producto.")
    elif len(product_name) > MAX_PRODUCT_NAME_LEN:
        errors.append(f"Nombre de producto demasiado largo (máx. {MAX_PRODUCT_NAME_LEN}).")

    if len(names) > MAX_INGREDIENTS:
        return (
            f'<div class="error-msg">Demasiados ingredientes ({len(names)} > {MAX_INGREDIENTS}).</div>',
            400,
        )

    valid_ingredients = []
    canonica = []  # alineada con valid_ingredients (mismo orden que la fórmula)
    for i, name in enumerate(names):
        dosage, unit = _at(dosages, i).strip(), _at(units, i)
        if not name.strip():
            continue
        err = validate_ingredient(name, dosage, unit)
        if err:
            errors.append(f"{name[:60]}: {err}")
            continue
        valid_ingredients.append({"name": name.strip(), "dosage": dosage, "unit": unit})
        active_raw = _at(actives, i).strip().replace(",", ".")
        try:
            active_mg = float(active_raw) if active_raw else None
        except ValueError:
            active_mg = None
        canonica.append({
            "name": name.strip(),
            "raw_mg": float(dosage.replace(",", ".")) if unit in ("mg",) else None,
            "active_mg": active_mg,
            "active_name": _at(active_names, i).strip(),
            "pct_active": _at(pcts, i).strip(),
            "unit": unit,
        })

    if errors:
        safe = Markup("<br>").join(errors)
        return f'<div class="error-msg">{safe}</div>', 400

    if not valid_ingredients:
        return '<div class="warning-msg">Añade al menos un ingrediente.</div>', 400

    formula_text = rows_to_formula(product_name, valid_ingredients)
    run_id = create_run(product_name, formula_text)
    output_dir = os.path.join(PROJECT_ROOT, "outputs", f"run_{run_id}")
    set_run_output_dir(run_id, output_dir)

    # Fórmula canónica (dosis de activo del FT PDF) → el composer la usa como
    # autoritativa. Solo se escribe si hay al menos un valor de activo.
    if any(c["active_mg"] is not None for c in canonica):
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "formula_canonica.json"), "w", encoding="utf-8") as fc:
            json.dump({"product_name": product_name, "ingredients": canonica},
                      fc, ensure_ascii=False, indent=2)

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


@app.route("/stop/<int:run_id>", methods=["POST"])
def stop_pipeline(run_id):
    import signal
    pid = _pipeline_procs.get(run_id)
    if pid:
        _cancelled_runs.add(run_id)
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    from flask import make_response
    resp = make_response("", 204)
    resp.headers["HX-Redirect"] = f"/?run_id={run_id}"
    return resp


@app.route("/run/<int:run_id>", methods=["DELETE"])
def delete_run_route(run_id):
    from flask import make_response, request
    import shutil
    if run_id in _pipeline_procs:
        return ("Pipeline en ejecución — detenlo primero", 409)
    run_data = get_run(run_id)
    if run_data and run_data.get("output_dir"):
        try:
            shutil.rmtree(run_data["output_dir"])
        except OSError:
            pass
    delete_run(run_id)
    current = request.args.get("current", type=int)
    if current == run_id:
        resp = make_response("", 204)
        resp.headers["HX-Redirect"] = "/"
        return resp
    return "", 200


@app.route("/pipeline-status/<int:run_id>")
def pipeline_status(run_id):
    ctx = _get_main_context(run_id)
    return render_template("partials/main_content.html", **ctx)


@app.route("/reset-pipeline")
def reset_pipeline():
    """Pipeline en estado 'sin run' (todos los agentes en espera).

    Se invoca desde el cliente al cargar una fórmula nueva (p. ej. arrastrar
    un FT PDF) para que el DAG de agentes no siga mostrando el estado de un
    run anterior ya irrelevante — sin tocar la sidebar, donde la fórmula
    recién cargada vive y el usuario la revisa antes de lanzar.
    """
    return render_template("partials/main_content.html", **_get_main_context(None))


@app.route("/run/<int:run_id>")
def load_run(run_id):
    ctx = _get_main_context(run_id)
    run_data = get_run(run_id)
    product_name = ""
    ingredients = [{"name": "", "dosage": "", "unit": "mg"}]
    if run_data and run_data.get("formula_text"):
        product_name, parsed = parse_formula(run_data["formula_text"])
        if parsed:
            ingredients = parsed
        # La fórmula canónica (dosis de activo del FT PDF) vive en disco
        # separada del `formula_text` (que solo trae materia prima). La
        # mergemos por índice para que el campo "Activo" se rellene al
        # recargar un run desde el historial.
        canonica = _load_canonica(run_data.get("output_dir"))
        if canonica is not None:
            for i, ing in enumerate(ingredients):
                if i < len(canonica):
                    ing["active"] = _fmt_num(canonica[i].get("active_mg"))
                    ing["active_name"] = canonica[i].get("active_name") or ""
                    ing["pct"] = canonica[i].get("pct_active") or ""

    main_html = render_template("partials/main_content.html", **ctx)
    oob_html = render_template(
        "partials/sidebar_oob.html",
        product_name=product_name,
        ingredients=ingredients,
        units=VALID_UNITS,
        pipeline_running=ctx.get("pipeline_running", False),
    )
    # Si la request viene de HTMX (click en el historial), devolver solo el
    # fragmento main + sidebar OOB y avisar a HTMX para que sincronice la URL
    # con pushState (sino refresh o compartir-enlace vuelve al home en blanco).
    # Si la request es directa (URL copiada, refresh, deep-link), NO devolver
    # un fragmento sin <head> — la página quedaría sin stylesheets. En ese
    # caso redirigir a /?run_id=<id> que sí renderiza el index.html completo.
    if request.headers.get("HX-Request"):
        resp = make_response(main_html + oob_html)
        resp.headers["HX-Push-Url"] = f"/run/{run_id}"
        return resp
    return redirect(url_for("index", run_id=run_id))


def _load_canonica(output_dir: str | None) -> list[dict] | None:
    """Lee la lista de ingredientes canónicos del output_dir (si existe).

    Devuelve None si el archivo no está (run antiguo, pre-Fase 7) — en ese
    caso el formulario simplemente no tendrá datos de activo, comportamiento
    aceptable. La lista vacía sí se devuelve (con `[]`) para distinguir de
    "no se pudo leer" (None) y permitir que el caller haga `len(canonica)`.
    """
    if not output_dir:
        return None
    path = os.path.join(output_dir, "formula_canonica.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    ings = data.get("ingredients") if isinstance(data, dict) else None
    return ings if isinstance(ings, list) else []


_FONTS = Path(__file__).resolve().parent / "dashboard" / "static" / "fonts"
_DEJAVU_SANS          = str(_FONTS / "DejaVuSans.ttf")
_DEJAVU_SANS_BOLD     = str(_FONTS / "DejaVuSans-Bold.ttf")
_DEJAVU_SANS_ITALIC   = str(_FONTS / "DejaVuSans-Oblique.ttf")
_DEJAVU_SANS_BOLDITAL = str(_FONTS / "DejaVuSans-BoldOblique.ttf")


@app.route("/download/<int:run_id>")
def download_report(run_id):
    import re, io
    from flask import Response
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, KeepTogether, PageBreak,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    run_data = get_run(run_id)
    if not run_data:
        return "Run not found", 404

    results = load_run_results(run_id)
    raw = get_agent_results(run_id)
    md_contents = {}
    for r in raw:
        if r.get("output_md"):
            md_contents[r["agent_name"]] = r["output_md"]

    product_name = run_data["product_name"] or "Sin nombre"
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── font registration (idempotent) ────────────────────────────────
    # Helvetica is built into ReportLab (PostScript core), no registration needed.
    # DejaVu is kept registered as a fallback for symbol/emoji glyphs that
    # Helvetica's WinAnsi encoding can't render (●○◆✓✗⚠ etc.).
    try:
        pdfmetrics.registerFont(TTFont('DejaVu',    str(_DEJAVU_SANS)))
        pdfmetrics.registerFont(TTFont('DejaVu-B',  str(_DEJAVU_SANS_BOLD)))
        pdfmetrics.registerFont(TTFont('DejaVu-I',  str(_DEJAVU_SANS_ITALIC)))
        pdfmetrics.registerFont(TTFont('DejaVu-BI', str(_DEJAVU_SANS_BOLDITAL)))
        pdfmetrics.registerFontFamily('DejaVu',
            normal='DejaVu', bold='DejaVu-B',
            italic='DejaVu-I', boldItalic='DejaVu-BI')
    except Exception:
        pass  # already registered on a previous request

    # ── colour palette ─────────────────────────────────────────────────
    NAVY      = HexColor('#0A1432')
    BLUE      = HexColor('#2850A0')
    MUTED     = HexColor('#8294B0')
    RULE      = HexColor('#C8D0E0')
    BODY      = HexColor('#282E38')
    BG        = HexColor('#F5F6F8')
    BORDER    = HexColor('#DCDFE6')
    ZEBRA     = HexColor('#EEF1F6')   # filas alternas en tablas de datos
    HEADER_TXT = HexColor('#FFFFFF')  # texto blanco sobre cabecera navy
    CODE_BG   = HexColor('#F8F9FB')   # fondo de bloques de código

    # ── paragraph styles ───────────────────────────────────────────────
    # Body justified (TA_JUSTIFY) for long descriptions; bullets and tables
    # stay left-aligned because justification on narrow widths creates rivers.
    def S(name, **kw):
        kw.setdefault('fontName', 'Helvetica')
        return ParagraphStyle(name, **kw)

    body_s   = S('body',   fontSize=10, leading=15, textColor=BODY,  alignment=TA_JUSTIFY, spaceAfter=3*mm, hyphenationLang='es_ES', hyphenationMinWordLength=6)
    bullet_s = S('bul',    fontSize=10, leading=15, textColor=BODY,  alignment=TA_JUSTIFY, leftIndent=18, bulletIndent=6, firstLineIndent=0, spaceAfter=2*mm, hyphenationLang='es_ES', hyphenationMinWordLength=6)
    # Jerarquía de cabeceras: tamaño decreciente + cambio de color/estilo en cada
    # nivel para que se segreguen visualmente sin necesidad de reglas adicionales.
    #   H1 (sección principal) → navy 18pt bold + page break
    #   H2 (subsección)        → navy 14pt bold + regla fina gris
    #   H3 (ingrediente)       → MUTED 12pt bold (color más suave que H2)
    #   H4 (etiqueta)          → BLUE 10pt italic (diferente estilo, no solo color)
    h1_s     = S('h1',     fontSize=18, leading=23, textColor=NAVY,  fontName='Helvetica-Bold',    spaceAfter=3*mm, spaceBefore=4*mm)
    h2_s     = S('h2',     fontSize=14, leading=18, textColor=NAVY,  fontName='Helvetica-Bold',    spaceAfter=2*mm, spaceBefore=5*mm)
    h3_s     = S('h3',     fontSize=12, leading=15, textColor=MUTED, fontName='Helvetica-Bold',    spaceAfter=1*mm, spaceBefore=3*mm)
    h4_s     = S('h4',     fontSize=10, leading=14, textColor=BLUE,  fontName='Helvetica-Oblique', spaceAfter=1*mm, spaceBefore=2*mm)
    quote_s  = S('quote',  fontSize=10, leading=15, textColor=MUTED, alignment=TA_JUSTIFY, leftIndent=12, fontName='Helvetica-Oblique', spaceAfter=2*mm)
    sec_s    = S('sec',    fontSize=14, leading=19, textColor=NAVY,  fontName='Helvetica-Bold')
    cov_t_s  = S('cov_t',  fontSize=28, leading=34, textColor=NAVY,  fontName='Helvetica-Bold')
    cov_sub_s= S('cov_s',  fontSize=14, leading=19, textColor=BLUE)
    cov_meta_s=S('cov_m',  fontSize=9,  leading=13, textColor=MUTED)
    code_s   = S('code',   fontSize=7.5, leading=11, textColor=HexColor('#374151'), fontName='Courier')
    tbl_hd_s = S('tbl_hd', fontSize=9, leading=12, fontName='Helvetica-Bold', textColor=BODY)
    tbl_bd_s = S('tbl_bd', fontSize=9, leading=12, textColor=BODY, alignment=TA_LEFT)
    # Cabecera de tabla "invertida": blanco sobre fondo navy.
    tbl_hd_inv_s = S('tbl_hd_inv', fontSize=9, leading=12, fontName='Helvetica-Bold', textColor=HEADER_TXT)

    # ── color-emoji → DejaVu-safe coloured glyph ──────────────────────
    # DejaVu Sans doesn't ship colour emoji (🔵🟦🟧🟥✅⚠️…) so we swap them
    # for monochrome glyphs wrapped in inline <font color=…> tags. Applied
    # after HTML-escape so the angle brackets aren't escaped.
    _EMOJI_MAP = [
        ('\U0001F535', '●', '#1E5BC6'),  # 🔵  → ● azul (sinergia fuerte)
        ('\U0001F7E6', '●', '#3B82F6'),  # 🟦  → ● azul claro (sinergia moderada)
        ('⬜',     '○', '#9CA3AF'),  # ⬜  → ○ gris (neutro)
        ('\U0001F7E7', '●', '#F59E0B'),  # 🟧  → ● naranja (antagonismo moderado)
        ('\U0001F7E5', '●', '#DC2626'),  # 🟥  → ● rojo (antagonismo fuerte)
        ('✅',     '✓', '#16A34A'),  # ✅  → ✓ verde
        ('⚠️','⚠', '#D97706'), # ⚠️  → ⚠ ámbar
        ('⚠',     '⚠', '#D97706'),  # ⚠   sin VS-16
        ('❌',     '✗', '#DC2626'),  # ❌  → ✗ rojo
        ('\U0001F536', '◆', '#F59E0B'),  # 🔶  → ◆ naranja
        ('❓',     '?',      '#6B7280'),  # ❓  → ? gris
        ('\U0001F534', '●', '#DC2626'),  # 🔴  → ● rojo (PCC)
    ]

    def _swap_emojis(text: str) -> str:
        # Glyphs wrapped in DejaVu because Helvetica's WinAnsi encoding has
        # no ●○◆✓✗⚠ etc. — DejaVu Sans does.
        for src, glyph, color in _EMOJI_MAP:
            if src in text:
                text = text.replace(
                    src,
                    f'<font name="DejaVu-B" color="{color}">{glyph}</font>',
                )
        return text

    # ── super/subíndices Unicode → <super>/<sub> de ReportLab ─────────
    # Helvetica no tiene glifos para ⁻ ₂ etc. (salen como ■). Los mapeamos a
    # dígitos/símbolos normales dentro de <super>/<sub> (p.ej. cm⁻¹ → cm<super>-1</super>,
    # O₂ → O<sub>2</sub>).
    _SUP = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9',
            '⁺':'+','⁻':'-','⁼':'=','ⁿ':'n','⁽':'(','⁾':')'}
    _SUB = {'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9',
            '₊':'+','₋':'-','₌':'=','₍':'(','₎':')'}
    _SUP_RE = re.compile('[' + ''.join(_SUP) + ']+')
    _SUB_RE = re.compile('[' + ''.join(_SUB) + ']+')

    def _supersub(text: str) -> str:
        text = _SUP_RE.sub(lambda m: '<super>' + ''.join(_SUP[c] for c in m.group()) + '</super>', text)
        text = _SUB_RE.sub(lambda m: '<sub>' + ''.join(_SUB[c] for c in m.group()) + '</sub>', text)
        return text

    # ── inline markdown → ReportLab XML ───────────────────────────────
    def rl(text: str) -> str:
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
        text = re.sub(r'\*\*(.+?)\*\*',     r'<b>\1</b>',         text)
        text = re.sub(r'__(.+?)__',          r'<b>\1</b>',         text)
        text = re.sub(r'\*(.+?)\*',          r'<i>\1</i>',         text)
        text = re.sub(r'_(.+?)_',            r'<i>\1</i>',         text)
        text = re.sub(r'`([^`]+)`',
                      r'<font name="Courier" size="9">\1</font>', text)
        # Strip empty inline tags created by chained substitutions on malformed
        # markdown like '****', '____', or interleaved markers.
        for _ in range(4):
            text = re.sub(r'<(b|i)>\s*</\1>', '', text)
        text = _supersub(text)
        text = _swap_emojis(text)
        return text

    def safe_paragraph(text: str, style):
        """Build a Paragraph; if the XML is malformed, fall back to escaped plain text."""
        try:
            return Paragraph(text, style)
        except Exception:
            plain = re.sub(r'<[^>]+>', '', text)
            plain = plain.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            plain = plain.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return Paragraph(plain, style)

    def code_table(lines_list: list[str]) -> Table:
        capped = lines_list[:80]
        if len(lines_list) > 80:
            capped.append(f'  … ({len(lines_list) - 80} líneas más)')
        safe = '<br/>'.join(
            l[:160].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            for l in capped
        )
        p = Paragraph(f'<font name="Courier" size="7.5">{safe}</font>', code_s)
        t = Table([[p]], colWidths=[CONTENT_W])
        # Look de "caja de código": acento azul a la izquierda, fondo muy
        # claro, sin recuadro completo (más limpio que BOX en informes).
        t.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), CODE_BG),
            ('LINEBEFORE',   (0,0), (0,-1), 0.6, BLUE),
            ('LEFTPADDING',  (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 9),
            ('TOPPADDING',   (0,0), (-1,-1), 7),
            ('BOTTOMPADDING',(0,0), (-1,-1), 7),
        ]))
        return t

    def _styled_table(rows: list, col_widths: list, has_header: bool = True) -> Table:
        """Tabla con estilo de informe profesional: cabecera navy con texto
        blanco, filas de datos con zebra, líneas finas, padding generoso.

        rows: lista de filas; cada fila es lista de Paragraph (o strings).
              Si `has_header`, la primera fila es cabecera.
        col_widths: anchos por columna en mm.
        """
        n_rows = len(rows)
        n_cols = max(len(r) for r in rows) if rows else len(col_widths)

        style = [
            ('VALIGN',       (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING',  (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING',   (0,0), (-1,-1), 5),
            ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ]

        if has_header and n_rows >= 1:
            style.extend([
                ('BACKGROUND', (0,0), (-1,0), NAVY),
            ])

        # Zebra en filas de datos: alterna ZEBRA en filas 1, 3, 5…
        if n_rows > 1:
            data_start = 1 if has_header else 0
            for i in range(data_start, n_rows):
                if (i - data_start) % 2 == 1:
                    style.append(('BACKGROUND', (0,i), (-1,i), ZEBRA))

        # Separador fino entre filas (orden importa: lo pondremos antes de
        # las reglas más prominentes para que estas las sobrescriban).
        style.append(('LINEBELOW', (0,0), (-1,-1), 0.3, RULE))

        # Regla gruesa bajo la cabecera (look "profesional" — separa el
        # bloque de título del bloque de datos).
        if has_header and n_rows > 1:
            style.append(('LINEBELOW', (0,0), (-1,0), 0.8, NAVY))
        # Regla de cierre al final de la tabla.
        if n_rows >= 1:
            style.append(('LINEBELOW', (0,-1), (-1,-1), 0.5, NAVY))

        t = Table(rows, colWidths=col_widths,
                  repeatRows=1 if has_header else 0)
        t.setStyle(TableStyle(style))
        return t

    # ── markdown → Platypus flowables ─────────────────────────────────
    def md_to_flowables(md_text: str, page_break_h1: bool = True) -> list:
        fl: list = []
        in_code = False
        code_buf: list[str] = []
        in_table = False
        table_rows: list[list[str]] = []
        in_toc = False
        toc_items: list[tuple[str, str]] = []

        def flush_toc():
            nonlocal toc_items, in_toc
            if not toc_items:
                in_toc = False
                return
            toc_num_s = S('toc_num', fontSize=10, leading=14,
                          textColor=MUTED, fontName='Helvetica-Bold')
            toc_txt_s = S('toc_txt', fontSize=10, leading=14, textColor=BODY)
            rows = [
                [Paragraph(num, toc_num_s), Paragraph(rl(title), toc_txt_s)]
                for num, title in toc_items
            ]
            t = Table(rows, colWidths=[12 * mm, CONTENT_W - 12 * mm])
            # Zebra + regla fina bajo cada item (no en la última) para que el
            # índice se lea de un vistazo sin perder ligereza visual.
            style = [
                ('VALIGN',       (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING',  (0,0), (-1,-1), 4),
                ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ('TOPPADDING',   (0,0), (-1,-1), 5),
                ('BOTTOMPADDING',(0,0), (-1,-1), 5),
                ('LINEBELOW',    (0,0), (-1,-2), 0.2, RULE),
            ]
            for i in range(len(rows)):
                if i % 2 == 1:
                    style.append(('BACKGROUND', (0,i), (-1,i), ZEBRA))
            t.setStyle(TableStyle(style))
            fl.append(t)
            fl.append(Spacer(1, 4 * mm))
            toc_items, in_toc = [], False

        def flush_code():
            nonlocal code_buf
            if code_buf:
                fl.append(code_table(code_buf))
                fl.append(Spacer(1, 3 * mm))
            code_buf = []

        def flush_table():
            nonlocal table_rows, in_table
            if not table_rows:
                in_table = False
                return
            n_cols = max(len(r) for r in table_rows)

            # Ancho por columna basado en contenido. Dos modos:
            #   * NARROW (body_max < NARROW_BODY_THRESHOLD): los valores son
            #     cortos ("ALTA", "✓", "4.5", "100 mg"). En estos casos el
            #     body marca el ancho real y la cabecera puede envolver si
            #     es larga. Sin esto, columnas como "Punt." o "Coste" reciben
            #     el ancho de su cabecera (17.5mm para 5 chars) aunque su
            #     contenido apenas ocupe 4-5mm, dejando un hueco visual feo.
            #   * NORMAL: la columna lleva descripciones o datos no triviales.
            #     Usamos max(header_needs, body_needs) para que ni la cabecera
            #     ("Biodisponibilidad", "Compatibilidad") ni el body se
            #     trunque.
            # BODY_CAP limita el body ideal: una celda de 80 chars no debe
            # devorar la tabla — se queda en BODY_CAP×CHAR_REG y el texto
            # envuelve en más líneas.
            NARROW_BODY_THRESHOLD = 6
            CHAR_BOLD = 1.5   # mm/char promedio Helvetica-Bold 9pt
            CHAR_REG  = 1.0   # mm/char promedio Helvetica 9pt
            COL_PAD   = 10    # mm totales de padding interno
            BODY_CAP  = 25    # chars: a partir de ahí, el texto envuelve
            MIN_W     = 12    # mm mínimo por columna
            MAX_W     = 50    # mm máximo por columna

            ideal = []
            for ci in range(n_cols):
                header_len = len(table_rows[0][ci]) if (table_rows and ci < len(table_rows[0])) else 0
                body_max = 0
                for row in table_rows[1:]:
                    if ci < len(row):
                        body_max = max(body_max, len(row[ci]))
                h_w = header_len * CHAR_BOLD + COL_PAD
                b_w = min(BODY_CAP, body_max) * CHAR_REG + COL_PAD
                if body_max < NARROW_BODY_THRESHOLD:
                    col_ideal = b_w
                else:
                    col_ideal = max(h_w, b_w)
                ideal.append(min(MAX_W, max(MIN_W, col_ideal)))

            # Escalar proporcionalmente para encajar exactamente en CONTENT_W.
            # Si tras escalar alguna columna cae por debajo de MIN_W, rebalancear
            # tomando el déficit de la columna más grande.
            total = sum(ideal) or 1
            col_widths = [w * (CONTENT_W / total) for w in ideal]
            for i, w in enumerate(col_widths):
                if w < MIN_W:
                    deficit = MIN_W - w
                    col_widths[i] = MIN_W
                    biggest = max((j for j in range(n_cols) if j != i),
                                  key=lambda j: col_widths[j])
                    col_widths[biggest] -= deficit

            rl_rows = []
            for ri, row in enumerate(table_rows):
                # Cabecera: blanco sobre navy. Cuerpo: estilo normal.
                st = tbl_hd_inv_s if ri == 0 else tbl_bd_s
                rl_rows.append([safe_paragraph(rl(c), st) for c in row])
            t = _styled_table(rl_rows, col_widths, has_header=True)
            fl.append(t)
            fl.append(Spacer(1, 4 * mm))
            table_rows, in_table = [], False

        for raw in md_text.split('\n'):
            line = raw.rstrip()
            stripped = line.strip()

            # code fence
            if re.match(r'^\s*```', stripped):
                flush_table()
                if not in_code:
                    in_code, code_buf = True, []
                else:
                    flush_code()
                    in_code = False
                continue
            if in_code:
                code_buf.append(line)
                continue

            # table rows
            if stripped.startswith('|') and stripped.endswith('|'):
                flush_code()
                in_table = True
                if re.match(r'^\|[\s\-|:]+\|$', stripped):
                    continue
                cells = [c.strip() for c in stripped.strip('|').split('|')]
                table_rows.append(cells)
                continue
            if in_table:
                flush_table()

            # headings
            if stripped.startswith('# '):
                flush_code()
                flush_toc()
                if page_break_h1:
                    fl.append(PageBreak())
                fl.append(safe_paragraph(rl(stripped[2:]), h1_s))
                continue
            if stripped.startswith('## '):
                flush_code()
                flush_toc()
                title = stripped[3:]
                # H2 numerado ("## 1. Análisis…", "## 8. Plan…") = sección
                # principal del informe ⇒ arranca en página propia.
                if page_break_h1 and re.match(r'^##\s+\d+\.', stripped):
                    fl.append(PageBreak())
                fl.append(safe_paragraph(rl(title), h2_s))
                fl.append(HRFlowable(width='100%', thickness=0.3, color=RULE, spaceAfter=2))
                if title.strip().lower() == 'índice':
                    in_toc = True
                continue
            if stripped.startswith('#### '):
                flush_code()
                fl.append(safe_paragraph(rl(stripped[5:]), h4_s))
                continue
            if stripped.startswith('### '):
                flush_code()
                fl.append(safe_paragraph(rl(stripped[4:]), h3_s))
                continue

            # blockquote
            if stripped.startswith('> '):
                flush_code()
                flush_toc()
                fl.append(safe_paragraph(rl(stripped[2:]), quote_s))
                continue

            # HR
            if stripped in ('---', '***', '___'):
                flush_code()
                flush_toc()
                fl.append(Spacer(1, 2 * mm))
                fl.append(HRFlowable(width='100%', thickness=0.4, color=RULE))
                fl.append(Spacer(1, 3 * mm))
                continue

            # bullet
            m = re.match(r'^[-*] (.+)', stripped)
            if m:
                flush_code()
                flush_toc()
                # Viñeta en azul corporativo para alinear con el look de informe.
                fl.append(safe_paragraph(
                    f'<font color="#2850A0">•</font> {rl(m.group(1))}',
                    bullet_s,
                ))
                continue

            # numbered list
            m = re.match(r'^(\d+)\. (.+)', stripped)
            if m:
                flush_code()
                if in_toc:
                    item = m.group(2)
                    link_m = re.match(r'^\[(.+?)\]\(#.+?\)$', item)
                    title = link_m.group(1) if link_m else item
                    toc_items.append((m.group(1), title))
                    continue
                # Numeración en azul + negrita para destacar la secuencia.
                fl.append(safe_paragraph(
                    f'<font color="#2850A0"><b>{m.group(1)}.</b></font> {rl(m.group(2))}',
                    bullet_s,
                ))
                continue

            # empty line
            if not stripped:
                flush_code()
                fl.append(Spacer(1, 2 * mm))
                continue

            # regular paragraph (inline markup preserved)
            flush_code()
            flush_toc()
            fl.append(safe_paragraph(rl(stripped), body_s))

        flush_code()
        flush_table()
        flush_toc()
        return fl

    # ── page callbacks (header / footer) ──────────────────────────────
    PW, PH = A4
    SIDE_MARGIN = 15 * mm                       # más estrecho que el 22mm por defecto
    CONTENT_W   = PW - 2 * SIDE_MARGIN          # 180mm en A4 — ancho útil de tablas y textos

    def _first_page(canvas, doc):
        # Portada limpia: sin header ni número de página.
        pass

    def _later_pages(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(SIDE_MARGIN, PH - 14 * mm, 'Umbrella — Análisis Regulatorio')
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(SIDE_MARGIN, PH - 17 * mm, PW - SIDE_MARGIN, PH - 17 * mm)
        canvas.drawCentredString(PW / 2, 12 * mm, f'Página {doc.page}')
        canvas.restoreState()

    # ── assemble document ──────────────────────────────────────────────
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=SIDE_MARGIN, rightMargin=SIDE_MARGIN,
        topMargin=22 * mm, bottomMargin=20 * mm,
    )

    story: list = []

    # Cover
    story.append(Spacer(1, 14 * mm))
    story.append(Paragraph('Informe de Análisis<br/>Regulatorio', cov_t_s))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(product_name, cov_sub_s))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f'Generado el {date_str}', cov_meta_s))
    story.append(Spacer(1, 7 * mm))
    story.append(HRFlowable(width='100%', thickness=0.8, color=NAVY))
    story.append(PageBreak())

    # Prefer the structured master report produced by pipeline.report_composer
    # (matches the v7 reference PDF: portada + índice + fórmula + 8 secciones + anexo).
    # Fall back to per-agent dump for legacy runs that predate the composer or
    # whose output_dir was deleted.
    composed_md = None
    out_dir = run_data.get("output_dir")
    if out_dir:
        composed_path = os.path.join(out_dir, "informe_ejecutivo.md")
        if os.path.exists(composed_path):
            try:
                with open(composed_path, encoding="utf-8") as fh:
                    composed_md = fh.read()
            except Exception:
                composed_md = None

    if composed_md:
        # Strip the composer's H1 portada (we already drew the Flask cover above).
        # The composer emits "# Informe de Producto — X\n\n**Fecha:** ...\n---\n\n## Índice…"
        body = composed_md
        first_hr = body.find("\n---\n")
        if body.startswith("# ") and first_hr != -1:
            body = body[first_hr + len("\n---\n"):].lstrip()
        story.extend(md_to_flowables(body))
    else:
        # Legacy fallback: per-agent dump from DB
        for agent in AGENT_ORDER:
            data = results.get(agent)
            md   = md_contents.get(agent)
            if not data and not md:
                continue

            label = AGENT_LABELS.get(agent, agent)

            section_header = [
                Paragraph(label, sec_s),
                HRFlowable(width='100%', thickness=0.4, color=RULE),
                Spacer(1, 4 * mm),
            ]

            if md:
                content = md_to_flowables(md)
            else:
                json_lines = json.dumps(data, indent=2, ensure_ascii=False).splitlines()
                content = [code_table(json_lines)]

            story.append(KeepTogether(section_header + content[:3]))
            story.extend(content[3:])
            story.append(Spacer(1, 10 * mm))

    doc.build(story, onFirstPage=_first_page, onLaterPages=_later_pages)
    pdf_bytes = buf.getvalue()

    filename = f"{product_name}_informe_regulatorio.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Register template filter for summarize
@app.template_filter("summarize")
def summarize_filter(data):
    return Markup(_summarize("", data))


@app.template_filter("agent_headline")
def agent_headline_filter(data, agent):
    return _agent_headline(agent, data or {})


@app.template_filter("summary_html")
def summary_html_filter(data, agent):
    return _render_summary(agent, data or {})


if __name__ == "__main__":
    init_db()
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("FLASK_PORT", "8503"))
    app.run(debug=debug, port=port)
