"""
Configuración centralizada del pipeline.

Cada agente lee su modelo, base_url y api_key del .env.
Si un agente no tiene configuración propia, usa los valores DEFAULT_*.

Ejemplo en .env:
    DEFAULT_MODEL=glm-5-turbo
    DEFAULT_BASE_URL=https://api.z.ai/api/coding/paas/v4
    DEFAULT_API_KEY=sk-...

    AGENT_1_KIC_MODEL=gpt-4o
    AGENT_1_KIC_BASE_URL=https://api.openai.com/v1
    AGENT_1_KIC_API_KEY=sk-...
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()
# Defaults del pipeline
DEFAULT_MODEL_FALLBACK = "glm-5-turbo"
DEFAULT_BASE_URL_FALLBACK = "https://api.z.ai/api/coding/paas/v4"
DEFAULT_TEMPERATURE_FALLBACK = 0.1
DEFAULT_SEARCH_MAX_FALLBACK = 5

# Prefijos de cada agente (en orden del pipeline)
AGENT_PREFIXES = {
    1: "AGENT_1_KIC",
    2: "AGENT_2_REG",
    3: "AGENT_3_FT",
    4: "AGENT_4_CLAIMS",
    5: "AGENT_5_ETIQUETA",
    6: "AGENT_6_FORMATOS",
    7: "AGENT_7_DOCS",
    8: "AGENT_8_QC",
}
# Alias “clave lógica de agente” -> prefijo de variables de entorno.
# Útil para frontends que quieran configurar cada agente individualmente.
AGENT_KEY_TO_PREFIX = {
    "KIC": AGENT_PREFIXES[1],
    "Regulatorio": AGENT_PREFIXES[2],
    "Ficha Técnica": AGENT_PREFIXES[3],
    "Claims": AGENT_PREFIXES[4],
    "Etiqueta": AGENT_PREFIXES[5],
    "Formatos": AGENT_PREFIXES[6],
    "Docs Internos": AGENT_PREFIXES[7],
    "QC": AGENT_PREFIXES[8],
}

PROVIDER_API_KEY_ENV_VARS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "ZAI_API_KEY",  # legacy / backwards compatibility
)

_SUPPORTED_AGENT_OVERRIDE_FIELDS = ("MODEL", "BASE_URL", "API_KEY", "TEMPERATURE")


@dataclass
class AgentConfig:
    model: str
    api_key: str
    base_url: str
    temperature: float = 0.1

    def __str__(self) -> str:
        key_preview = self.api_key[:8] + "..." if self.api_key else "(no key)"
        return f"model={self.model} | base_url={self.base_url} | key={key_preview} | temperature={self.temperature}"

def _first_non_empty(*values: str | None) -> str:
    for v in values:
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return ""


def _infer_provider_api_key_env(base_url: str, model: str) -> str | None:
    """Infiero qué variable de API key conviene usar según endpoint/modelo."""
    b = (base_url or "").lower()
    m = (model or "").lower()

    if "openrouter.ai" in b:
        return "OPENROUTER_API_KEY"
    if "api.openai.com" in b:
        return "OPENAI_API_KEY"
    if "anthropic.com" in b:
        return "ANTHROPIC_API_KEY"
    if "generativelanguage.googleapis.com" in b or "googleapis.com" in b:
        return "GEMINI_API_KEY"
    if "api.z.ai" in b:
        return "ZAI_API_KEY"

    # Heurística por nombre de modelo si el base_url no ayuda.
    if m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3"):
        return "OPENAI_API_KEY"
    if "claude" in m:
        return "ANTHROPIC_API_KEY"
    if "gemini" in m:
        return "GEMINI_API_KEY"
    return None


def _resolve_api_key(prefix: str, base_url: str, model: str) -> str:
    provider_env = _infer_provider_api_key_env(base_url, model)
    provider_value = os.getenv(provider_env) if provider_env else None

    # Prioridad:
    # 1) Variable específica del agente
    # 2) DEFAULT_API_KEY
    # 3) Variable de proveedor inferida por endpoint/modelo
    # 4) Cualquier variable estándar de proveedor
    return _first_non_empty(
        os.getenv(f"{prefix}_API_KEY"),
        os.getenv("DEFAULT_API_KEY"),
        provider_value,
        *(os.getenv(name) for name in PROVIDER_API_KEY_ENV_VARS),
    )


def get_search_max_queries(prefix: str | None = None) -> int:
    """Devuelve el tope de búsquedas web/PubMed que se le indica al agente.

    Prioridad:
      1) AGENT_<prefix>_SEARCH_MAX (si se pasa prefix)
      2) SEARCH_MAX_QUERIES (global)
      3) DEFAULT_SEARCH_MAX_FALLBACK
    """
    candidates = []
    if prefix:
        candidates.append(os.getenv(f"{prefix}_SEARCH_MAX"))
    candidates.append(os.getenv("SEARCH_MAX_QUERIES"))
    raw = _first_non_empty(*candidates)
    if not raw:
        return DEFAULT_SEARCH_MAX_FALLBACK
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"Valor inválido para tope de búsquedas ({prefix or 'global'}): '{raw}'. "
            f"Debe ser un entero ≥ 0."
        ) from exc
    if value < 0:
        raise RuntimeError(
            f"El tope de búsquedas no puede ser negativo (recibido {value})."
        )
    return value


def _resolve_temperature(prefix: str) -> float:
    raw = _first_non_empty(
        os.getenv(f"{prefix}_TEMPERATURE"),
        os.getenv("DEFAULT_TEMPERATURE"),
    )
    if not raw:
        return DEFAULT_TEMPERATURE_FALLBACK
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"Temperatura inválida para {prefix}: '{raw}'. "
            f"Define {prefix}_TEMPERATURE o DEFAULT_TEMPERATURE con un número."
        ) from exc


def get_agent_config(prefix: str) -> AgentConfig:
    """
    Devuelve la configuración de un agente.
    Prioridad: variable específica del agente → DEFAULT_* → fallbacks hardcoded.
    """
    model = (
        os.getenv(f"{prefix}_MODEL")
        or os.getenv("DEFAULT_MODEL")
        or DEFAULT_MODEL_FALLBACK
    )
    base_url = (
        os.getenv(f"{prefix}_BASE_URL")
        or os.getenv("DEFAULT_BASE_URL")
        or DEFAULT_BASE_URL_FALLBACK
    )
    api_key = _resolve_api_key(prefix=prefix, base_url=base_url, model=model)

    if not api_key:
        raise RuntimeError(
            f"No hay API key para el agente con prefijo {prefix}. "
            f"Define {prefix}_API_KEY, DEFAULT_API_KEY o una API key de proveedor "
            f"(OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, ZAI_API_KEY) en .env"
        )

    temperature = _resolve_temperature(prefix)

    return AgentConfig(model=model, api_key=api_key, base_url=base_url,
                       temperature=temperature)


def build_agent_env_overrides(agent_settings: dict[str, dict[str, object]] | None) -> dict[str, str]:
    """Convierte settings por agente en variables AGENT_*_X para inyectar en env.

    Soporta claves de entrada por:
    - nombre lógico de agente (ej: "KIC", "Claims", "Ficha Técnica"), o
    - prefijo directo (ej: "AGENT_1_KIC").
    """
    env_overrides: dict[str, str] = {}
    if not agent_settings:
        return env_overrides

    for agent_key, settings in agent_settings.items():
        if not isinstance(settings, dict):
            continue
        prefix = AGENT_KEY_TO_PREFIX.get(agent_key, agent_key if str(agent_key).startswith("AGENT_") else None)
        if not prefix:
            continue

        for field in _SUPPORTED_AGENT_OVERRIDE_FIELDS:
            raw = settings.get(field) or settings.get(field.lower())
            if raw is None:
                continue
            value = str(raw).strip()
            if not value:
                continue
            env_overrides[f"{prefix}_{field}"] = value

    return env_overrides

def print_pipeline_config() -> None:
    """Imprime la configuración de todos los agentes al iniciar el pipeline."""
    print("─" * 60)
    print("  Configuración del pipeline")
    print("─" * 60)
    for num, prefix in AGENT_PREFIXES.items():
        cfg = get_agent_config(prefix)
        print(f"  Agente {num} ({prefix}): {cfg}")
    print("─" * 60)
