"""Precios de OpenRouter por modelo, para estimar el coste de cada agente.

Tarifas en USD por millón de tokens (entrada, salida), consultadas en el
catálogo de OpenRouter el 2026-10-02. Si cambian, se actualiza esta tabla:
el coste del informe se calcula con ella a partir de los tokens que guarda
`_trazabilidad`.
"""

PRICES_USD_PER_M: dict[str, tuple[float, float]] = {
    "anthropic/claude-opus-5.5": (4.0, 20.0),
    "anthropic/claude-sonnet-5.5": (2.0, 10.0),
    "anthropic/claude-haiku-4.5": (1.0, 5.0),
    "google/gemini-3.5-flash": (1.5, 9.0),
    "google/gemini-3.8-flash": (0.75, 3.75),
    "google/gemini-3.1-flash-lite": (0.25, 1.5),
    "openai/gpt-5.4-mini": (0.75, 4.5),
    "openai/gpt-5.6-luna": (0.2, 1.2),
    "mistralai/mistral-large-2512": (0.5, 1.5),
    "qwen/qwen3.6-plus": (0.33, 1.95),
    "deepseek/deepseek-v4-pro": (0.21, 0.42),
    "minimax/minimax-m3": (0.3, 1.2),
}


def agent_cost_usd(model: str | None, input_tokens: int, output_tokens: int) -> float | None:
    """Coste en USD de una llamada, o None si el modelo no está en la tabla."""
    price = PRICES_USD_PER_M.get(model or "")
    if price is None:
        return None
    return (input_tokens * price[0] + output_tokens * price[1]) / 1_000_000
