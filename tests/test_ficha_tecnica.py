"""Test script for Agente 3: Ficha Técnica — CON DuckDuckGo"""

import json
import os
import re

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.tools.duckduckgo import DuckDuckGoTools
from json_repair import repair_json

from agents.legacy.ficha_tecnica_agent import FICHA_TECNICA_INSTRUCTIONS

load_dotenv()

FORMULA_EJEMPLO = """\
Inmuno Complex Pro

- Vitamina C (ác. ascórbico): 120mg (150% VRN)
- Zinc (gluconato): 10mg
- Vit. D3: 20μg
"""


def strip_markdown_json(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*\n?|\n?```\s*$", "", text.strip(), flags=re.MULTILINE)


def main():
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: ZAI_API_KEY no está definida en .env")

    print("=" * 60)
    print("  Agente 3: Ficha Técnica — Test CON DuckDuckGo")
    print("=" * 60)
    print(f"\nFórmula de entrada:\n{FORMULA_EJEMPLO}")

    agent = Agent(
        name="Ficha Técnica Agent",
        model=OpenAILike(
            id="glm-5-turbo",
            api_key=api_key,
            base_url="https://api.z.ai/api/coding/paas/v4",
            request_params={"timeout": 120},
        ),
        tools=[DuckDuckGoTools()],
        instructions=FICHA_TECNICA_INSTRUCTIONS,
        markdown=False,
    )

    print("\nEjecutando agente con web search...\n")

    response = agent.run(FORMULA_EJEMPLO)
    content = response.content
    text = strip_markdown_json(content) if isinstance(content, str) else json.dumps(content, ensure_ascii=False)

    print(text)

    os.makedirs("outputs", exist_ok=True)
    try:
        repaired = repair_json(text)
        data = json.loads(repaired)
        with open("outputs/ficha_tecnica_result.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n✅ Resultado guardado en outputs/ficha_tecnica_result.json")
    except Exception as e:
        with open("outputs/ficha_tecnica_result_raw.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n⚠️  Error al reparar JSON: {e}")
        print("⚠️  Guardado como texto en outputs/ficha_tecnica_result_raw.txt")

    if hasattr(response, "metrics") and response.metrics:
        print(f"\n📊 Tokens: {response.metrics.input_tokens} input + {response.metrics.output_tokens} output = {response.metrics.total_tokens} total")
        print(f"⏱️  Duración: {response.metrics.duration:.1f}s")


if __name__ == "__main__":
    main()
