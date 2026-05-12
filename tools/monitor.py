"""
Monitorización en terminal del pipeline multi-agente.

Muestra mensajes en tiempo real cuando se ejecutan agentes y llamadas externas
(PubMed, DuckDuckGo, Tavily). Se activa/desactiva con MONITOR_ENABLED en .env.
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

MONITOR_ENABLED = os.getenv("MONITOR_ENABLED", "true").lower() in ("true", "1", "yes", "si")

# Colores ANSI
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"
_RED = "\033[31m"


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def monitor(category: str, message: str, color: str = _CYAN) -> None:
    """Imprime un mensaje de monitorización si está habilitado."""
    if not MONITOR_ENABLED:
        return
    ts = _timestamp()
    print(f"{_DIM}{ts}{_RESET} {color}{_BOLD}[{category}]{_RESET} {message}", file=sys.stderr, flush=True)


def monitor_agent_start(agent_name: str) -> None:
    monitor("AGENT", f"Iniciando: {agent_name}", _CYAN)


def monitor_agent_end(agent_name: str, success: bool, duration_s: float = 0) -> None:
    if success:
        dur = f" ({duration_s:.1f}s)" if duration_s else ""
        monitor("AGENT", f"Completado: {agent_name}{dur}", _GREEN)
    else:
        monitor("AGENT", f"Fallido: {agent_name}", _RED)


def monitor_agent_retry(agent_name: str, attempt: int, max_retries: int, delay: int) -> None:
    monitor("RETRY", f"{agent_name} - intento {attempt}/{max_retries} en {delay}s", _YELLOW)


def monitor_search(tool_name: str, query: str) -> None:
    q = query[:80] + "..." if len(query) > 80 else query
    monitor("SEARCH", f"{tool_name} -> \"{q}\"", _MAGENTA)


def monitor_search_result(tool_name: str, num_results: int) -> None:
    monitor("SEARCH", f"{tool_name} <- {num_results} resultado(s)", _BLUE)


def monitor_wave(wave_num: int, description: str) -> None:
    monitor("WAVE", f"Wave {wave_num}: {description}", _CYAN)


def monitor_pipeline(message: str) -> None:
    monitor("PIPELINE", message, _GREEN)
