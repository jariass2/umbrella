"""
Composición del informe final de producto.
Lee los JSON de los 8 agentes y genera un documento markdown profesional.
Sin llamadas a LLM — composición puramente programática.
"""

from __future__ import annotations

import json
import os
from datetime import date

SEMAFORO = {
    "PERMITIDO": "✅",
    "CONDICIONADO": "⚠️",
    "PROBLEMÁTICO": "❌",
    "VERIFICAR": "❓",
    "VIABLE": "✅",
    "VIABLE_CON_CONDICIONES": "⚠️",
    "REQUIERE_REVISION": "🔶",
    "NO_VIABLE": "❌",
}

INTERACCION_EMOJI = {
    "SINERGIA_FUERTE": "🔵",
    "SINERGIA_MODERADA": "🟦",
    "NEUTRO": "⬜",
    "ANTAGONISMO_MODERADO": "🟧",
    "ANTAGONISMO_FUERTE": "🟥",
    "INCOMPATIBILIDAD": "❌",
}

# Precios en USD por millón de tokens (in/out).
# Clave = subcadena que aparece en el model ID (case-insensitive).
# El primer match gana — ordenar del más específico al más genérico.
PRICING_PER_1M: list[tuple[str, float, float]] = [
    ("kimi-k2",           0.14,  0.60),
    ("claude-haiku-4",    0.80,  4.00),
    ("claude-sonnet-4",   3.00, 15.00),
    ("claude-opus-4",    15.00, 75.00),
    ("gpt-4o-mini",       0.15,  0.60),
    ("gpt-4o",            2.50, 10.00),
    ("llama-3.3-70b",     0.12,  0.30),
    ("deepseek-chat",     0.07,  1.10),
    ("gemini-flash",      0.075, 0.30),
]


def _lookup_price(model_id: str) -> tuple[float, float]:
    """Devuelve (precio_in, precio_out) por millón de tokens. (0, 0) si desconocido."""
    if not model_id:
        return (0.0, 0.0)
    lower = model_id.lower()
    for key, p_in, p_out in PRICING_PER_1M:
        if key in lower:
            return (p_in, p_out)
    return (0.0, 0.0)


def _format_cost(usd: float) -> str:
    if usd == 0.0:
        return "—"
    if usd < 0.001:
        return f"${usd * 1000:.4f}m"
    return f"${usd:.4f}"


