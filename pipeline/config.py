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


@dataclass
class AgentConfig:
    model: str
    api_key: str
    base_url: str
    temperature: float = 0.1

    def __str__(self) -> str:
        key_preview = self.api_key[:8] + "..." if self.api_key else "(no key)"
        return f"model={self.model} | base_url={self.base_url} | key={key_preview} | temperature={self.temperature}"


def get_agent_config(prefix: str) -> AgentConfig:
    """
    Devuelve la configuración de un agente.
    Prioridad: variable específica del agente → DEFAULT_* → fallbacks hardcoded.
    """
    model = (
        os.getenv(f"{prefix}_MODEL")
        or os.getenv("DEFAULT_MODEL")
        or "glm-5-turbo"
    )
    api_key = (
        os.getenv(f"{prefix}_API_KEY")
        or os.getenv("DEFAULT_API_KEY")
        or os.getenv("ZAI_API_KEY")
        or ""
    )
    base_url = (
        os.getenv(f"{prefix}_BASE_URL")
        or os.getenv("DEFAULT_BASE_URL")
        or "https://api.z.ai/api/coding/paas/v4"
    )

    if not api_key:
        raise RuntimeError(
            f"No hay API key para el agente con prefijo {prefix}. "
            f"Define {prefix}_API_KEY, DEFAULT_API_KEY o ZAI_API_KEY en .env"
        )

    temperature = float(
        os.getenv(f"{prefix}_TEMPERATURE")
        or os.getenv("DEFAULT_TEMPERATURE")
        or "0.1"
    )

    return AgentConfig(model=model, api_key=api_key, base_url=base_url,
                       temperature=temperature)


def print_pipeline_config() -> None:
    """Imprime la configuración de todos los agentes al iniciar el pipeline."""
    print("─" * 60)
    print("  Configuración del pipeline")
    print("─" * 60)
    for num, prefix in AGENT_PREFIXES.items():
        cfg = get_agent_config(prefix)
        print(f"  Agente {num} ({prefix}): {cfg}")
    print("─" * 60)
