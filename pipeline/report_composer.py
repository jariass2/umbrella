"""
Composición del informe final de producto.
Lee los JSON de los 8 agentes y genera un documento markdown profesional.
Sin llamadas a LLM — composición puramente programática.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import OrderedDict
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
    ("mimo-v2.5-pro",     0.435, 0.87),
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
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {}
        if isinstance(data, dict):
            return data
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


def _kv_block(data: dict, fields: list[tuple[str, str]], suffix: str = "  ") -> list[str]:
    """Emit "**label:** value{suffix}" lines for each (key, label) where data[key] is truthy."""
    out: list[str] = []
    for key, label in fields:
        val = data.get(key)
        if val:
            out.append(f"**{label}:** {val}{suffix}")
    return out


def _labeled_list(label: str, items, *, blank_after: bool = True) -> list[str]:
    """Emit '**label:**' + '- item' lines. Accepts list, scalar, or empty."""
    if not items:
        return []
    seq = items if isinstance(items, list) else [items]
    if not seq:
        return []
    out = [f"**{label}:**"] + [f"- {x}" for x in seq]
    if blank_after:
        out.append("")
    return out


def _fuentes(fuentes: list, level: int = 3) -> list[str]:
    if not fuentes:
        return []
    lines = [_section("Fuentes consultadas", level)]
    for f in fuentes:
        url = f.get("url", "")
        link = f" ([enlace]({url}))" if url else ""
        lines.append(f"[{f.get('id','')}] {f.get('fuente','')}{link} — *{f.get('tipo','')}*")
    return lines


def _norm(s) -> str:
    """Normaliza un nombre de ingrediente para cruzar datos entre agentes.

    minúsculas + sin acentos + sin paréntesis + sin sufijo '→ ...' + espacios colapsados.
    """
    if not s:
        return ""
    s = str(s).lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"\s*→.*$", "", s)  # el agente Regulatorio incrusta dosis tras "→"
    return re.sub(r"\s+", " ", s).strip()


def _fmt_pct(v) -> str:
    """Formatea un %NRV/VRN evitando el doble '%%' y los 'no aplica%'."""
    s = _val(v, "")
    if not s or s == "—":
        return "—"
    low = s.lower()
    # 'N/A', 'NA', 'none'… no son porcentajes → guion, no 'N/A%'.
    if low in ("n/a", "na", "n.a.", "none", "null", "no aplica"):
        return "—"
    if "%" in s or "aplica" in low or "establec" in low or "ai:" in low or "vrn" in low:
        return s
    return f"{s}%"


def _spec_val(v) -> str:
    """Renderiza un valor de especificación que puede venir como dict
    {'valor':…, 'metodo':…} en vez de string (bug de datos: salía el dict crudo)."""
    if isinstance(v, dict):
        valor = v.get("valor", v.get("value", v.get("especificacion", "")))
        metodo = v.get("metodo", v.get("método", v.get("method", "")))
        if valor and metodo:
            return f"{valor} *(método: {metodo})*"
        return _val(valor or metodo)
    return _val(v)


# ── Confidencialidad: dosis de ACTIVO (pública) vs dosis de materia prima ────
# Xavier (2026-06-02): "la dosis quantitativa és secreta i no es diu mai".
# La dosis de materia prima (dosis_formula_mg) revela la fórmula → NUNCA en
# bloques cliente. Lo comunicable es el ACTIVO aportado ("En base Claim Actiu").

def _parse_pct_activo(nombre: str):
    """Extrae el % de estandarización/activo del nombre del ingrediente
    (ej. '(30% AKBA)', '<95 % curcuminoides', '(2,5% ...)'). Devuelve float o None.

    PUENTE: aproximación hasta conciliar con la Tabla Cuantitativa (Excel, 7b).
    """
    if not nombre:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", str(nombre))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _fmt_mg(valor, unidad: str = "mg") -> str:
    """'50.0' -> '50 mg'; '1.4' -> '1.4 mg'. Sin ceros sobrantes.

    Decimales adaptativos: las microdosis (B12 ≈ 0,004 mg) no deben colapsar a
    '0' por redondeo a 2 cifras. Amplía precisión hasta que un valor no nulo
    deje de truncarse a cero.
    """
    v = float(valor)
    if v == 0:
        return f"0 {unidad}".strip()
    for dec in (2, 3, 4, 5, 6):
        s = f"{v:.{dec}f}"
        if float(s) != 0:
            break
    s = s.rstrip("0").rstrip(".")
    return f"{s} {unidad}".strip()


def _activo_desde_raw(raw_mg, pct_active) -> float | None:
    """Dosis de activo = materia prima × % activo. Devuelve None si no computa.
    `pct_active` puede venir como '0,1' (coma decimal del FT)."""
    if raw_mg in (None, "") or pct_active in (None, ""):
        return None
    try:
        return float(raw_mg) * float(str(pct_active).replace(",", ".")) / 100.0
    except (TypeError, ValueError):
        return None


def _dosis_activo(ing: dict, canonical: dict | None = None) -> str:
    """Dosis de ACTIVO aportado. Pública. Nunca expone `dosis_formula_mg`.

    Si hay dato canónico (de la ficha de fórmula de Xavier, vía
    `formula_canonica.json`) se usa tal cual (autoritativo, incl. casos con
    sobredosado como la B6). Si no, se estima desde la estandarización del
    nombre (puente). '—' si no se puede.
    """
    if canonical and canonical.get("active_mg") not in (None, ""):
        am = canonical["active_mg"]
        # El FT PDF redondea a 2 decimales, así que una microdosis (B12,
        # 0,1% → 0,004 mg) llega como 0,0. Recupérala desde materia prima × %.
        if not am:
            am = _activo_desde_raw(canonical.get("raw_mg"), canonical.get("pct_active")) or am
        return _fmt_mg(am, canonical.get("unit", "mg"))

    mg = ing.get("dosis_formula_mg")
    pct = _parse_pct_activo(ing.get("ingrediente", ""))
    if mg in (None, "", 0) or pct is None:
        return "—"
    try:
        activo = float(mg) * pct / 100.0
    except (TypeError, ValueError):
        return "—"
    return _fmt_mg(activo, ing.get("dosis_formula_unidad", "") or "mg")


def _load_canonica(output_dir: str | None) -> list[dict]:
    """Lista de ingredientes de `formula_canonica.json` (del FT PDF), o []."""
    if not output_dir:
        return []
    path = os.path.join(output_dir, "formula_canonica.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    ings = data.get("ingredients") if isinstance(data, dict) else None
    return ings if isinstance(ings, list) else []


# Sinónimos bilingües (ES↔EN/químico): la canónica viene del FT PDF en
# inglés/nombre químico y KIC escribe en español. Normalizan al token común.
_ING_SYN = {
    "tocoferol": "tocopherol", "biotina": "biotin", "ascorbico": "ascorbic",
    "hialuronico": "hyaluron", "hialuronato": "hyaluron", "hyaluronate": "hyaluron",
    "remolacha": "beet", "pina": "pineapple", "condroitina": "chondroitin",
    "condroitin": "chondroitin", "colecalciferol": "cholecalciferol",
    "tiamina": "thiamin", "riboflavina": "riboflavin", "riboflavine": "riboflavin",
    "piridoxina": "pyridoxine", "cianocobalamina": "cyanocobalamin",
    "nicotinamida": "nicotinamide", "curcuminoides": "curcuminoid",
    "curcuminoids": "curcuminoid", "glucosamina": "glucosamine",
    "astaxantina": "astaxanthin", "sucralosa": "sucralose",
    "bovino": "bovine", "frutos": "fruits", "rojos": "red",
}

# Ruido común a ambos lados que no discrimina ingredientes.
_ING_STOP = {
    "vit", "vitamina", "vitamin", "extract", "extracto", "powder", "polvo", "cwd",
    "natural", "pure", "microencapsulated", "microencapsulado", "microencapsulada",
    "de", "del", "la", "el", "en", "como", "soluble", "sodico", "sodium", "na",
    "acido", "acid", "oil", "aceite", "algae", "algas", "root", "s", "medium",
    "chain", "triglycerides", "triglyceridos", "cadena", "media", "complex",
    "flavour", "flavor", "sabor", "saborizantes", "deshidratada", "dehydrated",
    "natur", "cell", "d", "l", "bg", "dc", "sulfato", "sulphate", "sulfate",
    "huevo", "cascara", "membrana",
}


def _ing_ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def _ing_ident_key(name: str) -> str | None:
    """Clave de identidad fuerte para vitaminas y minerales (inequívoca entre
    idiomas). Las vitaminas se comprueban ANTES que los minerales para que la
    B5 (Ca D-Pantotenato) no se confunda con el Calcio."""
    s = _ing_ascii(name)
    m = re.search(r"\bb\s*([0-9]{1,2})\b", s)
    if m and ("vit" in s or ("b" + m.group(1)) in s.replace(" ", "")):
        return f"vit:b{int(m.group(1))}"
    if re.search(r"\bvit\.?\s*c\b", s) or "ascorbic" in s:
        return "vit:c"
    if re.search(r"\bd3\b", s) or "cholecalciferol" in s:
        return "vit:d3"
    if re.search(r"\bvit\.?\s*e\b", s) or "tocopherol" in s or "tocoferol" in s:
        return "vit:e"
    if re.search(r"\bvit\.?\s*h\b", s) or "biotin" in s or "biotina" in s:
        return "vit:h"
    if re.search(r"\bk2\b", s) or "mk7" in s.replace("-", "").replace(" ", "") or "mk-7" in s:
        return "vit:k2"
    if "magnes" in s or re.search(r"\bmg\b", s):
        return "min:mg"
    if "zinc" in s or re.search(r"\bzn\b", s):
        return "min:zn"
    if "calci" in s or re.search(r"\bca\b", s):
        return "min:ca"
    return None


def _ing_dist_tokens(name: str) -> set[str]:
    """Tokens distintivos (marca/compuesto) para emparejar el resto de
    ingredientes. Conserva ratios tipo '1:5' (discriminan piña polvo vs aroma)."""
    s = _ing_ascii(name)
    ratios = re.findall(r"\d+:\d+", s)
    s = re.sub(r"[^a-z0-9]", " ", s)
    out = set(ratios)
    for t in s.split():
        if not t or re.fullmatch(r"\d+", t):
            continue
        t = _ING_SYN.get(t, t)
        if t in _ING_STOP or len(t) < 3:
            continue
        out.add(t)
    return out


def _alinear_canonica(kic_ings: list[dict], canonica: list[dict]) -> list[dict | None]:
    """Empareja cada ingrediente de KIC con su fila canónica (FT PDF) por
    IDENTIDAD, no por índice: KIC reordena y consolida (3 aromas→1, eggshell+
    bisglicinato→'Calcio') por lo que los conteos casi nunca cuadran y el orden
    no se conserva. Estrategia: (1) clave fuerte para vitaminas/minerales;
    (2) tokens distintivos con asignación global 1-a-1 (Jaccard sobre la unión).
    Sin match → None (cae al cálculo puente de `_dosis_activo`)."""
    res: list[dict | None] = [None] * len(kic_ings)
    if not canonica:
        return res

    cused: set[int] = set()
    ckeys = [_ing_ident_key(f"{c.get('name','')} {c.get('active_name','') or ''}") for c in canonica]

    # (1) Vitaminas y minerales por clave de identidad.
    for ki, ing in enumerate(kic_ings):
        kk = _ing_ident_key(ing.get("ingrediente", ""))
        if not kk:
            continue
        for cj, ck in enumerate(ckeys):
            if cj not in cused and ck == kk:
                res[ki] = canonica[cj]
                cused.add(cj)
                break

    # (2) El resto por tokens distintivos; asignación global mejor-primero.
    pairs: list[tuple[float, int, int]] = []
    for ki, ing in enumerate(kic_ings):
        if res[ki] is not None:
            continue
        tk = _ing_dist_tokens(ing.get("ingrediente", ""))
        if not tk:
            continue
        for cj, c in enumerate(canonica):
            if cj in cused:
                continue
            tc = _ing_dist_tokens(f"{c.get('name','')} {c.get('active_name','') or ''}")
            inter = tk & tc
            if inter:
                pairs.append((len(inter) / len(tk | tc), ki, cj))
    for score, ki, cj in sorted(pairs, reverse=True):
        if res[ki] is None and cj not in cused and score >= 0.34:
            res[ki] = canonica[cj]
            cused.add(cj)
    return res


# Nota al pie según la procedencia del dato.
NOTA_DOSIS_ACTIVO_CANON = (
    "*Dosis de activo aportado según la ficha de fórmula (no la dosis de materia "
    "prima, confidencial). «—» = excipiente.*"
)


# Nota al pie reutilizable para las tablas de dosis de activo.
NOTA_DOSIS_ACTIVO = (
    "*Dosis de activo aportado (no la dosis de materia prima, confidencial). "
    "Estimada desde la estandarización; pendiente de conciliar con la Tabla "
    "Cuantitativa. «—» = excipiente o activo sin estandarización declarada.*"
)


# ── Bloque 1 · Tabla maestra de ingredientes ────────────────────────────────
# Sustituye las 3-4 tablas de ingredientes que antes repetían dosis y %NRV
# (KIC "Perfil", Regulatorio "Evaluación", Ficha Técnica "Composición").

def fmt_tabla_maestra(kic: dict, reg: dict, ft: dict, canonica: list[dict] | None = None) -> list[str]:
    """Tabla ÚNICA de ingredientes fusionando los tres agentes:
    dosis/%NRV/biodisponibilidad (KIC) + forma química (Ficha Técnica) +
    semáforo regulatorio (Regulatorio). Cruce por nombre normalizado.

    `canonica` (de `formula_canonica.json`, FT PDF) aporta la dosis de activo
    autoritativa, emparejada por índice (KIC conserva el orden del input)."""
    reg_by_name = {
        _norm(i.get("nombre", "")): i
        for i in reg.get("ingredientes", []) if isinstance(i, dict)
    }
    ft_comp = ft.get("fase_2_composicion", {})
    ft_ings = ft_comp.get("ingredientes_activos", ft_comp.get("ingredientes", [])) if isinstance(ft_comp, dict) else []
    ft_by_name: dict[str, dict] = {}
    for i in (ft_ings if isinstance(ft_ings, list) else []):
        if isinstance(i, dict):
            nm = i.get("nombre_ingrediente", i.get("nombre", i.get("ingrediente", "")))
            ft_by_name[_norm(nm)] = i

    kic_ings = [i for i in kic.get("fase_2_ingredientes", []) if isinstance(i, dict)]
    canon_alineada = _alinear_canonica(kic_ings, canonica or [])
    usa_canon = any(c is not None for c in canon_alineada)

    lines = [_section("Tabla de ingredientes", 3)]
    headers = ["#", "Ingrediente", "Nom Actiu", "% Actiu", "Dosis de activo", "% NRV/VRN", "Forma química", "Biodisponibilidad", "Reg."]
    rows = []
    for idx, ing in enumerate(kic_ings):
        nombre = ing.get("ingrediente", "")
        key = _norm(nombre)
        bio = ing.get("biodisponibilidad", {})
        bio_str = bio.get("nivel", "") if isinstance(bio, dict) else _val(bio)

        ft_i = ft_by_name.get(key, {})
        forma = ft_i.get("forma_quimica", ft_i.get("forma", "")) if isinstance(ft_i, dict) else ""

        reg_i = reg_by_name.get(key, {})
        sem = reg_i.get("semaforo", "") if isinstance(reg_i, dict) else ""
        sem_str = f"{SEMAFORO.get(sem, '')} {sem}".strip()

        canon_i = canon_alineada[idx]
        nom_actiu = canon_i.get("active_name", "") if canon_i else ""
        pct_actiu = canon_i.get("pct_active", "") if canon_i else ""
        if pct_actiu:
            pct_actiu = f"{pct_actiu}%"

        rows.append([
            str(idx + 1),
            nombre,
            nom_actiu or "—",
            pct_actiu or "—",
            _dosis_activo(ing, canon_i),
            _fmt_pct(ing.get("porcentaje_nrv", "")),
            forma or "—",
            bio_str or "—",
            sem_str or "—",
        ])
    lines += _table(headers, rows)
    lines.append("")
    lines.append(NOTA_DOSIS_ACTIVO_CANON if usa_canon else NOTA_DOSIS_ACTIVO)
    lines.append("")
    return lines


# ── Bloque 1 · Análisis de ingredientes (KIC, sin tabla ni mejoras) ──────────

def fmt_analisis_ingredientes(d: dict) -> list[str]:
    """Detalle función/mecanismo por ingrediente + matriz de interacciones +
    coherencia/sinergia. La tabla de dosis vive en la maestra; los gaps y
    sugerencias se consolidan en 'Propuestas de mejora'."""
    lines = [_section("Análisis de ingredientes", 3)]

    c = d.get("fase_1_clasificacion", {})
    lines += [
        f"**Tipo de producto:** {_val(c.get('tipo_producto'))}  ",
        f"**Objetivo funcional principal:** {_val(c.get('objetivo_funcional_principal'))}  ",
    ]
    obj_sec = c.get("objetivos_funcionales_secundarios", [])
    if obj_sec:
        lines.append(f"**Objetivos secundarios:** {', '.join(obj_sec)}  ")
    lines.append("")

    for ing in d.get("fase_2_ingredientes", []):
        if not isinstance(ing, dict):
            continue
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

    interacciones = d.get("fase_3_interacciones_cruzadas", [])
    if interacciones:
        lines.append(_section("Matriz de interacciones", 4))
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

    vg = d.get("fase_4_valoracion_global", {})
    if vg:
        lines.append(_section("Valoración global de la fórmula", 4))
        lines.append(f"**Coherencia funcional:** {_val(vg.get('coherencia_funcional'))}  ")
        lines.append(f"**Potencial sinérgico:** {_val(vg.get('potencial_sinergetico'))}  ")
        lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []), level=4)
    return lines


# ── Bloque 1 · Validación regulatoria (sin re-imprimir dosis ni mejoras) ─────

def fmt_validacion_regulatoria(d: dict) -> list[str]:
    lines = [_section("Validación regulatoria", 3)]

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

    # Tabla por ingrediente: normativa + condiciones. El semáforo y la dosis
    # ya están en la tabla maestra → aquí solo lo que aporta el regulatorio.
    lines.append(_section("Estatus regulatorio por ingrediente", 4))
    headers = ["Ingrediente", "Normativa aplicable", "Condiciones / Advertencias"]
    rows = []
    for ing in d.get("ingredientes", []):
        normativa = ing.get("normativa_aplicable", "")
        if isinstance(normativa, list):
            normativa = "; ".join(normativa[:2])
        cond = ing.get("condiciones", "")
        if isinstance(cond, list):
            cond = "; ".join(cond[:2])
        rows.append([
            ing.get("nombre", ""),
            normativa[:90],
            cond[:120] if cond else ing.get("dictamen", "")[:120],
        ])
    lines += _table(headers, rows)
    lines.append("")

    adv = ev.get("advertencias_obligatorias_producto", [])
    if adv:
        lines.append(_section("Advertencias obligatorias en etiqueta", 4))
        lines += [f"- {a}" for a in adv]
        lines.append("")

    lines += _fuentes(d.get("fuentes_consultadas", []), level=4)
    return lines


# ── Bloque 1 · Propuestas de mejora (consolida KIC + Regulatorio) ────────────

def fmt_propuestas_mejora(kic: dict, reg: dict) -> list[str]:
    """Consolida en un único bloque, sin duplicados, las recomendaciones de
    formulación de KIC (gaps/riesgos/sugerencias) y las modificaciones del
    agente Regulatorio."""

    def _extract(x) -> tuple[str, str, str]:
        if isinstance(x, dict):
            texto = x.get("gap", x.get("riesgo", x.get("sugerencia",
                     x.get("modificacion", x.get("detalle", "")))))
            detalle = x.get("detalle", x.get("descripcion", ""))
            accion = x.get("accion_sugerida", x.get("accion", ""))
            return str(texto), str(detalle), str(accion)
        return str(x), "", ""

    vg = kic.get("fase_4_valoracion_global", {}) or {}
    items: list[tuple[str, str, str, str]] = []  # (categoria, texto, detalle, accion)
    for campo, cat in [
        ("gaps_funcionales", "Gaps funcionales"),
        ("riesgos_formulacion", "Riesgos de formulación"),
        ("sugerencias_mejora", "Sugerencias de mejora"),
    ]:
        for x in (vg.get(campo, []) or []):
            t, det, acc = _extract(x)
            items.append((cat, t, det, acc))
    for x in ((reg.get("evaluacion_global", {}) or {}).get("modificaciones_recomendadas", []) or []):
        t, det, acc = _extract(x)
        items.append(("Modificaciones regulatorias", t, det, acc))

    if not items:
        return []

    # Dedup por clave normalizada del texto (captura repeticiones exactas/casi).
    seen: set[str] = set()
    by_cat: "OrderedDict[str, list[tuple[str, str, str]]]" = OrderedDict()
    for cat, t, det, acc in items:
        key = _norm(t)[:60]
        if not key or key in seen:
            continue
        seen.add(key)
        by_cat.setdefault(cat, []).append((t, det, acc))

    lines = [
        _section("Propuestas de mejora (IA)", 3),
        "*Consolidado de los análisis de composición (KIC) y regulatorio, sin duplicados.*",
        "",
    ]
    for cat, lst in by_cat.items():
        lines.append(f"**{cat}:**")
        for t, det, acc in lst:
            lines.append(f"- **{t}**" + (f": {det}" if det else ""))
            if acc:
                lines.append(f"  - *Acción:* {acc}")
        lines.append("")
    return lines



# ── Plantilla de Ficha Técnica (formato estándar Umbrella, 6 secciones) ──────
# Cabecera del fabricante y textos normativos deterministas: son plantilla, NO
# los inventa el LLM. Espejo del PDF "FT Formula 1 MIX 250188".

FT_FABRICANTE = {
    "Empresa": "Umbrella F&FI, S.L.",
    "NIF / VAT": "B65876351",
    "Dirección": "Pol. Ind. Mogent A7 Park — Av. Mogent 262-264, 08450 Llinars del Vallès (Barcelona), España",
    "Registro": "RGSEAA 26.020214/B",
    "Web": "www.umbrellamix.com",
}

# Anexo II Reg. (UE) 1169/2011 — 14 grupos de alérgenos de declaración obligatoria.
ALERGENOS_ANEXO_II = [
    "Cereales con gluten y derivados",
    "Crustáceos y derivados",
    "Huevos y derivados",
    "Pescado y derivados",
    "Cacahuetes y derivados",
    "Soja y derivados",
    "Leche y derivados (incl. lactosa)",
    "Frutos de cáscara (almendra, avellana, nuez…)",
    "Apio y derivados",
    "Mostaza y derivados",
    "Granos de sésamo y derivados",
    "Dióxido de azufre y sulfitos (>10 mg/kg)",
    "Altramuces y derivados",
    "Moluscos y derivados",
]

FT_DIETAS = ["Vegetariano", "Vegano", "Sin gluten", "Sin azúcar (<0,5 g/dosis)",
             "Kosher", "Halal", "Bio / Ecológico"]

# Boilerplate normativo de la plantilla Umbrella (no es output del LLM).
FT_FOOD_GRADE = (
    "Todos los aditivos cumplen la legislación alimentaria de la UE. Extractos vegetales y "
    "derivados de origen animal conformes al Reg. (CE) 396/2005 (residuos de plaguicidas) y a "
    "los límites de contaminantes del Reg. (UE) 915/2023. Criterios de pureza según Ph. Eur."
)
FT_GMO = "No fabricado a partir de materias primas GMO; no sujeto a Reg. (CE) 1829/2003 ni 1830/2003."
FT_TSE = "Fabricado sin materias primas de origen humano ni con riesgo TSE/BSE."
FT_TRANSPORTE = "No clasificado como peligroso. Transportar a 15-25 °C, protegido de luz, calor y humedad."


def _ft_nutricional_rows(nut: dict) -> list[list[str]]:
    """Extrae las filas de la tabla nutricional (acepta los dos formatos del LLM)."""
    tabla = nut.get("tabla_nutricional", nut.get("tabla", []))
    tab_por_dosis = nut.get("tabla_nutricional_por_dosis", {})
    rows: list[list[str]] = []
    if isinstance(tabla, list) and tabla:
        for fila in tabla:
            if isinstance(fila, dict):
                rows.append([
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
        sec = tab_por_dosis.get("seccion_obligatoria", {})
        if isinstance(sec, dict):
            for k, v in sec.items():
                if k == "metodo_calculo":
                    continue
                rows.append([NUTRIENTE_LABELS.get(k, k.replace("_", " ").capitalize()), _val(v), "—"])
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
                    rows.append([label_str, _val(cant_str), _val(v.get("porcentaje_nrv", v.get("pct_vrn", "")))])
    return rows


# ── Bloque 2 · Ficha Técnica (formato Umbrella de 6 secciones) ───────────────

def fmt_ficha_tecnica(ft: dict, qc: dict | None = None, kic: dict | None = None,
                      reg: dict | None = None, clm: dict | None = None,
                      nombre_producto: str = "", hoy: str = "",
                      canonica: list[dict] | None = None) -> list[str]:
    """Renderiza la Ficha Técnica con el formato estándar de 6 secciones de
    Umbrella, cruzando datos de Ficha Técnica + QC + KIC + Regulatorio + Claims.
    Los campos de fabricación que no existen en los datos se marcan como
    'pendiente de muestra de producción' (no se inventan)."""
    qc = qc or {}
    kic = kic or {}
    reg = reg or {}
    clm = clm or {}
    lines: list[str] = []
    id_ = ft.get("fase_1_identificacion", {})
    mea = ft.get("fase_7_modo_empleo_advertencias", {})
    modo = mea.get("modo_empleo", {}) if isinstance(mea, dict) else {}
    dosis_diaria = (modo.get("dosis_diaria", "") if isinstance(modo, dict) else "") or "—"

    # ── 1 · Identificación y tabla de claims activos ─────────────────
    lines.append(_section("1 · Identificación y claims activos", 3))
    lines += [f"**{k}:** {v}  " for k, v in FT_FABRICANTE.items()]
    lines.append("")
    lines += _kv_block(id_, [
        ("denominacion_legal", "Denominación legal"),
        ("nombre_comercial", "Nombre comercial"),
        ("tipo_producto", "Tipo de producto"),
        ("forma_presentacion", "Forma de presentación"),
        ("publico_objetivo", "Público objetivo"),
    ])
    if hoy:
        lines.append(f"**Fecha / versión:** {hoy}  ")
    lines.append(f"**Dosis diaria:** {dosis_diaria}  ")
    lines.append("")

    # Tabla de activos por dosis (Active Claims Table)
    lines.append(_section("Tabla de activos por dosis", 4))
    headers = ["Activo", "Dosis de activo", "% NRV/VRN", "Forma química"]
    ft_comp = ft.get("fase_2_composicion", {})
    ft_ings = ft_comp.get("ingredientes_activos", ft_comp.get("ingredientes", [])) if isinstance(ft_comp, dict) else []
    ft_by_name = {}
    for i in (ft_ings if isinstance(ft_ings, list) else []):
        if isinstance(i, dict):
            ft_by_name[_norm(i.get("nombre_ingrediente", i.get("nombre", i.get("ingrediente", ""))))] = i
    kic_ings = [i for i in kic.get("fase_2_ingredientes", []) if isinstance(i, dict)]
    canon_alineada = _alinear_canonica(kic_ings, canonica or [])
    usa_canon = any(c is not None for c in canon_alineada)
    rows = []
    for idx, ing in enumerate(kic_ings):
        nombre = ing.get("ingrediente", "")
        ft_i = ft_by_name.get(_norm(nombre), {})
        rows.append([
            nombre,
            _dosis_activo(ing, canon_alineada[idx]),
            _fmt_pct(ing.get("porcentaje_nrv", "")),
            (ft_i.get("forma_quimica", "") if isinstance(ft_i, dict) else "") or "—",
        ])
    lines += _table(headers, rows)
    lines.append("")
    lines.append(NOTA_DOSIS_ACTIVO_CANON if usa_canon else NOTA_DOSIS_ACTIVO)
    lines.append("")

    # Colección de posibles claims vs ingredientes (lo que pide Xavier)
    parte_a = clm.get("parte_a_claims_regulatorios", clm.get("claims_regulatorios", {}))
    if isinstance(parte_a, list):
        parte_a = {"claims_por_ingrediente": parte_a}
    claims_por_ing = parte_a.get("claims_por_ingrediente", []) if isinstance(parte_a, dict) else []
    if claims_por_ing:
        lines.append(_section("Posibles claims por ingrediente", 4))
        lines.append("*Resumen ingrediente → disponibilidad de claim EFSA. El listado completo está en el Bloque 3 (Marketing).*")
        headers = ["Ingrediente", "Claims EFSA", "Ejemplo de claim autorizado"]
        rows = []
        for ic in claims_por_ing:
            if not isinstance(ic, dict):
                continue
            cl = ic.get("claims", []) or []

            def _es_valido(c) -> bool:
                if not isinstance(c, dict):
                    return False
                ref = str(c.get("referencia_efsa", c.get("referencia_reglamento", c.get("id_ue", ""))))
                txt = str(c.get("texto_traduccion_es", c.get("texto_claim", c.get("texto", ""))))
                blob = (ref + " " + txt).upper()
                # Botánicos "on hold": el agente escribe "Ninguno autorizado" /
                # "No autorizado" → no es un claim válido, es estado en espera.
                invalidos = ("N/A", "NO APLICA", "SIN CLAIM", "NINGUNO AUTORIZADO",
                             "NO AUTORIZADO", "EN ESPERA", "ON HOLD", "PENDIENTE")
                return not any(m in blob for m in invalidos)

            válidos = [c for c in cl if _es_valido(c)]
            if válidos:
                c0 = válidos[0]
                ejemplo = c0.get("texto_traduccion_es", c0.get("texto_claim", c0.get("texto", "")))[:90] or "—"
                rows.append([ic.get("ingrediente", ""), str(len(válidos)), ejemplo])
            else:
                rows.append([ic.get("ingrediente", ""), "—", "En espera (botánico)"])
        lines += _table(headers, rows)
        lines.append("")

    # ── 2 · Tabla de ingredientes (orden de peso) ────────────────────
    lines.append(_section("2 · Ingredientes (por orden de peso)", 3))
    ordenados = sorted(
        [i for i in kic.get("fase_2_ingredientes", []) if isinstance(i, dict)],
        key=lambda i: i.get("dosis_formula_mg", 0) or 0, reverse=True,
    )
    if ordenados:
        items = []
        for ing in ordenados:
            ft_i = ft_by_name.get(_norm(ing.get("ingrediente", "")), {})
            forma = ft_i.get("forma_quimica", "") if isinstance(ft_i, dict) else ""
            items.append(f"{ing.get('ingrediente','')}" + (f" — *{forma}*" if forma else ""))
        lines += [f"- {x}" for x in items]
        lines.append("")
    lines.append("*Coadyuvantes tecnológicos y excipientes minoritarios según fórmula (Annex III Reg. (CE) 1334/2008).*")
    lines.append("")

    # ── 3 · Información nutricional, vida útil y reactividad ──────────
    lines.append(_section("3 · Información nutricional", 3))
    nut_rows = _ft_nutricional_rows(ft.get("fase_3_informacion_nutricional", {}))
    if nut_rows:
        lines += _table(["Nutriente", "Por dosis", "% VRN*"], nut_rows)
        lines.append("*\\* % Valores de Referencia de la Nutrición*")
        lines.append("")

    cons = ft.get("fase_6_conservacion_vida_util", {})
    vida = cons.get("vida_util_estimada", {}) if isinstance(cons, dict) else {}
    if isinstance(vida, dict) and vida.get("meses"):
        _m = str(vida["meses"]).strip()
        vida_str = _m if "mes" in _m.lower() else f"{_m} meses"
    else:
        vida_str = _val(vida if not isinstance(vida, dict) else "")
    lines.append(f"**Vida útil estimada:** {vida_str}  ")
    lines.append("")

    # Reactividad cualitativa: derivada de los riesgos/advertencias de KIC.
    riesgos = (kic.get("fase_4_valoracion_global", {}) or {}).get("riesgos_formulacion", [])
    if riesgos:
        lines.append(_section("Reactividad y estabilidad (cualitativa)", 4))
        for r in riesgos[:5]:
            txt = r.get("riesgo", r.get("detalle", str(r))) if isinstance(r, dict) else str(r)
            lines.append(f"- {txt}")
        lines.append("")

    # Microbiología (de QC fase_6) — datos analíticos de control.
    f6 = qc.get("fase_6_ensayos_analiticos_adicionales", {})
    micro = f6.get("microbiologia", {}) if isinstance(f6, dict) else {}
    crit = micro.get("criterios_microbiologicos", []) if isinstance(micro, dict) else []
    if crit:
        lines.append(_section("Criterios microbiológicos", 4))
        rows = [[c.get("parametro", ""), c.get("criterio", c.get("limite", ""))]
                for c in crit if isinstance(c, dict)]
        lines += _table(["Parámetro", "Criterio"], rows)
        lines.append("")

    # ── 4 · Identificación y especificaciones ────────────────────────
    lines.append(_section("4 · Identificación y especificaciones", 3))
    espec = ft.get("fase_5_especificaciones_tecnicas", {})
    fq = espec.get("especificaciones_fisicoquimicas", {}) if isinstance(espec, dict) else {}
    if isinstance(fq, dict) and fq:
        for k, v in fq.items():
            lines.append(f"**{k.replace('_',' ').capitalize()}:** {_spec_val(v)}  ")
        lines.append("")
    # Identidad analítica desde QC
    ftir = qc.get("fase_1_ftir", {})
    if ftir:
        lines.append(f"**Identidad FTIR:** {ftir.get('objetivo','Identificación por espectro FTIR — pasa test')}  ")
    if qc.get("fase_2_granulometria") or qc.get("fase_3_densidad") or qc.get("fase_4_ph"):
        lines.append("**Granulometría / densidad / pH:** según plan de control (ver Bloque 5).  ")
    if not fq and not ftir:
        lines.append("*Especificaciones físico-químicas pendientes de muestra de producción.*  ")
    lines += [
        "",
        f"**Food grade:** {FT_FOOD_GRADE}  ",
        f"**GMO:** {FT_GMO}  ",
        f"**TSE/BSE:** {FT_TSE}  ",
        "",
    ]

    # ── 5 · Alérgenos y aptitud dietética ────────────────────────────
    lines.append(_section("5 · Alérgenos y aptitud dietética", 3))
    alerg = ft.get("fase_4_alergenos", {})
    presentes = alerg.get("presentes", "") if isinstance(alerg, dict) else ""
    trazas = alerg.get("trazas", "") if isinstance(alerg, dict) else ""
    dec = alerg.get("declaracion_etiqueta", alerg.get("declaracion", "")) if isinstance(alerg, dict) else ""
    if presentes:
        lines.append(f"**Contiene:** {presentes if isinstance(presentes, str) else ', '.join(presentes)}")
    if trazas:
        lines.append(f"**Trazas posibles:** {trazas if isinstance(trazas, str) else ', '.join(trazas)}")
    if dec:
        lines.append(f"**Declaración:** {dec if isinstance(dec, str) else dec.get('texto_recomendado', str(dec))}")
    lines.append("")
    lines.append(_section("Tabla de alérgenos (Anexo II Reg. UE 1169/2011)", 4))
    lines.append("*Marcado a verificar con fichas de proveedor y plan HACCP; no analizado en esta fase.*")
    lines += _table(["Grupo de alérgenos", "Estado"],
                    [[a, "Verificar"] for a in ALERGENOS_ANEXO_II])
    lines.append("")
    lines.append(_section("Aptitud para dietas", 4))
    lines += _table(["Dieta", "Estado"], [[d, "Bajo petición"] for d in FT_DIETAS])
    lines.append("")

    # ── 6 · Datos de producto y conservación ─────────────────────────
    lines.append(_section("6 · Datos de producto y conservación", 3))
    if isinstance(cons, dict):
        for campo, label in [
            ("condiciones_conservacion", "Conservación"),
            ("condiciones_post_apertura", "Tras apertura"),
        ]:
            v = cons.get(campo)
            if v:
                lines.append(f"**{label}:** {_val(v)}  ")
    lines += [
        f"**Vida útil (producto terminado):** {vida_str}  ",
        f"**Transporte:** {FT_TRANSPORTE}  ",
        f"**Modo de empleo:** {dosis_diaria}  ",
        "",
    ]

    lines += _fuentes(ft.get("fuentes_consultadas", []))
    return lines


# ── Sección 4: Claims ───────────────────────────────────────────────────────

_SIN_CLAIM_MARKERS = ("ninguno autorizado", "no autorizado", "sin claim",
                      "n/a", "no aplica", "en espera", "on hold", "pendiente")


def _claim_en_espera(c) -> bool:
    """True si el 'claim' indica ausencia de claim autorizado (botánico en
    espera EFSA) en vez de un claim real del Reg. (UE) 432/2012."""
    if not isinstance(c, dict):
        return not str(c).strip()
    txt = str(c.get("texto_traduccion_es", c.get("texto_claim", c.get("texto", ""))))
    ref = str(c.get("referencia_efsa", c.get("referencia_reglamento", c.get("id_ue", ""))))
    blob = (txt + " " + ref).lower()
    return (not txt.strip()) or any(m in blob for m in _SIN_CLAIM_MARKERS)


def fmt_claims(d: dict) -> list[str]:
    lines = [_section("Claims y diferenciación comercial", 3)]

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
            # Botánicos sin claim autorizado: mostrar estado, no una fila vacía.
            válidos = [c for c in claims_list if not _claim_en_espera(c)]
            if not válidos:
                lines += ["*En espera (botánico) — sin claim autorizado en el Reg. (UE) 432/2012.*", ""]
                continue
            headers = ["Texto del claim", "Condición de uso", "Ref. EFSA"]
            rows = []
            for c in válidos:
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


# ── Bloque 3 · Etiqueta (layout cara frontal / caras laterales, ES + EN) ─────
# Espejo del ejemplo "Immunara*": panel frontal + caras laterales, con la
# división obligatorio/opcional que pide Xavier. Bilingüe: el español sale de
# los datos del agente; el inglés de los campos con sufijo `_en` (cuando el
# agente Etiqueta los emita) y, en su defecto, de las frases legales fijas.

ETIQUETA_MENCION = {"es": "Complemento alimenticio", "en": "Food supplement"}
ETIQUETA_ADVERTENCIAS_EN = [
    "Do not exceed the recommended daily dose.",
    "Food supplements should not be used as a substitute for a varied and balanced diet and a healthy lifestyle.",
    "Keep out of reach of young children.",
]
ETIQUETA_ECOEMBES = "Logo Ecoembes (Punto Verde) — gestión de residuos de envases"


def _etq_caras(d: dict) -> dict:
    caras = d.get("fase_2_texto_por_caras", d.get("caras", {}))
    if isinstance(caras, list):
        out: dict = {}
        for c in caras:
            if isinstance(c, dict):
                out[c.get("cara", "").lower().replace(" ", "_")] = c
        return out
    return caras if isinstance(caras, dict) else {}


def _etq_panel(caras: dict, lista_ing_es: str, lang: str, nombre_producto: str) -> list[str]:
    """Layout (cara frontal + caras laterales) en el idioma dado.
    Para 'en' lee los campos con sufijo `_en`; si faltan, usa las frases legales
    fijas y marca el contenido variable como pendiente."""
    cp = caras.get("cara_principal", {}) or {}
    cs = caras.get("cara_secundaria", {}) or {}
    cl = caras.get("cara_lateral_contraetiqueta", {}) or {}
    pend = "_(pendiente: regenerar el pipeline con el agente Etiqueta bilingüe)_" if lang == "en" else "—"

    def g(dic: dict, key: str) -> str:
        return (dic.get(f"{key}_en", "") if lang == "en" else dic.get(key, "")) or ""

    def gn(dic: dict, key: str) -> str:
        # Campos administrativos (operador, fabricante, lote, fechas): comunes a
        # ambos idiomas → siempre el valor base, sin sufijo _en ni 'pendiente'.
        return dic.get(key, "") or ""

    L: list[str] = []
    # ── Cara frontal ──
    L.append(_section("Cara frontal", 4))
    L.append("**Obligatorio:**")
    L.append(f"- Marca / nombre comercial: {nombre_producto or g(cp,'denominacion_venta') or pend}")
    base = g(cp, "denominacion_venta")
    # Evita "a base de… complemento alimenticio a base de…" (la denominación legal ya lo incluye).
    base = re.sub(r"(?i)^\s*(complemento alimenticio\s+)?a base de\s+", "", base).strip()
    en_base = "Food supplement based on:" if lang == "en" else "En base a:"
    L.append(f"- {en_base} {base or pend}")
    L.append(f"- Dosis / cantidad neta: {g(cp,'cantidad_neta') or pend}")
    L.append(f"- Mención legal: **{ETIQUETA_MENCION[lang]}**")
    L.append("**Opcional:**")
    L.append("- Logos (certificaciones: vegano, sin gluten, GMP… según corresponda)")
    L.append("")
    # ── Caras laterales ──
    L.append(_section("Caras laterales", 4))
    L.append("**Obligatorio:**")
    li = lista_ing_es if lang == "es" else g(cs, "lista_ingredientes")
    L.append("- Lista de ingredientes *(alérgenos en negrita)*:")
    L.append(f"  > {li or pend}")
    aler = g(cs, "alergenos")
    if aler:
        L.append(f"- Declaración de alérgenos: {aler}")
    modo = g(cs, "modo_empleo") or g(cs, "dosis_diaria")
    L.append(f"- Modo de empleo / dosis: {modo or pend}")
    adv = cs.get("advertencias_obligatorias", []) if lang == "es" else (cs.get("advertencias_obligatorias_en") or ETIQUETA_ADVERTENCIAS_EN)
    L.append("- Advertencias y frases obligatorias:")
    for a in (adv or []):
        L.append(f"  - {a.get('texto', a) if isinstance(a, dict) else a}")
    op_es = [("operador_responsable", "Operador responsable"), ("fabricante", "Fabricado por")]
    op_en = [("operador_responsable", "Responsible operator"), ("fabricante", "Manufactured by")]
    for key, lab in (op_en if lang == "en" else op_es):
        v = gn(cl, key)  # administrativo → valor común (no se traduce)
        if v:
            L.append(f"- {lab}: {v.splitlines()[0] if v else v}")
    L.append("- Distribuido por: " + (gn(cl, "distribuido_por") or "—"))
    L.append(f"- Peso neto · Lote · Caducidad: {gn(cl, 'fecha_duracion_minima') or '—'}")
    L.append(f"- {ETIQUETA_ECOEMBES}")
    L.append("**Opcional:**")
    L.append("- Tabla nutricional / %VRN → ver Bloque 2 (Ficha Técnica)")
    L.append("- Contribución nutricional (claims) → ver Claims, Bloque 3")
    L.append("- Código de barras · código QR")
    L.append("")
    return L


def fmt_etiqueta(d: dict, nombre_producto: str = "") -> list[str]:
    lines = [_section("Propuesta de etiqueta", 3)]
    caras = _etq_caras(d)
    lista_ing = d.get("fase_4_lista_ingredientes_completa", d.get("lista_ingredientes_completa", ""))
    if isinstance(lista_ing, dict):
        lista_ing = lista_ing.get("texto", lista_ing.get("lista", ""))

    lines.append(_section("Versión en español (ES)", 4))
    lines += _etq_panel(caras, lista_ing, "es", nombre_producto)

    lines.append(_section("Versión en inglés (EN)", 4))
    has_en = any(
        (caras.get(c, {}) or {}).get(f"{k}_en")
        for c in ("cara_principal", "cara_secundaria", "cara_lateral_contraetiqueta")
        for k in ("denominacion_venta", "lista_ingredientes", "modo_empleo")
    )
    if not has_en:
        lines += [
            "*El agente Etiqueta aún no emite contenido en inglés; se muestran las "
            "menciones legales fijas en EN y el contenido variable queda pendiente. "
            "Regenera el pipeline tras activar el modo bilingüe del agente para poblarlo.*",
            "",
        ]
    lines += _etq_panel(caras, lista_ing, "en", nombre_producto)

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
    lines = [_section("Formatos e innovación", 3)]

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
            if isinstance(items, list):
                lines += _labeled_list(label, items)

    lines += _fuentes(d.get("fuentes_consultadas", []))
    return lines


# ── Bloque 3 · Segmentos de mercado (Claims) ─────────────────────────────────

def fmt_segmentos(clm: dict) -> list[str]:
    """Segmentos de mercado adecuados para la fórmula. Usa la lista estructurada
    `parte_f_segmentos_mercado` si el agente la emite; si no, cae a los públicos
    objetivo de `parte_d_diferenciadores` (lo que existe hoy)."""
    seg = clm.get("parte_f_segmentos_mercado", clm.get("segmentos_mercado", []))
    pd = clm.get("parte_d_diferenciadores", {}) if isinstance(clm.get("parte_d_diferenciadores"), dict) else {}

    lines = [_section("Segmentos de mercado", 3)]
    if isinstance(seg, list) and seg:
        headers = ["Segmento", "Necesidad principal", "Encaje con la fórmula", "Mensaje clave"]
        rows = []
        for s in seg:
            if not isinstance(s, dict):
                continue
            rows.append([
                s.get("segmento", s.get("nombre", "")),
                s.get("necesidad_principal", s.get("necesidad", "")),
                s.get("encaje_formula", s.get("encaje", "")),
                s.get("mensaje_clave", s.get("mensaje", "")),
            ])
        lines += _table(headers, rows)
        lines.append("")
    elif pd.get("publico_objetivo_principal") or pd.get("publico_objetivo_secundario"):
        if pd.get("publico_objetivo_principal"):
            lines.append(f"**Público objetivo principal:** {pd['publico_objetivo_principal']}  ")
        if pd.get("publico_objetivo_secundario"):
            lines.append(f"**Público objetivo secundario:** {pd['publico_objetivo_secundario']}  ")
        if pd.get("momento_consumo"):
            lines.append(f"**Momento de consumo:** {pd['momento_consumo']}  ")
        lines += ["", "*Segmentación detallada pendiente: regenera el pipeline para poblar la tabla de segmentos.*", ""]
    else:
        lines += ["*Pendiente: regenera el pipeline para poblar los segmentos de mercado.*", ""]
    return lines


# ── Bloque 3 · Formatos × Segmentos (Formatos) ───────────────────────────────

def fmt_formatos_segmentos(fmt: dict) -> list[str]:
    """Matriz formato × segmento. Usa `matriz_formato_segmento` si el agente la
    emite; si no, deriva una matriz inicial del formato óptimo/alternativo y los
    formatos de innovación ya presentes."""
    lines = [_section("Formatos × Segmentos", 3)]
    matriz = fmt.get("matriz_formato_segmento", [])
    if isinstance(matriz, list) and matriz:
        headers = ["Segmento", "Formato recomendado", "Por qué", "Innovación"]
        rows = []
        for m in matriz:
            if not isinstance(m, dict):
                continue
            innov = m.get("es_innovacion", m.get("innovacion", ""))
            innov_str = "✅" if innov is True else ("—" if innov in (False, "", None) else _val(innov))
            rows.append([
                m.get("segmento", ""),
                m.get("formato_recomendado", m.get("formato", "")),
                m.get("justificacion", m.get("motivo", "")),
                innov_str,
            ])
        lines += _table(headers, rows)
        lines.append("")
        return lines

    # Fallback: matriz inicial derivada de la recomendación de formatos existente.
    rec = fmt.get("fase_4_recomendacion_final", {})
    opt = rec.get("formato_optimo", {}) if isinstance(rec, dict) else {}
    alt = rec.get("formato_alternativo", {}) if isinstance(rec, dict) else {}
    opt_n = opt.get("nombre", "") if isinstance(opt, dict) else _val(opt)
    alt_n = alt.get("nombre", "") if isinstance(alt, dict) else _val(alt)
    rows = []
    if opt_n:
        rows.append(["Segmento principal", opt_n,
                     (opt.get("justificacion_comercial", "") if isinstance(opt, dict) else "") or "Formato óptimo recomendado", "—"])
    if alt_n:
        rows.append(["Segmento alternativo", alt_n,
                     (alt.get("escenario", "") if isinstance(alt, dict) else "") or "Escenario de coste/target distinto", "—"])
    if rows:
        lines += _table(["Segmento", "Formato recomendado", "Por qué", "Innovación"], rows)
        lines += ["", "*Matriz inicial derivada del análisis de formatos. Regenera el pipeline para la matriz formato×segmento completa.*", ""]
    else:
        lines += ["*Pendiente: regenera el pipeline para poblar la matriz formato×segmento.*", ""]
    return lines


# ── Sección 7: Docs Internos ────────────────────────────────────────────────

def fmt_docs_internos(d: dict) -> list[str]:
    # El título del bloque ("## 4. Documentación Interna de Producción") lo añade compose_informe.
    lines: list[str] = []

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
                    # El marcador PCC va FUERA de la negrita del título para no
                    # anidar `**...**` (rompe el render markdown→PDF dejando '**').
                    pcc_str = " 🔴 PCC" if pcc else ""
                    lines.append(f"**{num}. {op}**{pcc_str}")
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
    # El título del bloque ("## 5. Plan de Calidad") lo añade compose_informe.
    lines: list[str] = []

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
                            _val(ensayo.get("parametro", categoria))[:40],
                            _val(ensayo.get("justificacion", ensayo.get("activo_a_controlar", "")))[:60],
                            _spec_val(ensayo.get("especificacion", ensayo.get("criterio", "")))[:80],
                            _method_str(ensayo.get("metodo", ensayo.get("referencia_metodologica", ""))),
                            _val(ensayo.get("frecuencia", "")),
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
                    _dur = str(cond.get("duracion", cond.get("meses", ""))).strip()
                    _dur_str = _dur if (not _dur or "mes" in _dur.lower()) else f"{_dur} meses"
                    lines.append(f"- {cond.get('tipo', cond.get('nombre',''))}: {cond.get('temperatura','')} / {cond.get('humedad_relativa', cond.get('humedad',''))} — {_dur_str}")
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


# ── Bloque 6 · Portfolio recomendado (Agente 9) ──────────────────────────────

def fmt_portfolio(d: dict) -> list[str]:
    """Renderiza el portfolio a aconsejar al cliente: posicionamiento del
    producto ancla, extensiones de línea, productos complementarios y gama
    recomendada."""
    lines: list[str] = []

    pos = d.get("fase_1_posicionamiento", {})
    if isinstance(pos, dict) and pos:
        lines += _kv_block(pos, [
            ("producto_ancla", "Producto ancla"),
            ("categoria", "Categoría"),
            ("propuesta_valor", "Propuesta de valor"),
        ])
        lines.append("")

    def _tabla_productos(items: list, titulo: str, col_relacion: str, key_relacion: str) -> None:
        if not isinstance(items, list) or not items:
            return
        lines.append(_section(titulo, 3))
        headers = ["Producto", col_relacion, "Ingredientes clave", "Formato", "Segmento"]
        rows = []
        for p in items:
            if not isinstance(p, dict):
                continue
            ing = p.get("ingredientes_clave", [])
            ing_str = ", ".join(ing) if isinstance(ing, list) else _val(ing)
            rows.append([
                p.get("nombre", ""),
                p.get(key_relacion, p.get("descripcion", "")),
                ing_str or "—",
                p.get("formato_sugerido", "") or "—",
                p.get("segmento_objetivo", "") or "—",
            ])
        lines.extend(_table(headers, rows))
        lines.append("")

    _tabla_productos(d.get("fase_2_extensiones_linea", []),
                     "Extensiones de línea", "Diferencia vs ancla", "diferencia_vs_ancla")
    _tabla_productos(d.get("fase_3_productos_complementarios", []),
                     "Productos complementarios", "Sinergia con el ancla", "sinergia_con_ancla")

    gama = d.get("fase_4_gama_recomendada", {})
    if isinstance(gama, dict) and gama:
        lines.append(_section("Gama recomendada (roadmap)", 3))
        sec = gama.get("secuencia_lanzamiento", [])
        if isinstance(sec, list):
            lines += [f"- {s}" for s in sec]
        just = gama.get("justificacion", "")
        if just:
            lines += ["", f"*{just}*"]
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
    prt = _load("agente_9_portfolio_v2", output_dir)
    canonica = _load_canonica(output_dir)  # dosis de activo del FT PDF (si existe)

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
        "AGENT_9_PORTFOLIO": prt.get("_trazabilidad", {}),
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
        "1. [Fórmula Cuantitativa](#1-fórmula-cuantitativa)",
        "2. [Ficha Técnica](#2-ficha-técnica)",
        "3. [Información de Marketing](#3-información-de-marketing)",
        "4. [Documentación Interna de Producción](#4-documentación-interna-de-producción)",
        "5. [Plan de Calidad](#5-plan-de-calidad)",
        "6. [Portfolio recomendado](#6-portfolio-recomendado)",
        "7. [Anexo — Configuración del Pipeline](#anexo--configuración-del-pipeline)",
        "",
        "---",
        "",
        "> **Confidencialidad:** la fórmula cuantitativa (dosis de materia prima) es "
        "información reservada de Umbrella y solo figura en los bloques internos de "
        "producción y calidad (4 y 5). Los bloques 1–3 muestran únicamente la "
        "**dosis de activo aportado**.",
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

    # ── Bloque 1 · Fórmula Cuantitativa ──────────────────────────────
    # Tabla maestra (única) + análisis de ingredientes + validación
    # regulatoria + propuestas de mejora consolidadas.
    if kic or reg or ft:
        lines.append(_section("1. Fórmula Cuantitativa", 2))
        if kic:
            lines += fmt_tabla_maestra(kic, reg, ft, canonica=canonica)
            lines += fmt_analisis_ingredientes(kic)
        if reg:
            lines += fmt_validacion_regulatoria(reg)
        propuestas = fmt_propuestas_mejora(kic, reg)
        if propuestas:
            lines += propuestas
        lines.append("\n---")

    # ── Bloque 2 · Ficha Técnica ─────────────────────────────────────
    if ft:
        lines.append(_section("2. Ficha Técnica", 2))
        lines += fmt_ficha_tecnica(ft, qc=qc, kic=kic, reg=reg, clm=clm,
                                   nombre_producto=nombre_producto, hoy=hoy,
                                   canonica=canonica)
        lines.append("\n---")

    # ── Bloque 3 · Información de Marketing ───────────────────────────
    if clm or fmt or etq:
        lines.append(_section("3. Información de Marketing", 2))
        if clm:
            lines += fmt_claims(clm)
            lines += fmt_segmentos(clm)
        if fmt:
            lines += fmt_formatos(fmt)
            lines += fmt_formatos_segmentos(fmt)
        if etq:
            lines += fmt_etiqueta(etq, nombre_producto=nombre_producto)
        lines.append("\n---")

    # ── Bloque 4 · Documentación Interna de Producción ───────────────
    if doc:
        lines.append(_section("4. Documentación Interna de Producción", 2))
        lines += fmt_docs_internos(doc)
        lines.append("\n---")

    # ── Bloque 5 · Plan de Calidad ───────────────────────────────────
    if qc:
        lines.append(_section("5. Plan de Calidad", 2))
        lines += fmt_qc(qc)
        lines.append("\n---")

    # ── Bloque 6 · Portfolio recomendado (Agente 9) ──────────────────
    lines.append(_section("6. Portfolio recomendado", 2))
    if prt:
        lines += fmt_portfolio(prt)
    else:
        lines.append(
            "*Pendiente: ejecuta el pipeline con el Agente 9 (Portfolio) para poblar "
            "esta sección con la propuesta de gama a aconsejar al cliente.*"
        )
        lines.append("")
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
            "AGENT_9_PORTFOLIO": ("Portfolio", "Agente 9 — Portfolio recomendado"),
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
            "| Agente | Modelo | Temp | Tiempo | Tokens (in / out) | Coste est. | Endpoint |",
            "|---|---|---|---|---|---|---|",
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
            temperature = tr.get("temperature", cfg.temperature)

            lines.append(
                f"| {name} | `{cfg.model}` | `{temperature}` | {t_str} | {tok_str} | {cost_str} | `{cfg.base_url}` |"
            )

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📋 Informe compuesto guardado en {path}")