def _load(filename: str, output_dir: str) -> dict:
    path = os.path.join(output_dir, f"{filename}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _val(v, default="—") -> str:
    if v is None or v == "" or v == []:
        return default
    return str(v)


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    """Genera una tabla markdown."""
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        lines.append("| " + " | ".join(_val(c) for c in row) + " |")
    return lines


def _section(title: str, level: int = 2) -> str:
    return f"\n{'#' * level} {title}\n"


def _fuentes(fuentes: list) -> list[str]:
    if not fuentes:
        return []
    lines = [_section("Fuentes consultadas", 3)]
    for f in fuentes:
        url = f.get("url", "")
        link = f" ([enlace]({url}))" if url else ""
        lines.append(f"[{f.get('id','')}] {f.get('fuente','')}{link} — *{f.get('tipo','')}*")
    return lines


# ── Sección 1: KIC ─────────────────────────────────────────────────────────

def fmt_kic(d: dict) -> list[str]:
    lines = [_section("1. Análisis de Composición de Ingredientes (KIC)")]

    c = d.get("fase_1_clasificacion", {})
    lines += [
        f"**Tipo de producto:** {_val(c.get('tipo_producto'))}  ",
        f"**Objetivo funcional principal:** {_val(c.get('objetivo_funcional_principal'))}  ",
    ]
    obj_sec = c.get("objetivos_funcionales_secundarios", [])
    if obj_sec:
        lines.append(f"**Objetivos secundarios:** {', '.join(obj_sec)}  ")
    lines.append("")

    # Tabla de ingredientes
    lines.append(_section("Perfil de ingredientes", 3))
    headers = ["Ingrediente", "Tipología", "Dosis", "% NRV", "Biodisponibilidad", "Evaluación dosis"]
    rows = []
    for ing in d.get("fase_2_ingredientes", []):
        bio = ing.get("biodisponibilidad", {})
        dos = ing.get("dosificacion", {})
        rows.append([
            ing.get("ingrediente", ""),
            ing.get("tipologia", ""),
            f"{ing.get('dosis_formula_mg','')} {ing.get('dosis_formula_unidad','')}".strip(),
            f"{ing.get('porcentaje_nrv', '')}%",
            bio.get("nivel", "") if isinstance(bio, dict) else _val(bio),
            dos.get("evaluacion", "") if isinstance(dos, dict) else _val(dos),
        ])
    lines += _table(headers, rows)
    lines.append("")

    # Detalle de función y mecanismo por ingrediente
    for ing in d.get("fase_2_ingredientes", []):
        lines.append(f"**{ing.get('ingrediente','')}**")
        fn = ing.get("funcion_tecnologica_nutricional", {})
        if isinstance(fn, dict):
            lines.append(f"- *Función:* {fn.get('rol_primario','')} {('/ ' + fn.get('rol_secundario','')) if fn.get('rol_secundario') else ''}")
        mec = ing.get("mecanismo_accion", {})
        if isinstance(mec, dict):
            lines.append(f"- *Mecanismo:* {mec.get('descripcion','')} — Evidencia: **{mec.get('nivel_evidencia','')}**")
        bio = ing.get("biodisponibilidad", {})
        if isinstance(bio, dict):
            mejora = "; ".join(bio.get("factores_positivos", bio.get("factores_mejora", [])) or [])
            reduccion = "; ".join(bio.get("factores_negativos", bio.get("factores_reduccion", [])) or [])
            if mejora:
                lines.append(f"- *Absorción (mejora):* {mejora}")
            if reduccion:
                lines.append(f"- *Absorción (reduce):* {reduccion}")
        advertencias = ing.get("advertencias_formulacion", [])
        if advertencias:
            if isinstance(advertencias, dict):
                adv_text = "; ".join(str(v) for v in list(advertencias.values())[:2])
            else:
                adv_text = "; ".join(str(a) for a in advertencias[:2])
            lines.append(f"- *Advertencias de formulación:* {adv_text}")
        lines.append("")

    # Interacciones
    interacciones = d.get("fase_3_interacciones_cruzadas", [])
    if interacciones:
        lines.append(_section("Matriz de interacciones", 3))
        headers = ["Par de ingredientes", "Tipo", "Relevancia", "Descripción"]
        rows = []
        for ix in interacciones:
            par = ix.get("par_ingredientes", "")
            if isinstance(par, list):
                par = " + ".join(par)
            tipo = ix.get("tipo_interaccion", "")
            emoji = INTERACCION_EMOJI.get(tipo, "")
            rows.append([
                par,
                f"{emoji} {tipo}",
                ix.get("relevancia_clinica", ""),
                ix.get("descripcion", "")[:120],
            ])
        lines += _table(headers, rows)
        lines.append("")

    # Valoración global
    vg = d.get("fase_4_valoracion_global", {})
    if vg:
        lines.append(_section("Valoración global de la fórmula", 3))
        lines.append(f"**Coherencia funcional:** {_val(vg.get('coherencia_funcional'))}  ")
        lines.append(f"**Potencial sinérgico:** {_val(vg.get('potencial_sinergetico'))}  ")
        lines.append("")
        for campo, label in [
            ("gaps_funcionales", "Gaps funcionales"),
            ("riesgos_formulacion", "Riesgos de formulación"),
            ("sugerencias_mejora", "Sugerencias de mejora"),
        ]:
            items = vg.get(campo, [])
            if items:
                lines.append(f"**{label}:**")
                for x in items:
                    if isinstance(x, dict):
                        text = x.get("gap", x.get("riesgo", x.get("sugerencia", x.get("detalle", str(x)))))
                        detail = x.get("detalle", x.get("descripcion", ""))
                        accion = x.get("accion_sugerida", "")
                        lines.append(f"- **{text}**" + (f": {detail}" if detail else ""))
                        if accion:
                            lines.append(f"  - *Acción:* {accion}")
                    else:
                        lines.append(f"- {x}")
                lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Sección 2: Regulatorio ─────────────────────────────────────────────────

def fmt_regulatorio(d: dict) -> list[str]:
    lines = [_section("2. Validación Regulatoria")]

    ev = d.get("evaluacion_global", {})
    viab = ev.get("viabilidad", "")
    emoji = SEMAFORO.get(viab, "")
    lines += [
        f"**Viabilidad:** {emoji} {viab}  ",
        f"> {ev.get('resumen', '')}",
        "",
    ]

    bloqueantes = ev.get("bloqueantes", [])
    if bloqueantes:
        lines.append("**Bloqueantes regulatorios:**")
        lines += [f"- {b}" for b in bloqueantes]
        lines.append("")

    modif = ev.get("modificaciones_recomendadas", [])
    if modif:
        lines.append("**Modificaciones recomendadas:**")
        lines += [f"- {m}" for m in modif]
        lines.append("")

    # Tabla por ingrediente
    lines.append(_section("Evaluación por ingrediente", 3))
    headers = ["Ingrediente", "Estado", "Normativa", "Condiciones / Advertencias"]
    rows = []
    for ing in d.get("ingredientes", []):
        sem = ing.get("semaforo", "")
        emoji_sem = SEMAFORO.get(sem, "")
        normativa = ing.get("normativa_aplicable", "")
        if isinstance(normativa, list):
            normativa = "; ".join(normativa[:2])
        cond = ing.get("condiciones", "")
        if isinstance(cond, list):
            cond = "; ".join(cond[:2])
        rows.append([
            ing.get("nombre", ""),
            f"{emoji_sem} {sem}",
            normativa[:80],
            cond[:100] if cond else ing.get("dictamen", "")[:100],
        ])
    lines += _table(headers, rows)
    lines.append("")

    # Advertencias obligatorias
    adv = ev.get("advertencias_obligatorias_producto", [])
    if adv:
        lines.append(_section("Advertencias obligatorias en etiqueta", 3))
        lines += [f"- {a}" for a in adv]
        lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Sección 3: Ficha Técnica ────────────────────────────────────────────────

def fmt_ficha_tecnica(d: dict) -> list[str]:
    lines = [_section("3. Ficha Técnica")]

    id_ = d.get("fase_1_identificacion", {})
    if id_:
        for campo, label in [
            ("denominacion_legal", "Denominación legal"),
            ("nombre_comercial", "Nombre comercial"),
            ("tipo_producto", "Tipo de producto"),
            ("forma_presentacion", "Forma de presentación"),
            ("publico_objetivo", "Público objetivo"),
        ]:
            val = id_.get(campo)
            if val:
                lines.append(f"**{label}:** {val}  ")
        lines.append("")

    # Composición
    comp = d.get("fase_2_composicion", {})
    if comp:
        lines.append(_section("Composición cualitativa y cuantitativa", 3))
        ingredientes = comp.get("ingredientes_activos", comp.get("ingredientes", []))
        if isinstance(ingredientes, list) and ingredientes:
            headers = ["Ingrediente", "Forma química", "Por dosis", "Por 100g", "% NRV", "Estado reg."]
            rows = []
            for ing in ingredientes:
                if isinstance(ing, dict):
                    nombre = ing.get("nombre_ingrediente", ing.get("nombre", ing.get("ingrediente", "")))
                    forma = ing.get("forma_quimica", ing.get("forma", ""))
                    rows.append([
                        nombre,
                        forma,
                        _val(ing.get("cantidad_por_dosis", ing.get("dosis", ""))),
                        _val(ing.get("cantidad_por_100g", "")),
                        _val(ing.get("porcentaje_nrv", ing.get("nrv", ""))),
                        _val(ing.get("semaforo_regulatorio", ing.get("estado", ""))),
                    ])
            if rows:
                lines += _table(headers, rows)
                lines.append("")

    # Información nutricional
    nut = d.get("fase_3_informacion_nutricional", {})
    if nut:
        lines.append(_section("Información nutricional", 3))
        # Try standard list format first
        tabla = nut.get("tabla_nutricional", nut.get("tabla", []))
        # Try nested dict format (seccion_obligatoria + vitaminas_minerales)
        tab_por_dosis = nut.get("tabla_nutricional_por_dosis", {})
        filas_rows = []
        if isinstance(tabla, list) and tabla:
            for fila in tabla:
                if isinstance(fila, dict):
                    filas_rows.append([
                        fila.get("parametro", fila.get("nutriente", fila.get("nombre", ""))),
                        _val(fila.get("cantidad_por_dosis", fila.get("por_dosis", fila.get("valor_por_dosis", "")))),
                        _val(fila.get("pct_vrn_dosis", fila.get("porcentaje_vrd", fila.get("vrd", "")))),
                    ])
        elif isinstance(tab_por_dosis, dict):
            NUTRIENTE_LABELS = {
                "valor_energetico_kj": "Valor energético (kJ)",
                "valor_energetico_kcal": "Valor energético (kcal)",
                "grasas_g": "Grasas (g)", "acidos_grasos_saturados_g": "— de las cuales saturadas (g)",
                "hidratos_de_carbono_g": "Hidratos de carbono (g)", "azucares_g": "— de los cuales azúcares (g)",
                "fibra_g": "Fibra (g)", "proteinas_g": "Proteínas (g)", "sal_g": "Sal (g)",
            }
            # Macronutrients (plain values, no VRN%)
            sec = tab_por_dosis.get("seccion_obligatoria", {})
            if isinstance(sec, dict):
                for k, v in sec.items():
                    if k == "metodo_calculo":
                        continue
                    label = NUTRIENTE_LABELS.get(k, k.replace("_", " ").capitalize())
                    filas_rows.append([label, _val(v), "—"])
            # Vitamins & minerals (dicts with nombre_etiqueta, cantidad_por_dosis, porcentaje_nrv)
            vit = tab_por_dosis.get("vitaminas_minerales", {})
            if isinstance(vit, dict):
                for k, v in vit.items():
                    if isinstance(v, dict):
                        label = v.get("nombre_etiqueta", k)
                        unidad = v.get("unidad", "")
                        label_str = f"{label} ({unidad})" if unidad and unidad not in label else label
                        cant = v.get("cantidad_por_dosis", v.get("por_dosis", ""))
                        eq = v.get("equivalencia_ui", "")
                        cant_str = f"{cant} ({eq})" if eq else cant
                        vrn = v.get("porcentaje_nrv", v.get("pct_vrn", ""))
                        filas_rows.append([label_str, _val(cant_str), _val(vrn)])
        if filas_rows:
            headers = ["Nutriente", "Por dosis", "% VRN*"]
            lines += _table(headers, filas_rows)
            lines.append("*\\* % Valores de Referencia de la Nutrición*")
            lines.append("")

    # Alérgenos
    alerg = d.get("fase_4_alergenos", {})
    if alerg:
        lines.append(_section("Alérgenos", 3))
        presentes = alerg.get("presentes", alerg.get("alergenos_presentes", []))
        trazas = alerg.get("trazas", alerg.get("posibles_trazas", []))
        if presentes:
            lines.append(f"**Contiene:** {', '.join(presentes) if isinstance(presentes, list) else presentes}")
        if trazas:
            lines.append(f"**Puede contener trazas de:** {', '.join(trazas) if isinstance(trazas, list) else trazas}")
        dec = alerg.get("declaracion_etiqueta", alerg.get("declaracion", ""))
        if dec:
            if isinstance(dec, dict):
                dec_text = dec.get("texto_recomendado", dec.get("texto", str(dec)))
                dec_trazas = dec.get("texto_trazas", "")
                lines.append(f"**Declaración:** {dec_text}")
                if dec_trazas:
                    lines.append(f"**Trazas posibles:** {dec_trazas}")
            else:
                lines.append(f"**Declaración:** {dec}")
        lines.append("")

    # Conservación y vida útil
    cons = d.get("fase_6_conservacion_vida_util", {})
    if cons:
        lines.append(_section("Conservación y vida útil", 3))
        for campo, label in [
            ("condiciones_conservacion", "Condiciones de conservación"),
            ("vida_util_estimada", "Vida útil estimada"),
            ("condiciones_transporte", "Condiciones de transporte"),
        ]:
            val = cons.get(campo)
            if val:
                if isinstance(val, dict):
                    meses = val.get("meses", "")
                    justif = val.get("justificacion", val.get("condicion", ""))
                    val_str = f"{meses} meses" if meses else ""
                    if justif:
                        val_str += f" — {justif[:150]}..." if len(str(justif)) > 150 else f" — {justif}"
                else:
                    val_str = str(val)
                lines.append(f"**{label}:** {val_str}  ")
        lines.append("")

    # Modo de empleo y advertencias
    mea = d.get("fase_7_modo_empleo_advertencias", {})
    if mea:
        lines.append(_section("Modo de empleo y advertencias", 3))
        modo = mea.get("modo_empleo", mea.get("posologia", ""))
        if modo:
            if isinstance(modo, dict):
                modo_str = modo.get("dosis_diaria", modo.get("modo_administracion", str(modo)))
                momento = modo.get("momento_ingesta", "")
                poblacion = modo.get("poblacion_objetivo", "")
                lines.append(f"**Modo de empleo:** {modo_str}  ")
                if momento:
                    lines.append(f"**Momento de ingesta:** {momento}  ")
                if poblacion:
                    lines.append(f"**Población objetivo:** {poblacion}  ")
            else:
                lines.append(f"**Modo de empleo:** {modo}  ")
        dosis = mea.get("dosis_maxima", mea.get("dosis_diaria_maxima", ""))
        if dosis:
            lines.append(f"**Dosis máxima:** {dosis}  ")
        advertencias = mea.get("advertencias_obligatorias", mea.get("advertencias", []))
        if advertencias:
            lines.append("**Advertencias obligatorias:**")
            items = advertencias if isinstance(advertencias, list) else [advertencias]
            for a in items:
                if isinstance(a, dict):
                    lines.append(f"- {a.get('texto', str(a))}")
                else:
                    lines.append(f"- {a}")
        lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Sección 4: Claims ───────────────────────────────────────────────────────

def fmt_claims(d: dict) -> list[str]:
    lines = [_section("4. Claims y Diferenciación Comercial")]

    parte_a = d.get("parte_a_claims_regulatorios", d.get("claims_regulatorios", {}))
    # Si es lista en vez de dict, convertir a dict con key "claims_por_ingrediente"
    if isinstance(parte_a, list):
        parte_a = {"claims_por_ingrediente": parte_a}
    if parte_a:
        lines.append(_section("Claims regulatorios autorizados (Reg. UE 432/2012)", 3))
        resumen = parte_a.get("resumen_ejecutivo", "")
        if resumen:
            lines += [f"> {resumen}", ""]

        claim_triple = parte_a.get("claim_compuesto_triple_inmunitario", "")
        if claim_triple:
            if isinstance(claim_triple, dict):
                claim_triple = claim_triple.get("texto_sugerido_etiqueta", claim_triple.get("texto", str(claim_triple)))
            lines += [f"**Claim compuesto recomendado:**", f"> {claim_triple}", ""]

        for ing_claims in parte_a.get("claims_por_ingrediente", []):
            if not isinstance(ing_claims, dict):
                continue
            nombre = ing_claims.get("ingrediente", "")
            claims_list = ing_claims.get("claims", [])
            if not claims_list:
                continue
            lines.append(f"**{nombre}**")
            headers = ["Texto del claim", "Condición de uso", "Ref. EFSA"]
            rows = []
            for c in claims_list:
                if isinstance(c, dict):
                    texto = c.get("texto_traduccion_es", c.get("texto_claim", c.get("texto", c.get("texto_oficial_en", ""))))
                    rows.append([
                        texto[:120],
                        c.get("condicion_uso", c.get("condicion", ""))[:80],
                        c.get("referencia_efsa", c.get("referencia_reglamento", c.get("id_ue", "")))[:60],
                    ])
            if rows:
                lines += _table(headers, rows)
            lines.append("")

    # Selling points
    parte_b = d.get("parte_b_selling_points_comerciales", d.get("selling_points", {}))
    if isinstance(parte_b, list):
        parte_b = {"selling_points": parte_b}
    if parte_b:
        lines.append(_section("Selling points comerciales", 3))
        sps = parte_b.get("selling_points", parte_b) if isinstance(parte_b, dict) else parte_b
        if isinstance(sps, list):
            for sp in sps:
                if isinstance(sp, dict):
                    titulo = sp.get("titular_corto_packaging", sp.get("titulo", sp.get("nombre", "")))
                    desc = sp.get("descripcion_ampliada", sp.get("descripcion", sp.get("mensaje", "")))
                    canal = sp.get("canales_uso", sp.get("canal", sp.get("canales", [])))
                    canal_str = ", ".join(canal) if isinstance(canal, list) else str(canal)
                    lines += [f"**{titulo}**", desc, f"*Canales: {canal_str}*" if canal_str else "", ""]
        elif isinstance(sps, dict):
            for k, v in sps.items():
                if isinstance(v, str):
                    lines.append(f"- **{k}:** {v}")
            lines.append("")

    # Diferenciadores
    dif = d.get("diferenciadores", {})
    if isinstance(dif, dict) and dif:
        lines.append(_section("Diferenciadores clave", 3))
        for campo, label in [
            ("vs_competencia", "vs Competencia"),
            ("innovacion", "Innovación"),
            ("publico_objetivo", "Público objetivo"),
            ("momento_consumo", "Momento de consumo"),
        ]:
            val = dif.get(campo)
            if val:
                if isinstance(val, list):
                    lines.append(f"**{label}:**")
                    lines += [f"- {v}" for v in val]
                else:
                    lines.append(f"**{label}:** {val}")
        lines.append("")

    # Estructura PPT
    ppt = d.get("estructura_ppt", [])
    if isinstance(ppt, list) and ppt:
        lines.append(_section("Estructura de presentación (PPT)", 3))
        for slide in ppt:
            if isinstance(slide, dict):
                num = slide.get("numero", "")
                titulo = slide.get("titulo", "")
                puntos = slide.get("puntos_clave", [])
                lines.append(f"**Slide {num}: {titulo}**")
                lines += [f"- {p}" for p in puntos]
                lines.append("")

    # Advertencias legales
    adv = d.get("parte_e_advertencias_legales", d.get("advertencias_legales", {}))
    if isinstance(adv, list):
        adv = {"claims_prohibidos": adv}
    if adv:
        lines.append(_section("Advertencias legales — qué NO puede afirmarse", 3))
        prohibidos = adv.get("claims_prohibidos", adv.get("prohibiciones", []))
        if isinstance(prohibidos, list):
            lines += [f"- {p}" for p in prohibidos]
        elif isinstance(prohibidos, str):
            lines.append(f"- {prohibidos}")
        lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Sección 5: Etiqueta ─────────────────────────────────────────────────────

def fmt_etiqueta(d: dict) -> list[str]:
    lines = [_section("5. Propuesta de Etiqueta")]

    caras = d.get("fase_2_texto_por_caras", d.get("caras", {}))
    if isinstance(caras, list) and caras:
        # Normalizar lista de caras a dict por nombre de cara
        caras_dict = {}
        for c in caras:
            if isinstance(c, dict):
                cara_name = c.get("cara", "").lower().replace(" ", "_")
                caras_dict[cara_name] = c
        caras = caras_dict
    if isinstance(caras, dict):
        # ── Cara principal ──────────────────────────────────────────
        cp = caras.get("cara_principal", {})
        if cp:
            lines.append(_section("Cara principal", 3))
            denom = cp.get("denominacion_venta", "")
            if denom:
                lines += [f"**Denominación de venta:**", f"> {denom}", ""]
            cantidad = cp.get("cantidad_neta", "")
            if cantidad:
                lines.append(f"**Cantidad neta:** {cantidad}  ")
            claims = cp.get("claims_autorizados", [])
            if claims:
                lines.append("**Claims autorizados:**")
                for c in (claims if isinstance(claims, list) else [claims]):
                    lines.append(f"- {c}")
            notas_c = cp.get("notas_claims", "")
            if notas_c:
                lines += ["", f"*{notas_c}*"]
            lines.append("")

        # ── Cara secundaria ─────────────────────────────────────────
        cs = caras.get("cara_secundaria", {})
        if cs:
            lines.append(_section("Cara secundaria", 3))
            lista_ing = cs.get("lista_ingredientes", "")
            if lista_ing:
                lines += [f"**Lista de ingredientes:**", f"> {lista_ing}", ""]
            alergenos = cs.get("alergenos", "")
            if alergenos:
                lines += [f"**Alérgenos:** {alergenos}  ", ""]
            modo = cs.get("modo_empleo", "")
            dosis = cs.get("dosis_diaria", "")
            poblacion = cs.get("poblacion", "")
            if modo:
                lines.append(f"**Modo de empleo:** {modo}  ")
            if dosis:
                lines.append(f"**Dosis diaria:** {dosis}  ")
            if poblacion:
                lines.append(f"**Población:** {poblacion}  ")
            lines.append("")
            adv_oblig = cs.get("advertencias_obligatorias", [])
            adv_rec = cs.get("advertencias_recomendadas", [])
            if adv_oblig:
                lines.append("**Advertencias obligatorias:**")
                for a in adv_oblig:
                    lines.append(f"- {a.get('texto', a) if isinstance(a, dict) else a}")
            if adv_rec:
                lines.append("**Advertencias recomendadas:**")
                for a in adv_rec:
                    lines.append(f"- {a.get('texto', a) if isinstance(a, dict) else a}")
            bloque = cs.get("bloque_advertencias_texto", "")
            if bloque and not adv_oblig and not adv_rec:
                lines += [f"> {bloque}"]
            lines.append("")

            # Tabla nutricional embebida en cara secundaria
            nut_cara = cs.get("tabla_nutricional", {})
            if isinstance(nut_cara, dict) and nut_cara:
                lines.append(_section("Tabla nutricional (cara secundaria)", 4))
                filas = nut_cara.get("filas", nut_cara.get("tabla", []))
                if isinstance(filas, list) and filas:
                    headers = ["Nutriente", "Por dosis", "% VRN*"]
                    rows = []
                    for fila in filas:
                        if isinstance(fila, dict):
                            nutriente = fila.get("parametro", fila.get("nutriente", fila.get("nombre", "")))
                            unidad = fila.get("unidad", "")
                            nombre_str = f"{nutriente} ({unidad})" if unidad and unidad not in str(nutriente) else nutriente
                            rows.append([
                                nombre_str,
                                _val(fila.get("por_dosis", fila.get("valor_por_dosis", fila.get("cantidad", "")))),
                                _val(fila.get("pct_vrn_dosis", fila.get("porcentaje_vrd", fila.get("vrd", fila.get("porcentaje_nrv", ""))))),
                            ])
                    if rows:
                        lines += _table(headers, rows)
                        lines.append("*\\* % Valores de Referencia de la Dieta*")
                lines.append("")

        # ── Cara lateral / contraetiqueta ───────────────────────────
        cl = caras.get("cara_lateral_contraetiqueta", {})
        if cl:
            lines.append(_section("Cara lateral / contraetiqueta", 3))
            for campo, label in [
                ("operador_responsable", "Operador responsable"),
                ("fabricante", "Fabricante"),
                ("fecha_duracion_minima", "Duración mínima"),
                ("condiciones_conservacion", "Conservación"),
                ("numero_lote", "N.º lote"),
                ("pais_origen", "País de origen"),
                ("notificacion_aesan", "Notificación AESAN"),
            ]:
                val = cl.get(campo, "")
                if val:
                    lines.append(f"**{label}:** {val}  ")
            notas_lat = cl.get("notas_lateral", "")
            if notas_lat:
                lines += ["", f"*{notas_lat}*"]
            lines.append("")

    # Lista de ingredientes
    lista_ing = d.get("fase_4_lista_ingredientes_completa", d.get("lista_ingredientes_completa", ""))
    if lista_ing:
        lines.append(_section("Lista de ingredientes", 3))
        if isinstance(lista_ing, str):
            lines += [f"> {lista_ing}", ""]
        elif isinstance(lista_ing, dict):
            texto = lista_ing.get("texto", lista_ing.get("lista", ""))
            if texto:
                lines += [f"> {texto}", ""]

    # Tabla nutricional
    nut = d.get("fase_3_tabla_nutricional_completa", d.get("tabla_informacion_nutricional", {}))
    if nut:
        lines.append(_section("Tabla de información nutricional", 3))
        dosis_ref = nut.get("dosis_referencia", nut.get("por_dosis", ""))
        if dosis_ref:
            lines.append(f"*Valores por dosis de referencia ({dosis_ref}):*")
        filas = nut.get("filas", nut.get("tabla", []))
        if isinstance(filas, list) and filas:
            headers = ["Nutriente", "Por 100g", "Por dosis", "% VRD*"]
            rows = []
            for fila in filas:
                if isinstance(fila, dict):
                    rows.append([
                        fila.get("nutriente", fila.get("nombre", "")),
                        _val(fila.get("valor_por_100g", fila.get("por_100g", ""))),
                        _val(fila.get("valor_por_dosis", fila.get("por_dosis", ""))),
                        _val(fila.get("porcentaje_vrd", fila.get("vrd", ""))),
                    ])
            if rows:
                lines += _table(headers, rows)
                lines.append("*\\* % Valores de Referencia de la Dieta*")
        lines.append("")

    # Notas técnicas
    notas = d.get("fase_5_notas_tecnicas_diseno", d.get("notas_tecnicas", {}))
    if notas:
        lines.append(_section("Notas técnicas de diseño", 3))
        for campo, label in [
            ("altura_x_minima", "Altura mínima de la 'x'"),
            ("superficie_etiquetado", "Superficie de etiquetado"),
        ]:
            val = notas.get(campo)
            if val:
                lines.append(f"- **{label}:** {val}")
        consideraciones = notas.get("consideraciones_especiales", notas.get("consideraciones", []))
        if consideraciones:
            for c in (consideraciones if isinstance(consideraciones, list) else [consideraciones]):
                lines.append(f"- {c}")
        lines.append("")

    # Menciones pendientes
    pendientes = d.get("fase_6_menciones_ausentes_incompletas", d.get("menciones_ausentes", {}))
    if pendientes:
        if isinstance(pendientes, list):
            lista = pendientes
        else:
            lista = pendientes.get("menciones_pendientes", pendientes.get("pendientes", []))
        if isinstance(lista, list) and lista:
            lines.append(_section("Información pendiente de completar", 3))
            for p in lista:
                if isinstance(p, dict):
                    mencion = p.get("mencion", p.get("campo", ""))
                    estado = p.get("estado", "")
                    info = p.get("informacion_necesaria", p.get("detalle", ""))
                    estado_str = f" _{estado}_" if estado else ""
                    lines.append(f"- **{mencion}**{estado_str}: {info}" if info else f"- **{mencion}**{estado_str}")
                else:
                    lines.append(f"- {p}")
            lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Sección 6: Formatos ─────────────────────────────────────────────────────

def fmt_formatos(d: dict) -> list[str]:
    lines = [_section("6. Formatos e Innovación")]

    # Recomendación primero
    rec = d.get("fase_4_recomendacion_final", {})
    if rec:
        fmt_opt = rec.get("formato_optimo", rec.get("formato_recomendado", ""))
        if isinstance(fmt_opt, dict):
            fmt_opt_nombre = fmt_opt.get("nombre", "")
            fmt_opt_justif = fmt_opt.get("justificacion_tecnica", fmt_opt.get("justificacion_comercial", ""))
            condiciones = fmt_opt.get("condiciones_exito", [])
        else:
            fmt_opt_nombre = str(fmt_opt)
            fmt_opt_justif = rec.get("justificacion", rec.get("justificacion_recomendacion", ""))
            condiciones = []
        lines += [
            f"**Formato recomendado:** {fmt_opt_nombre}  ",
            f"> {fmt_opt_justif[:300]}..." if len(str(fmt_opt_justif)) > 300 else f"> {fmt_opt_justif}",
            "",
        ]
        if condiciones and isinstance(condiciones, list):
            lines.append("**Condiciones de éxito:**")
            lines += [f"- {c}" for c in condiciones]
            lines.append("")
        alt = rec.get("formato_alternativo", "")
        if alt:
            if isinstance(alt, dict):
                alt_nombre = alt.get("nombre", "")
                alt_escenario = alt.get("escenario", alt.get("diferencias_vs_optimo", ""))
                lines.append(f"**Formato alternativo:** {alt_nombre}  ")
                if alt_escenario:
                    lines += [f"> {alt_escenario[:200]}..." if len(str(alt_escenario)) > 200 else f"> {alt_escenario}", ""]
            else:
                lines.append(f"**Formato alternativo:** {alt}  ")
            lines.append("")

    # Tabla comparativa de formatos
    ev = d.get("fase_1_evaluacion_formatos", {})
    tabla_comp = ev.get("tabla_comparativa_resumen", []) if isinstance(ev, dict) else []

    if isinstance(tabla_comp, list) and tabla_comp:
        lines.append(_section("Comparativa de formatos evaluados", 3))
        # Use actual field names from tabla_comparativa_resumen
        sample = tabla_comp[0] if tabla_comp else {}
        extra_keys = [k for k in sample.keys() if k not in ("formato", "puntuacion", "coste")]
        headers = ["Formato", "Punt.", "Coste"] + [k.replace("_", " ").capitalize() for k in extra_keys]
        rows = []
        for fmt in tabla_comp:
            if not isinstance(fmt, dict):
                continue
            row = [
                fmt.get("formato", ""),
                _val(fmt.get("puntuacion", "")),
                fmt.get("coste", fmt.get("coste_relativo", "")),
            ] + [_val(fmt.get(k, "")) for k in extra_keys]
            rows.append(row)
        if rows:
            lines += _table(headers, rows)
            lines.append("")

    # Innovación
    innov = d.get("fase_3_innovacion_ingredientes", {})
    if innov:
        lines.append(_section("Diferenciación e innovación", 3))
        propuesta = innov.get("propuesta_innovacion", innov.get("narrativa_innovacion", ""))
        if propuesta:
            lines += [f"> {propuesta}", ""]
        for campo, label in [
            ("ingredientes_diferenciadores", "Ingredientes diferenciadores"),
            ("formas_quimicas_premium", "Formas químicas premium"),
            ("combinaciones_sinergicas", "Combinaciones sinérgicas"),
        ]:
            items = innov.get(campo, [])
            if isinstance(items, list) and items:
                lines.append(f"**{label}:**")
                lines += [f"- {x}" for x in items]
                lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Sección 7: Docs Internos ────────────────────────────────────────────────

def fmt_docs_internos(d: dict) -> list[str]:
    lines = [_section("7. Documentación Interna de Producción")]

    # Lista de Materiales
    lm = d.get("fase_1_lista_materiales_navision", {})
    materiales = []
    if isinstance(lm, list):
        materiales = lm
    elif isinstance(lm, dict):
        # Prefer explicit 'ingredientes' key, then fallback to first list value
        if isinstance(lm.get("ingredientes"), list):
            materiales = lm["ingredientes"]
        else:
            for v in lm.values():
                if isinstance(v, list):
                    materiales = v
                    break
                elif isinstance(v, dict):
                    materiales.append(v)

    if materiales:
        lines.append(_section("Lista de Materiales (L.M.) NAVISION", 3))
        headers = ["Orden", "Ingrediente / Ref. NAVISION", "Cantidad / ud.", "Cantidad lote (×10.000)", "Estado"]
        rows = []
        for mat in materiales:
            if not isinstance(mat, dict):
                continue
            nombre = mat.get("denominacion_navision", mat.get("ingrediente", mat.get("descripcion_navision", mat.get("denominacion", ""))))
            ref = mat.get("codigo_referencia", mat.get("referencia_navision", ""))
            nombre_str = f"{nombre} ({ref})" if ref else nombre
            cant_ud = mat.get("cantidad_por_unidad_mg", mat.get("cantidad_por_unidad", mat.get("cantidad_ud", "")))
            cant_lote = mat.get("cantidad_lote_con_merma_g", mat.get("cantidad_lote_g", mat.get("cantidad_por_lote", mat.get("cantidad_lote", ""))))
            estado = mat.get("estado_material", mat.get("estado", mat.get("estado_homologacion", "")))
            rows.append([
                _val(mat.get("orden_incorporacion", mat.get("orden", mat.get("numero_linea", "")))),
                nombre_str,
                f"{cant_ud} mg" if cant_ud else "—",
                f"{cant_lote} g" if cant_lote else "—",
                estado,
            ])
        if rows:
            lines += _table(headers, rows)
            lines.append("")

    # Fórmula cuantitativa
    fq = d.get("fase_2_formula_cuantitativa", {})
    if fq:
        lines.append(_section("Fórmula cuantitativa", 3))
        total = fq.get("total_capsula_mg", fq.get("total", ""))
        if total:
            lines.append(f"**Peso total por unidad:** {total} mg  ")
        comp = fq.get("composicion", fq.get("ingredientes", {}))
        if isinstance(comp, dict):
            headers = ["Ingrediente", "mg/ud", "%"]
            rows = []
            for nombre, datos in comp.items():
                if isinstance(datos, dict):
                    rows.append([nombre, _val(datos.get("cantidad_mg",datos.get("mg",""))), _val(datos.get("porcentaje",datos.get("%","")))])
                else:
                    rows.append([nombre, _val(datos), ""])
            if rows:
                lines += _table(headers, rows)
        lines.append("")

    # Proceso de fabricación
    proc = d.get("fase_2b_proceso_fabricacion", {})
    if proc:
        lines.append(_section("Proceso de fabricación", 3))
        pasos = proc.get("pasos", proc.get("proceso", []))
        if isinstance(pasos, list):
            for paso in pasos:
                if isinstance(paso, dict):
                    num = paso.get("paso", paso.get("numero", ""))
                    op = paso.get("operacion", paso.get("nombre", ""))
                    desc = paso.get("descripcion", paso.get("detalle", ""))
                    pcc = paso.get("punto_critico", paso.get("pcc", False))
                    pcc_str = " 🔴 **PCC**" if pcc else ""
                    lines.append(f"**{num}. {op}{pcc_str}**")
                    lines.append(f"{desc}")
                    cond = paso.get("condiciones", {})
                    if isinstance(cond, dict) and cond:
                        cond_str = "; ".join(f"{k}: {v}" for k, v in cond.items())
                        lines.append(f"*Condiciones: {cond_str}*")
                    lines.append("")

    # Mapa de reactividad
    mapa = d.get("fase_3_mapa_reactividad", {})
    if mapa:
        lines.append(_section("Mapa de reactividad por formato", 3))
        formatos_r = mapa if isinstance(mapa, list) else list(mapa.values()) if isinstance(mapa, dict) else []
        for fmt_r in formatos_r:
            if not isinstance(fmt_r, dict):
                continue
            fmt_nombre = fmt_r.get("formato", "")
            caducidad = fmt_r.get("caducidad_estimada", "")
            riesgo = fmt_r.get("riesgo_global", "")
            lines.append(f"**{fmt_nombre}** — Caducidad estimada: {caducidad} | Riesgo global: {riesgo}")
            params = fmt_r.get("parametros", fmt_r.get("factores", []))
            if isinstance(params, list):
                headers = ["Factor", "Riesgo", "Ingredientes afectados", "Medida preventiva"]
                rows = []
                for p in params:
                    if isinstance(p, dict):
                        afect = p.get("ingredientes_afectados", [])
                        rows.append([
                            p.get("parametro", p.get("factor", "")),
                            p.get("nivel_riesgo", p.get("riesgo", "")),
                            ", ".join(afect) if isinstance(afect, list) else str(afect),
                            p.get("medida_preventiva", p.get("accion", ""))[:80],
                        ])
                if rows:
                    lines += _table(headers, rows)
            lines.append("")

    # Alertas NAVISION
    alertas = d.get("fase_4_alertas_navision", {})
    if alertas:
        items = alertas if isinstance(alertas, list) else alertas.get("alertas", list(alertas.values()) if isinstance(alertas, dict) else [])
        if items:
            lines.append(_section("Alertas NAVISION", 3))
            for a in items:
                if isinstance(a, dict):
                    mat_a = a.get("material", a.get("ingrediente", ""))
                    estado_a = a.get("estado", "")
                    accion_a = a.get("accion", a.get("descripcion", ""))
                    prior_a = a.get("prioridad", "")
                    lines.append(f"- **{mat_a}** _{estado_a}_ (prioridad: {prior_a}) — {accion_a}")
                elif isinstance(a, str):
                    lines.append(f"- {a}")
            lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Sección 8: QC ───────────────────────────────────────────────────────────

def fmt_qc(d: dict) -> list[str]:
    lines = [_section("8. Plan de Control de Calidad")]

    # Resumen ejecutivo QC
    resumen = d.get("fase_8_resumen_ejecutivo", "")
    if resumen:
        if isinstance(resumen, dict):
            resumen = resumen.get("texto_resumen", resumen.get("texto", resumen.get("resumen", str(resumen))))
        lines += [f"> {resumen}", ""]

    # Tabla resumen de especificaciones clave
    lines.append(_section("Especificaciones analíticas por lote", 3))
    headers = ["Ensayo", "Parámetro / Objetivo", "Especificación", "Método", "Frecuencia"]

    def _method_str(m) -> str:
        if isinstance(m, dict):
            return m.get("nombre", m.get("tecnica", m.get("equipo", str(m)[:60])))
        return str(m)[:60] if m else "—"

    rows = []

    # FTIR
    f1 = d.get("fase_1_ftir", {})
    if f1:
        mg = f1.get("metodologia_general", {})
        ctrl = f1.get("control_mix_final", {})
        criterio = ctrl.get("criterio_aceptacion", "") if isinstance(ctrl, dict) else ""
        rows.append(["FTIR (Identidad)", f1.get("objetivo", "")[:60],
                     criterio[:80], _method_str(mg), "Cada lote + cada MP"])

    # Granulometría
    f2 = d.get("fase_2_granulometria", {})
    if f2:
        mp = f2.get("metodo_primario", {})
        espec = f2.get("especificaciones_por_ingrediente", {})
        vit_c = espec.get("acido_ascorbico", {}) if isinstance(espec, dict) else {}
        espec_str = f"D50: {vit_c.get('D50_um','')}, D90: {vit_c.get('D90_um','')}" if vit_c else "Ver especificaciones"
        rows.append(["Granulometría", f2.get("objetivo", "")[:60],
                     espec_str, _method_str(mp), "Cada lote de MP"])

    # Densidad
    f3 = d.get("fase_3_densidad", {})
    if f3:
        metodos = f3.get("metodos", {})
        m_ap = metodos.get("densidad_aparente", {}) if isinstance(metodos, dict) else {}
        ic = f3.get("indices_reologia", {})
        carr = ic.get("indice_carr", {}) if isinstance(ic, dict) else {}
        espec_str = f"Índice Carr: {carr.get('rango_especificacion', carr.get('rango_esperado',''))}" if carr else "Ver especificaciones"
        rows.append(["Densidad", f3.get("objetivo", "")[:60],
                     espec_str[:80], _method_str(m_ap), f3.get("frecuencia", "")])

    # pH
    f4 = d.get("fase_4_ph", {})
    if f4:
        rango = f4.get("rango_esperado", {})
        ph_val = rango.get("ph_esperado", "") if isinstance(rango, dict) else str(rango)
        espec = f4.get("especificacion_aceptacion", f"pH {ph_val}")
        rows.append(["pH", f4.get("objetivo", "")[:60],
                     str(espec)[:80], _method_str(f4.get("metodo", {})), f4.get("frecuencia", "")])

    # Aspecto
    f5 = d.get("fase_5_aspecto_organoleptico", {})
    if f5:
        criterios = f5.get("criterios_aceptacion", {})
        capsula = criterios.get("capsula", {}) if isinstance(criterios, dict) else {}
        color = capsula.get("color", "") if isinstance(capsula, dict) else ""
        espec_str = f"Color: {color}" if color else "Inspección visual"
        rows.append(["Aspecto", _val(f5.get("descripcion_producto", ""))[:60],
                     espec_str[:80], _method_str(f5.get("metodo_inspeccion", {})), f5.get("frecuencia", "").replace("Frecuencia: ", "")])

    # Ensayos analíticos adicionales (fase_6 es dict de categorías)
    f6 = d.get("fase_6_ensayos_analiticos_adicionales", {})
    if isinstance(f6, dict):
        for categoria, items in f6.items():
            if isinstance(items, list):
                for ensayo in items:
                    if isinstance(ensayo, dict):
                        rows.append([
                            ensayo.get("parametro", categoria)[:40],
                            ensayo.get("justificacion", "")[:60],
                            ensayo.get("especificacion", ensayo.get("criterio", ""))[:80],
                            ensayo.get("metodo", ensayo.get("referencia_metodologica", ""))[:60],
                            ensayo.get("frecuencia", ""),
                        ])
            elif isinstance(items, dict):
                crit = items.get("criterios_microbiologicos", [])
                if isinstance(crit, list):
                    for c in crit[:3]:
                        if isinstance(c, dict):
                            rows.append([
                                c.get("parametro", "Microbiología")[:40], "",
                                c.get("criterio", c.get("limite", ""))[:80],
                                "Según Reg. (CE) 2073/2005", items.get("frecuencia", ""),
                            ])

    if rows:
        lines += _table(headers, rows)
        lines.append("")

    # Detalles FTIR
    ftir = d.get("fase_1_ftir", {})
    espectros = ftir.get("espectros_referencia", {})
    if espectros:
        lines.append(_section("FTIR — Picos característicos por ingrediente", 3))
        for ing_name, esp_data in (espectros.items() if isinstance(espectros, dict) else []):
            lines.append(f"**{ing_name}**")
            if isinstance(esp_data, dict):
                picos = esp_data.get("picos_principales", esp_data.get("picos", []))
                if isinstance(picos, list):
                    for p in picos:
                        if isinstance(p, dict):
                            lines.append(f"- {p.get('numero_onda', p.get('cm_1',''))} cm⁻¹ — {p.get('asignacion', p.get('descripcion',''))}")
                        else:
                            lines.append(f"- {p}")
                criterio = esp_data.get("criterio_aceptacion", "")
                if criterio:
                    lines.append(f"  *Criterio: {criterio}*")
            lines.append("")

    # Plan de estabilidad
    estab = d.get("fase_7_plan_estabilidad", {})
    if estab:
        lines.append(_section("Plan de estabilidad (ICH Q1A(R2))", 3))
        zona = estab.get("zona_climatica", "")
        lotes = estab.get("numero_lotes", "")
        vida = estab.get("vida_util_estimada", estab.get("vida_util_objetivo", ""))
        if isinstance(vida, dict):
            vida_meses = vida.get("objetivo_meses", vida.get("meses", ""))
            vida_alcanzable = vida.get("alcanzable", "")
            alcanzable_str = " ✅" if vida_alcanzable is True else (" ⚠️" if vida_alcanzable is False else "")
            vida_str = f"{vida_meses} meses{alcanzable_str}"
        else:
            vida_str = str(vida)
        lines += [
            f"**Zona climática:** {zona}  ",
            f"**N.º lotes:** {lotes}  ",
            f"**Vida útil objetivo:** {vida_str}  ",
            "",
        ]
        condiciones = estab.get("condiciones_estudio", [])
        if isinstance(condiciones, list) and condiciones:
            lines.append("**Condiciones de estudio:**")
            for cond in condiciones:
                if isinstance(cond, dict):
                    lines.append(f"- {cond.get('tipo', cond.get('nombre',''))}: {cond.get('temperatura','')} / {cond.get('humedad_relativa', cond.get('humedad',''))} — {cond.get('duracion', cond.get('meses',''))} meses")
                else:
                    lines.append(f"- {cond}")
            lines.append("")

        crono = estab.get("cronograma_estudio", {})
        puntos = crono.get("puntos_tiempo", crono) if isinstance(crono, dict) else crono
        if isinstance(puntos, list) and puntos:
            lines.append("**Cronograma:**")
            headers = ["Tiempo", "Condición", "Parámetros monitorizados"]
            rows = []
            for p in puntos:
                if isinstance(p, dict):
                    params = p.get("parametros_monitorizados", p.get("parametros", []))
                    params_str = ", ".join(params[:4]) if isinstance(params, list) else str(params)
                    rows.append([
                        p.get("tiempo", p.get("punto","")),
                        p.get("condicion", p.get("tipo","")),
                        params_str[:100],
                    ])
            if rows:
                lines += _table(headers, rows)
            lines.append("")

        criterios = estab.get("criterios_fin_vida_util", [])
        if criterios:
            lines.append("**Criterios de fin de vida útil:**")
            for c in (criterios if isinstance(criterios, list) else [criterios]):
                if isinstance(c, dict):
                    criterio = c.get("criterio", c.get("parametro", ""))
                    desc = c.get("descripcion", c.get("detalle", ""))
                    lines.append(f"- **{criterio}**: {desc}" if desc else f"- {criterio}")
                else:
                    lines.append(f"- {c}")
            lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Compositor principal ────────────────────────────────────────────────────

def compose_informe(formula: str, path: str, agent_models: dict | None = None,
                    timings: dict | None = None, total_elapsed: float = 0,
                    output_dir: str | None = None) -> None:
    """
    Lee los JSON de los 8 agentes y genera un informe de producto
    en formato markdown profesional.
    """
    nombre_producto = formula.strip().splitlines()[0]
    hoy = date.today().strftime("%d/%m/%Y")

    # output_dir defaults to the directory containing the report itself
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(path))

    kic = _load("agente_1_kic_v2", output_dir)
    reg = _load("agente_2_regulatorio_v2", output_dir)
    ft  = _load("agente_3_ficha_técnica_v2", output_dir)
    clm = _load("agente_4_claims_v2", output_dir)
    etq = _load("agente_5_etiqueta_v2", output_dir)
    fmt = _load("agente_6_formatos_v2", output_dir)
    doc = _load("agente_7_docs_internos_v2", output_dir)
    qc  = _load("agente_8_qc_v2", output_dir)

    # Mapa prefix → _trazabilidad (para tokens y coste en el Anexo)
    _trazab_map: dict[str, dict] = {
        "AGENT_1_KIC":      kic.get("_trazabilidad", {}),
        "AGENT_2_REG":      reg.get("_trazabilidad", {}),
        "AGENT_3_FT":       ft.get("_trazabilidad", {}),
        "AGENT_4_CLAIMS":   clm.get("_trazabilidad", {}),
        "AGENT_5_ETIQUETA": etq.get("_trazabilidad", {}),
        "AGENT_6_FORMATOS": fmt.get("_trazabilidad", {}),
        "AGENT_7_DOCS":     doc.get("_trazabilidad", {}),
        "AGENT_8_QC":       qc.get("_trazabilidad", {}),
    }

    # ── Portada ──────────────────────────────────────────────────────
    viab = reg.get("evaluacion_global", {}).get("viabilidad", "")
    emoji_v = SEMAFORO.get(viab, "")
    _f4 = fmt.get("fase_4_recomendacion_final", {})
    _fmt_opt = _f4.get("formato_optimo", _f4.get("formato_recomendado", "—"))
    if isinstance(_fmt_opt, dict):
        fmt_rec = _fmt_opt.get("nombre", str(_fmt_opt))
    else:
        fmt_rec = _val(_fmt_opt)

    lines = [
        f"# Informe de Producto — {nombre_producto}",
        "",
        f"**Fecha:** {hoy}  ",
        f"**Viabilidad regulatoria:** {emoji_v} {viab}  ",
        f"**Formato recomendado:** {fmt_rec}  ",
        "",
        "---",
        "",
        "## Índice",
        "",
        "1. [Análisis KIC — Composición de Ingredientes](#1-análisis-de-composición-de-ingredientes-kic)",
        "2. [Validación Regulatoria](#2-validación-regulatoria)",
        "3. [Ficha Técnica](#3-ficha-técnica)",
        "4. [Claims y Diferenciación Comercial](#4-claims-y-diferenciación-comercial)",
        "5. [Propuesta de Etiqueta](#5-propuesta-de-etiqueta)",
        "6. [Formatos e Innovación](#6-formatos-e-innovación)",
        "7. [Documentación Interna de Producción](#7-documentación-interna-de-producción)",
        "8. [Plan de Control de Calidad](#8-plan-de-control-de-calidad)",
        "9. [Anexo — Configuración del Pipeline](#anexo--configuración-del-pipeline)",
        "",
        "---",
        "",
        "## Fórmula analizada",
        "",
        "```",
        formula.strip(),
        "```",
        "",
        "---",
    ]

    # ── Secciones ────────────────────────────────────────────────────
    # Normalise QC: LLM may return a list of phase-dicts instead of a single dict
    if isinstance(qc, list):
        merged: dict = {}
        for item in qc:
            if isinstance(item, dict):
                merged.update(item)
        qc = merged

    for fn, data in [
        (fmt_kic,          kic),
        (fmt_regulatorio,  reg),
        (fmt_ficha_tecnica, ft),
        (fmt_claims,       clm),
        (fmt_etiqueta,     etq),
        (fmt_formatos,     fmt),
        (fmt_docs_internos, doc),
        (fmt_qc,           qc),
    ]:
        if data:
            lines += fn(data)
        lines.append("\n---")

    # ── Anexo: modelos y tiempos de ejecución ────────────────────────
    if agent_models:
        agent_names = {
            "AGENT_1_KIC":      ("KIC", "Agente 1 — KIC (Análisis de Ingredientes)"),
            "AGENT_2_REG":      ("Regulatorio", "Agente 2 — Regulatorio"),
            "AGENT_3_FT":       ("Ficha Técnica", "Agente 3 — Ficha Técnica"),
            "AGENT_4_CLAIMS":   ("Claims", "Agente 4 — Claims y Diferenciación"),
            "AGENT_5_ETIQUETA": ("Etiqueta", "Agente 5 — Etiqueta"),
            "AGENT_6_FORMATOS": ("Formatos", "Agente 6 — Formatos e Innovación"),
            "AGENT_7_DOCS":     ("Docs Internos", "Agente 7 — Documentación Interna"),
            "AGENT_8_QC":       ("QC", "Agente 8 — Plan QC"),
        }
        # Calcular duración total en mm:ss
        total_mm = int(total_elapsed // 60)
        total_ss = int(total_elapsed % 60)

        # Calcular coste total
        total_cost = 0.0
        for prefix in agent_names:
            tr = _trazab_map.get(prefix, {})
            p_in, p_out = _lookup_price(tr.get("model") or (agent_models.get(prefix, None) and agent_models[prefix].model) or "")
            total_cost += (tr.get("input_tokens", 0) / 1_000_000) * p_in
            total_cost += (tr.get("output_tokens", 0) / 1_000_000) * p_out

        lines += [
            "",
            "---",
            "",
            "## Anexo — Configuración del Pipeline",
            "",
            f"**Fecha de ejecución:** {hoy}  ",
            f"**Tiempo total de pipeline:** {total_mm}m {total_ss}s  ",
            f"**Coste estimado total:** {_format_cost(total_cost)}  ",
            "",
            "| Agente | Modelo | Tiempo | Tokens (in / out) | Coste est. | Endpoint |",
            "|---|---|---|---|---|---|",
        ]
        for prefix, cfg in agent_models.items():
            key, name = agent_names.get(prefix, (prefix, prefix))
            t = timings.get(key, {}) if timings else {}
            elapsed = t.get("elapsed", 0)
            if elapsed:
                mm = int(elapsed // 60)
                ss = int(elapsed % 60)
                t_str = f"{mm}m {ss}s"
            else:
                t_str = "—"

            tr = _trazab_map.get(prefix, {})
            in_tok = tr.get("input_tokens", 0)
            out_tok = tr.get("output_tokens", 0)
            if in_tok or out_tok:
                tok_str = f"{in_tok:,} / {out_tok:,}"
            else:
                tok_str = "—"

            p_in, p_out = _lookup_price(tr.get("model") or cfg.model or "")
            cost = (in_tok / 1_000_000) * p_in + (out_tok / 1_000_000) * p_out
            cost_str = _format_cost(cost)

            lines.append(f"| {name} | `{cfg.model}` | {t_str} | {tok_str} | {cost_str} | `{cfg.base_url}` |")

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📋 Informe compuesto guardado en {path}")
