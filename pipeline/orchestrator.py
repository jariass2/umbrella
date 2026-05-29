"""Pipeline v2 completo: 8 agentes en cadena + composición programática del informe."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys as _sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from json_repair import repair_json
from pydantic import BaseModel

import sys
from pathlib import Path

# Ensure project root is on sys.path so sibling packages resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.monitored_tools import MonitoredPubmedTools
from tools.tavily_search import TavilySearchTools
from tools.monitor import (
    monitor_agent_start, monitor_agent_end, monitor_agent_retry,
    monitor_wave, monitor_pipeline,
)

from agents.kic_agent_v2 import KIC_INSTRUCTIONS, KICAnalysis, PROMPT_VERSION as KIC_PROMPT_VERSION
from agents.regulatory_agent_v2 import REGULATORY_INSTRUCTIONS, PROMPT_VERSION as REGULATORY_PROMPT_VERSION
from agents.ficha_tecnica_agente_v2 import FICHA_TECNICA_INSTRUCTIONS, FichaTecnica, PROMPT_VERSION as FT_PROMPT_VERSION
from agents.claims_agent_v2 import CLAIMS_INSTRUCTIONS, ClaimsAnalysis, PROMPT_VERSION as CLAIMS_PROMPT_VERSION
from agents.etiqueta_agent_v2 import ETIQUETA_INSTRUCTIONS, EtiquetaAnalysis, PROMPT_VERSION as ETIQUETA_PROMPT_VERSION
from agents.formatos_agent_v2 import FORMATOS_INSTRUCTIONS, FormatosAnalysis, PROMPT_VERSION as FORMATOS_PROMPT_VERSION
from agents.docs_internos_agent_v2 import DOCS_INTERNOS_INSTRUCTIONS, DocsInternosAnalysis, PROMPT_VERSION as DOCS_PROMPT_VERSION
from agents.qc_agent_v2 import QC_INSTRUCTIONS, PlanQCAnalysis, PROMPT_VERSION as QC_PROMPT_VERSION
from pipeline.config import (
    get_agent_config,
    get_search_max_queries,
    AGENT_PREFIXES,
    print_pipeline_config,
)
from pipeline.report_composer import compose_informe

# Mapa de modelos Pydantic por clave de agente (None = sin modelo, usa json_mode)
AGENT_OUTPUT_MODELS: dict[str, type[BaseModel] | None] = {
    "KIC": KICAnalysis,
    "Regulatorio": None,  # no tiene modelo Pydantic, usa json_mode
    "Ficha Técnica": FichaTecnica,
    "Claims": ClaimsAnalysis,
    "Etiqueta": EtiquetaAnalysis,
    "Formatos": FormatosAnalysis,
    "Docs Internos": DocsInternosAnalysis,
    "QC": PlanQCAnalysis,
}

AGENT_PROMPT_VERSIONS: dict[str, str] = {
    "KIC": KIC_PROMPT_VERSION,
    "Regulatorio": REGULATORY_PROMPT_VERSION,
    "Ficha Técnica": FT_PROMPT_VERSION,
    "Claims": CLAIMS_PROMPT_VERSION,
    "Etiqueta": ETIQUETA_PROMPT_VERSION,
    "Formatos": FORMATOS_PROMPT_VERSION,
    "Docs Internos": DOCS_PROMPT_VERSION,
    "QC": QC_PROMPT_VERSION,
}

# Agentes que necesitan búsqueda web (el resto trabaja solo con la fórmula)
AGENTS_WITH_SEARCH = {"KIC", "Regulatorio", "Claims"}

# Semáforos por base_url: limitan llamadas concurrentes por endpoint.
# z.ai falla bajo 3 llamadas paralelas → límite 2. nvidia aguanta más → límite 4.
_ENDPOINT_MAX_CONCURRENT: dict[str, int] = {
    "api.z.ai": 2,
    "openrouter.ai": 4,
}
_ENDPOINT_DEFAULT_CONCURRENT = 4
_endpoint_semaphores: dict[str, threading.Semaphore] = {}
_endpoint_semaphores_lock = threading.Lock()


def _get_semaphore(base_url: str | None) -> threading.Semaphore:
    """Devuelve (creando si hace falta) el semáforo para el endpoint dado."""
    key = base_url or ""
    with _endpoint_semaphores_lock:
        if key not in _endpoint_semaphores:
            limit = _ENDPOINT_DEFAULT_CONCURRENT
            for host, max_c in _ENDPOINT_MAX_CONCURRENT.items():
                if host in key:
                    limit = max_c
                    break
            _endpoint_semaphores[key] = threading.Semaphore(limit)
    return _endpoint_semaphores[key]

# Configuración de reintentos: presupuestos diferenciados.
# - Transitorios (red, timeout, 429, 5xx): backoff exponencial, hasta 3 reintentos.
# - Deterministas (JSON malformado, ValidationError, ValueError de parser):
#   1 reintento rápido — el LLM a veces se recupera al segundo intento.
TRANSIENT_BUDGET = 3
TRANSIENT_BASE_DELAY = 5  # segundos: 5, 10, 20
DETERMINISTIC_BUDGET = 1
DETERMINISTIC_DELAY = 1   # segundos: reintento inmediato

_DETERMINISTIC_TYPES = {
    "JSONDecodeError",
    "ValidationError",
    "ValueError",
    "TypeError",
    "AttributeError",
    "KeyError",
}

_TRANSIENT_MARKERS = (
    "timeout", "timed out", "connection", "network", "temporarily",
    "429", "500", "502", "503", "504", "rate limit", "remote disconnected",
)

_TRANSIENT_TYPE_HINTS = (
    "Timeout", "ConnectError", "ConnectionError", "ReadError", "WriteError",
    "RemoteProtocolError", "APIConnectionError", "RateLimitError",
    "APIStatusError", "APIError",
)


def _is_transient_error(exc: Exception) -> bool:
    """Clasifica un error como transitorio (vale la pena reintentar con backoff)
    o determinista (un reintento rápido y, si vuelve a fallar, abortar)."""
    name = type(exc).__name__
    if name in _DETERMINISTIC_TYPES:
        return False
    if any(hint in name for hint in _TRANSIENT_TYPE_HINTS):
        return True
    msg = str(exc).lower()
    if any(m in msg for m in _TRANSIENT_MARKERS):
        return True
    # Por defecto, tratar como transitorio (conservador).
    return True

FORMULA_EJEMPLO = """\
Collagen Complex Pro

- L-Glicina: 5g
- Péptidos de Colágeno: 5g
- Ácido Hialurónico: 100mg
- Magnesio: 75mg
- AKBA (Boswellia serrata, extracto 30% AKBA): 10mg
- Hierro: 3,5mg
- Zinc: 2,5mg
- Vitamina B5 (ácido pantoténico): 1,5mg
- Astaxantina: 1mg
- Vitamina B2 (riboflavina): 0,35mg
- Vitamina B6 (piridoxina): 0,35mg
- Vitamina B1 (tiamina): 0,275mg
- Folato (ácido fólico): 50µg
- Vitamina K2 (MK-7): 25µg
- Vitamina B12 (cianocobalamina): 0,63µg
"""

OUTPUT_DIR = "outputs/v2"


def _load_formula(path: str | None, inline: str | None) -> tuple[str, str]:
    """Devuelve (texto_formula, fuente_descriptiva).

    Precedencia: --formula-text > --formula <path>/`-` (stdin) > FORMULA_EJEMPLO.
    """
    if inline:
        text = inline.strip()
        if not text:
            raise ValueError("--formula-text está vacío")
        return text, "inline (--formula-text)"

    if path:
        if path == "-":
            text = _sys.stdin.read().strip()
            if not text:
                raise ValueError("stdin vacío (se esperaba la fórmula por --formula -)")
            return text, "stdin"
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"--formula apunta a un archivo inexistente: {p}")
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"--formula vacío: {p}")
        return text, str(p)

    return FORMULA_EJEMPLO.strip(), "FORMULA_EJEMPLO (default hardcodeado)"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pipeline.orchestrator",
        description="Pipeline v2 — analiza una fórmula con 8 agentes en cadena.",
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--formula", "-f",
        metavar="PATH",
        help="Ruta al archivo de texto con la fórmula (usa '-' para leer de stdin). "
             "Si se omite y no hay --formula-text, se usa FORMULA_EJEMPLO.",
    )
    src.add_argument(
        "--formula-text", "-t",
        metavar="TEXTO",
        help="Texto de la fórmula inline. Útil para invocaciones desde otros scripts.",
    )
    parser.add_argument(
        "--output-dir", "-o",
        metavar="DIR",
        default=OUTPUT_DIR,
        help=f"Directorio donde se guardan los outputs (JSON/MD/informe). "
             f"Default: {OUTPUT_DIR}. Cada run sobreescribe los archivos del directorio elegido, "
             f"así que usa un dir distinto por fórmula si quieres conservar runs anteriores.",
    )
    return parser.parse_args(argv)


def make_agent(name: str, env_prefix: str,
               use_search: bool = True) -> Agent:
    cfg = get_agent_config(env_prefix)
    pubmed_email = os.getenv("PUBMED_EMAIL", "pipeline@paymsa.com")
    tools = [TavilySearchTools(), MonitoredPubmedTools(email=pubmed_email)] if use_search else []
    return Agent(
        name=name,
        model=OpenAILike(
            id=cfg.model,
            api_key=cfg.api_key,
            base_url=cfg.base_url,
            temperature=cfg.temperature,
            request_params={"timeout": 300},
        ),
        tools=tools,
        markdown=False,
    )


def strip_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*\n?|\n?```\s*$", "", text.strip(), flags=re.MULTILINE)


def _to_md(value, depth: int = 0) -> str:
    """Convierte recursivamente un valor JSON a texto markdown legible."""
    indent = "  " * depth
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            label = k.replace("_", " ").capitalize()
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{indent}**{label}:**")
                lines.append(_to_md(v, depth + 1))
            else:
                lines.append(f"{indent}**{label}:** {_to_md(v, depth)}")
        return "\n".join(lines)
    elif isinstance(value, list):
        if not value:
            return f"{indent}_(vacío)_"
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{indent}-")
                lines.append(_to_md(item, depth + 1))
            else:
                lines.append(f"{indent}- {item}")
        return "\n".join(lines)
    else:
        return str(value) if value is not None else "—"


def save_markdown(data: dict, label: str, filename_base: str) -> None:
    """Guarda una versión markdown legible del output del agente."""
    path = f"{OUTPUT_DIR}/{filename_base}.md"

    lines = [f"# {label}\n"]

    fuentes = data.get("fuentes_consultadas")
    body = {k: v for k, v in data.items() if k != "fuentes_consultadas"}
    lines.append(_to_md(body))

    if fuentes:
        lines.append("\n---\n## Fuentes consultadas\n")
        for f in fuentes:
            fid = f.get("id", "")
            nombre = f.get("fuente", "")
            url = f.get("url", "")
            tipo = f.get("tipo", "")
            url_str = f" — [{url}]({url})" if url else ""
            lines.append(f"[{fid}] **{nombre}**{url_str} _{tipo}_")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📄 Markdown guardado en {path}")


def _validate_defensively(data: dict, output_model: type[BaseModel] | None, label: str) -> None:
    """Valida el dict contra el modelo Pydantic sin abortar.

    Loguea avisos cuando el LLM se desvía del contrato (claves faltantes/extra o
    tipos incorrectos), pero deja pasar el `data` original para que el pipeline
    continúe. La validación es informativa, no bloqueante.
    """
    if output_model is None or not isinstance(data, dict):
        return
    try:
        obj = output_model.model_validate(data)
        dumped = obj.model_dump()
        expected = set(dumped.keys())
        got = set(data.keys())
        missing = expected - got
        extra = got - expected
        if missing:
            print(f"⚠️  [{label}] claves faltantes vs schema: {sorted(missing)}")
        if extra:
            print(f"ℹ️  [{label}] claves extra no contempladas en schema: {sorted(extra)}")
    except Exception as e:
        # Truncamos el mensaje para no inundar logs cuando hay muchos errores
        msg = str(e).replace("\n", " ")[:400]
        print(f"⚠️  [{label}] drift contra schema {output_model.__name__}: {msg}")


def _collect_tool_calls(agent: Agent) -> dict[str, int]:
    """Suma el `call_count` de cada toolkit del agente, agrupado por nombre lógico."""
    counts: dict[str, int] = {}
    for tool in getattr(agent, "tools", []) or []:
        n = getattr(tool, "call_count", None)
        if n is None:
            continue
        # Nombre lógico estable para reporting (no el nombre de la clase Python).
        cls_name = type(tool).__name__
        label = {
            "MonitoredPubmedTools": "pubmed",
            "MonitoredDuckDuckGoTools": "duckduckgo",
            "TavilySearchTools": "tavily",
        }.get(cls_name, cls_name)
        counts[label] = counts.get(label, 0) + int(n)
    return counts


def _build_trace(agent: Agent, prompt_version: str | None,
                 attempt: int, transient_count: int, deterministic_count: int,
                 elapsed: float, input_tokens: int = 0,
                 output_tokens: int = 0) -> dict:
    """Construye el bloque `_trazabilidad` con metadatos operacionales del run."""
    from datetime import datetime, timezone
    model_id = getattr(getattr(agent, "model", None), "id", None)
    base_url = getattr(getattr(agent, "model", None), "base_url", None)
    temperature = getattr(getattr(agent, "model", None), "temperature", None)
    tool_calls = _collect_tool_calls(agent)
    return {
        "prompt_version": prompt_version,
        "model": model_id,
        "base_url": base_url,
        "temperature": temperature,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_s": round(elapsed, 2),
        "attempts": attempt,
        "transient_retries": transient_count,
        "deterministic_retries": deterministic_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tool_calls": tool_calls,
        "tool_calls_total": sum(tool_calls.values()) if tool_calls else 0,
    }


def run_agent(agent: Agent, prompt: str, label: str,
              output_model: type[BaseModel] | None = None,
              prompt_version: str | None = None) -> dict:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    filename = label.lower().replace(" ", "_").replace(":", "").replace("→", "").strip()
    last_error = None
    monitor_agent_start(label)

    transient_count = 0
    deterministic_count = 0
    attempt = 0
    max_intentos = 1 + TRANSIENT_BUDGET + DETERMINISTIC_BUDGET  # cota superior

    while attempt < max_intentos:
        attempt += 1
        try:
            print(f"Ejecutando agente (intento {attempt})...\n")
            t0 = time.time()
            response = agent.run(prompt)
            content = response.content

            if isinstance(content, BaseModel):
                data = content.model_dump()
            elif isinstance(content, dict):
                data = content
            elif isinstance(content, str):
                text = strip_fences(content)
                if not text:
                    # Respuesta vacía = timeout o error de red tragado por agno.
                    # Clasificar como TRANSITORIO para activar backoff completo.
                    raise ConnectionError("Respuesta vacía del LLM (posible timeout de red)")
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    repaired = repair_json(text)
                    data = json.loads(repaired)
            elif content is None:
                raise ConnectionError("Respuesta None del LLM (posible timeout de red)")
            else:
                raise ValueError(f"Respuesta inesperada del agente: type={type(content).__name__}")

            if not isinstance(data, dict):
                if isinstance(data, list):
                    dicts = [x for x in data if isinstance(x, dict) and x]
                    if len(dicts) == 1:
                        print(f"⚠️  [{label}] respuesta top-level era lista; se extrae el único dict")
                        data = dicts[0]
                    elif len(dicts) > 1:
                        print(f"⚠️  [{label}] respuesta top-level era lista con {len(dicts)} dicts; se fusionan")
                        merged = {}
                        for d in dicts:
                            merged.update(d)
                        data = merged
                    else:
                        print(f"⚠️  [{label}] respuesta top-level no es dict ({type(data).__name__}); se envuelve en _payload")
                        data = {"_payload": data}
                else:
                    print(f"⚠️  [{label}] respuesta top-level no es dict ({type(data).__name__}); se envuelve en _payload")
                    data = {"_payload": data}

            elapsed = time.time() - t0
            monitor_agent_end(label, success=True, duration_s=elapsed)

            # Validación defensiva: avisa de drift contra el schema Pydantic
            # pero NO aborta — el `data` original se entrega al siguiente agente.
            _validate_defensively(data, output_model, label)

            # Capturar tokens del modelo antes de inyectar trazabilidad
            # response.metrics es un Dict[str, list] (Agno agrega valores por mensaje),
            # no un objeto. Hay que sumar las listas.
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, "metrics") and response.metrics:
                m = response.metrics
                def _sum_metric(key: str) -> int:
                    v = m.get(key) if isinstance(m, dict) else getattr(m, key, 0)
                    if isinstance(v, list):
                        return sum(int(x or 0) for x in v)
                    return int(v or 0)
                input_tokens = _sum_metric("input_tokens")
                output_tokens = _sum_metric("output_tokens")
                total_tokens = input_tokens + output_tokens
                print(f"📊 Tokens: {input_tokens} in + {output_tokens} out = {total_tokens} total | ⏱️ {elapsed:.1f}s")

            # Trazabilidad: model, base_url, prompt_version, timestamp, intentos, tokens.
            # Se inyecta como `_trazabilidad` (prefijo `_` = managed por orquestador)
            # para no colisionar con el `metadata` emitido por el LLM.
            if isinstance(data, dict):
                data["_trazabilidad"] = _build_trace(
                    agent, prompt_version, attempt,
                    transient_count, deterministic_count, elapsed,
                    input_tokens=input_tokens, output_tokens=output_tokens,
                )

            # Guardar JSON
            json_path = f"{OUTPUT_DIR}/{filename}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON guardado en {json_path}")
            save_markdown(data, label, filename)

            return data

        except Exception as e:
            last_error = e
            is_transient = _is_transient_error(e)
            tipo = "transitorio" if is_transient else "determinista"
            print(f"⚠️  Error {tipo} en {label} (intento {attempt}): {type(e).__name__}: {e}")

            if is_transient:
                if transient_count >= TRANSIENT_BUDGET:
                    print(f"❌ Presupuesto de reintentos transitorios agotado ({TRANSIENT_BUDGET}).")
                    break
                transient_count += 1
                delay = TRANSIENT_BASE_DELAY * (2 ** (transient_count - 1))
                print(f"⏳ Reintento transitorio {transient_count}/{TRANSIENT_BUDGET} en {delay}s...")
                monitor_agent_retry(label, attempt + 1, max_intentos, delay)
                time.sleep(delay)
            else:
                if deterministic_count >= DETERMINISTIC_BUDGET:
                    print(f"❌ Reintento determinista agotado ({type(e).__name__}). Abortando sin más backoff.")
                    break
                deterministic_count += 1
                print(f"⏳ Reintento determinista {deterministic_count}/{DETERMINISTIC_BUDGET} en {DETERMINISTIC_DELAY}s...")
                monitor_agent_retry(label, attempt + 1, max_intentos, DETERMINISTIC_DELAY)
                time.sleep(DETERMINISTIC_DELAY)

    # Todos los reintentos fallaron
    monitor_agent_end(label, success=False)
    print(f"❌ {label} falló tras {attempt} intentos ({transient_count} transitorios, {deterministic_count} deterministas): {last_error}")
    raw_path = f"{OUTPUT_DIR}/{filename}_raw.txt"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(str(last_error))
    return {}




def ctx(*keys: str, results: dict) -> str:
    """
    Serializa solo los resultados indicados por clave para pasarlos como contexto.
    Sin indent para minimizar tokens enviados al LLM.
    """
    return "\n\n".join(
        f"CONTEXTO {key.upper()}:\n{json.dumps(results[key], ensure_ascii=False)}"
        for key in keys
        if results.get(key)
    )


def _slim_kic(kic: dict) -> dict:
    """KIC → Regulatorio: solo nombre, dosis, tipología y advertencias por ingrediente."""
    slim_ings = [
        {
            "ingrediente":           ing.get("ingrediente"),
            "dosis_formula_mg":      ing.get("dosis_formula_mg"),
            "dosis_formula_unidad":  ing.get("dosis_formula_unidad"),
            "tipologia":             ing.get("tipologia"),
            "advertencias_formulacion": ing.get("advertencias_formulacion"),
        }
        for ing in kic.get("fase_2_ingredientes", [])
    ]
    return {
        "ingredientes":        slim_ings,
        "riesgos_formulacion": (kic.get("fase_4_valoracion_global") or {}).get("riesgos_formulacion"),
    }


def _slim_kic_for_ft(kic: dict) -> dict:
    """KIC → Ficha Técnica: agrega función y mecanismo de acción (necesarios para la ficha)."""
    slim_ings = [
        {
            "ingrediente":                    ing.get("ingrediente"),
            "dosis_formula_mg":               ing.get("dosis_formula_mg"),
            "dosis_formula_unidad":           ing.get("dosis_formula_unidad"),
            "tipologia":                      ing.get("tipologia"),
            "funcion_tecnologica_nutricional": ing.get("funcion_tecnologica_nutricional"),
            "mecanismo_accion":               ing.get("mecanismo_accion"),
            "advertencias_formulacion":       ing.get("advertencias_formulacion"),
        }
        for ing in kic.get("fase_2_ingredientes", [])
    ]
    return {
        "ingredientes":       slim_ings,
        "valoracion_global":  kic.get("fase_4_valoracion_global"),
    }


def _slim_reg(reg: dict) -> dict:
    """Regulatorio → Claims/FT: semáforo, dictamen, condiciones y advertencias por ingrediente."""
    slim_ings = [
        {
            "nombre":                 ing.get("nombre"),
            "semaforo":               ing.get("semaforo"),
            "dictamen":               ing.get("dictamen"),
            "condiciones":            ing.get("condiciones"),
            "advertencias_etiquetado": ing.get("advertencias_etiquetado"),
        }
        for ing in reg.get("ingredientes", [])
    ]
    return {
        "clasificacion_producto": reg.get("clasificacion_producto"),
        "ingredientes":           slim_ings,
        "evaluacion_global":      reg.get("evaluacion_global"),
    }


def ctx_reg(results: dict) -> str:
    """Contexto KIC reducido para el agente Regulatorio."""
    kic = results.get("KIC")
    if not kic:
        return ""
    return f"CONTEXTO KIC:\n{json.dumps(_slim_kic(kic), ensure_ascii=False)}"


def ctx_ft(results: dict) -> str:
    """Contexto KIC + Regulatorio reducido para Ficha Técnica."""
    parts = []
    if results.get("KIC"):
        parts.append(f"CONTEXTO KIC:\n{json.dumps(_slim_kic_for_ft(results['KIC']), ensure_ascii=False)}")
    if results.get("Regulatorio"):
        parts.append(f"CONTEXTO REGULATORIO:\n{json.dumps(_slim_reg(results['Regulatorio']), ensure_ascii=False)}")
    return "\n\n".join(parts)


def ctx_claims(results: dict) -> str:
    """Contexto Regulatorio reducido para Claims."""
    reg = results.get("Regulatorio")
    if not reg:
        return ""
    return f"CONTEXTO REGULATORIO:\n{json.dumps(_slim_reg(reg), ensure_ascii=False)}"


def ctx_etiqueta(results: dict) -> str:
    """Contexto Claims + Ficha Técnica reducido para Etiqueta."""
    parts = []
    if results.get("Claims"):
        clm = results["Claims"]
        # Excluye estructura PPT, fuentes y metadata — no relevantes para etiqueta
        slim_clm = {k: clm[k] for k in (
            "parte_a_claims_regulatorios",
            "parte_b_selling_points_comerciales",
            "parte_e_advertencias_legales",
            # fallback keys
            "claims_regulatorios", "selling_points", "advertencias_legales",
        ) if k in clm}
        parts.append(f"CONTEXTO CLAIMS:\n{json.dumps(slim_clm or clm, ensure_ascii=False)}")
    if results.get("Ficha Técnica"):
        ft = results["Ficha Técnica"]
        # Excluye marco normativo, fuentes y metadata — no relevantes para texto de etiqueta
        slim_ft = {k: ft[k] for k in (
            "fase_1_identificacion",
            "fase_2_composicion",
            "fase_3_informacion_nutricional",
            "fase_4_alergenos",
            "fase_5_especificaciones_tecnicas",
            "fase_6_conservacion_vida_util",
            "fase_7_modo_empleo_advertencias",
        ) if k in ft}
        parts.append(f"CONTEXTO FICHA_TECNICA:\n{json.dumps(slim_ft or ft, ensure_ascii=False)}")
    return "\n\n".join(parts)



def _run_step(key: str, label: str, env_prefix: int,
               instructions: str, prompt: str,
               started_event: threading.Event | None = None):
    """Ejecuta un agente individual (para usar dentro de ThreadPoolExecutor)."""
    use_search = key in AGENTS_WITH_SEARCH
    prefix = AGENT_PREFIXES[env_prefix]
    agent = make_agent(label, prefix, use_search=use_search)
    # Sustituye placeholders soportados en el prompt. Usamos .replace() porque los
    # prompts contienen ejemplos JSON con llaves `{}` que romperían str.format().
    if "{search_max}" in instructions:
        instructions = instructions.replace(
            "{search_max}", str(get_search_max_queries(prefix))
        )
    agent.instructions = instructions
    t0 = time.time()
    output_model = AGENT_OUTPUT_MODELS.get(key)
    prompt_version = AGENT_PROMPT_VERSIONS.get(key)
    base_url = getattr(getattr(agent, "model", None), "base_url", None)
    sem = _get_semaphore(base_url)
    print(f"⏳ [{label}] esperando slot en endpoint ({base_url})...")
    with sem:
        if started_event is not None:
            started_event.set()
        print(f"🔓 [{label}] slot adquirido")
        data = run_agent(agent, prompt, label,
                         output_model=output_model,
                         prompt_version=prompt_version)
    elapsed = time.time() - t0
    return key, data, label, elapsed


def _collect(future, results: dict, timings: dict) -> bool:
    """Recoge el resultado de un future. Devuelve True si tuvo éxito."""
    try:
        key, data, label, elapsed = future.result()
        results[key] = data
        timings[key] = {"label": label, "elapsed": elapsed}
        return bool(data)  # {} se considera fallo
    except Exception as e:
        print(f"❌ Error recogiendo resultado: {e}")
        return False


def main(argv: list[str] | None = None):
    global OUTPUT_DIR
    args = _parse_args(argv)
    try:
        F, fuente = _load_formula(args.formula, args.formula_text)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        _sys.exit(2)

    # `run_agent` y `save_markdown` leen OUTPUT_DIR como global del módulo,
    # así que basta con reasignarlo antes de lanzar el DAG.
    OUTPUT_DIR = args.output_dir

    # Primera línea no vacía del texto se usa como etiqueta humana del run.
    titulo = next((ln.strip() for ln in F.splitlines() if ln.strip()), "fórmula")

    print(f"\n🚀 PIPELINE v2 COMPLETO — {titulo}")
    print(f"📥 Fórmula: {fuente}")
    print(f"📂 Output dir: {OUTPUT_DIR}\n")
    monitor_pipeline(f"Iniciando pipeline v2 — {titulo}")
    print_pipeline_config()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    r = {}        # resultados por clave corta
    timings = {}  # tiempos de ejecución por clave
    t_pipeline_start = time.time()

    # ── DAG con futures: cada agente arranca en cuanto sus dependencias están listas ──
    # Dependencias:
    #   KIC, Formatos, Docs Internos, QC → solo fórmula (sin dependencias)
    #   Regulatorio → KIC
    #   Ficha Técnica → KIC + Regulatorio
    #   Claims → Regulatorio
    #   Etiqueta → Claims + Ficha Técnica

    max_workers = max(1, int(os.environ.get("PIPELINE_MAX_WORKERS", "4")))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:

        # Wave 1: KIC arranca primero (path crítico → Regulatorio lo espera).
        # Los demás se lanzan solo después de que KIC haya adquirido su slot
        # en el semáforo del endpoint, garantizando que no le ganen la plaza.
        monitor_wave(1, "KIC + Formatos + Docs Internos + QC (paralelo)")
        print(f"\n{'─'*60}")
        print("  WAVE 1: KIC + Formatos + Docs Internos + QC (paralelo)")
        print(f"{'─'*60}")

        kic_slot_acquired = threading.Event()
        fut_kic = pool.submit(
            _run_step, "KIC", "Agente 1: KIC v2", 1, KIC_INSTRUCTIONS,
            f"Analiza la siguiente fórmula:\n\n{F}", kic_slot_acquired)

        # Esperar a que KIC tenga su slot (máx. 60 s por si el endpoint tarda)
        kic_slot_acquired.wait(timeout=60)

        fut_formatos = pool.submit(
            _run_step, "Formatos", "Agente 6: Formatos v2", 6, FORMATOS_INSTRUCTIONS,
            f"Propone y evalúa formatos de presentación para el siguiente producto:\n\n{F}")

        fut_docs = pool.submit(
            _run_step, "Docs Internos", "Agente 7: Docs Internos v2", 7, DOCS_INTERNOS_INSTRUCTIONS,
            f"Genera la documentación interna de producción del siguiente producto:\n\n{F}")

        fut_qc = pool.submit(
            _run_step, "QC", "Agente 8: QC v2", 8, QC_INSTRUCTIONS,
            f"Define el plan de control de calidad del siguiente producto:\n\n{F}")

        # Wave 2: Regulatorio arranca en cuanto KIC termina (sin esperar a Formatos/Docs/QC)
        kic_ok = _collect(fut_kic, r, timings)
        if not kic_ok:
            print("❌ KIC falló — es crítico para el pipeline. Abortando waves dependientes.")
        else:
            monitor_wave(2, "Regulatorio (KIC listo)")
            print(f"\n{'─'*60}")
            print("  WAVE 2: Regulatorio (KIC listo → arranca sin esperar a los demás)")
            print(f"{'─'*60}")

        fut_reg = pool.submit(
            _run_step, "Regulatorio", "Agente 2: Regulatorio v2", 2, REGULATORY_INSTRUCTIONS,
            f"Valida regulatoriamente la siguiente fórmula:\n\n{F}\n\n{ctx_reg(r)}") if kic_ok else None

        # Recoger Wave 1 restante (probablemente ya terminaron)
        _collect(fut_formatos, r, timings)
        _collect(fut_docs, r, timings)
        _collect(fut_qc, r, timings)

        # Wave 3: FT + Claims en paralelo (en cuanto Regulatorio termina)
        reg_ok = _collect(fut_reg, r, timings) if fut_reg else False
        if reg_ok:
            monitor_wave(3, "Ficha Técnica + Claims (paralelo)")
            print(f"\n{'─'*60}")
            print("  WAVE 3: Ficha Técnica + Claims (paralelo)")
            print(f"{'─'*60}")

            fut_ft = pool.submit(
                _run_step, "Ficha Técnica", "Agente 3: Ficha Técnica v2", 3, FICHA_TECNICA_INSTRUCTIONS,
                f"Genera la ficha técnica completa del siguiente producto:\n\n{F}\n\n{ctx_ft(r)}")

            fut_claims = pool.submit(
                _run_step, "Claims", "Agente 4: Claims v2", 4, CLAIMS_INSTRUCTIONS,
                f"Genera los claims regulatorios y selling points del siguiente producto:\n\n{F}\n\n{ctx_claims(r)}")

            _collect(fut_ft, r, timings)
            _collect(fut_claims, r, timings)
        else:
            print("⚠️  Regulatorio falló — saltando Ficha Técnica, Claims y Etiqueta")

        # Wave 4: Etiqueta (necesita Claims + FT)
        if r.get("Claims") and r.get("Ficha Técnica"):
            monitor_wave(4, "Etiqueta")
            print(f"\n{'─'*60}")
            print("  WAVE 4: Etiqueta")
            print(f"{'─'*60}")

            fut_etiqueta = pool.submit(
                _run_step, "Etiqueta", "Agente 5: Etiqueta v2", 5, ETIQUETA_INSTRUCTIONS,
                f"Genera el texto completo de la etiqueta del siguiente producto:\n\n{F}\n\n{ctx_etiqueta(r)}")

            _collect(fut_etiqueta, r, timings)
        else:
            print("⚠️  Claims o Ficha Técnica no disponibles — saltando Etiqueta")

    # ── Composición del informe final (sin LLM) ────────────────────────
    t_pipeline_total = time.time() - t_pipeline_start
    agent_models = {
        AGENT_PREFIXES[i]: get_agent_config(AGENT_PREFIXES[i])
        for i in range(1, 9)
    }
    compose_informe(
        F,
        f"{OUTPUT_DIR}/informe_ejecutivo.md",
        agent_models=agent_models,
        timings=timings,
        total_elapsed=t_pipeline_total,
    )

    ok = [k for k, v in r.items() if v]
    fail = [k for k in AGENT_OUTPUT_MODELS if k not in ok]

    monitor_pipeline(f"Pipeline completado — {len(ok)}/8 agentes exitosos")
    print(f"\n{'='*60}")
    print(f"  Pipeline v2 completado — {len(ok)}/8 agentes exitosos")
    if fail:
        print(f"  ⚠️  Fallaron: {', '.join(fail)}")
    print(f"  Outputs en: {OUTPUT_DIR}/")
    print(f"  Informe final: {OUTPUT_DIR}/informe_ejecutivo.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
