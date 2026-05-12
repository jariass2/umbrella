"""Test KIC Agent sin web search — valida conexion LLM"""

import json
import os
import re
import sys

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from json_repair import repair_json

from agents.legacy.kic_agent import KIC_INSTRUCTIONS

load_dotenv()

FORMULA_EJEMPLO = """\
Inmuno Complex Pro

- Vitamina C (ác. ascórbico): 120mg (150% VRN)
- Zinc (gluconato): 10mg
- Vit. D3: 20μg
"""


def strip_markdown_json(text: str) -> str:
    """Remove ```json ... ``` fences from LLM output."""
    return re.sub(r"^```(?:json)?\s*\n?|\n?```\s*$", "", text.strip(), flags=re.MULTILINE)


def main():
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        sys.exit("ERROR: ZAI_API_KEY no está definida en .env")

    print("=" * 60)
    print("  Agente 1: KIC — Test SIN web search")
    print("=" * 60)

    agent = Agent(
        name="KIC Analysis Agent",
        model=OpenAILike(
            id="glm-5-turbo",
            api_key=api_key,
            base_url="https://api.z.ai/api/coding/paas/v4",
            request_params={"timeout": 120},
        ),
        instructions=KIC_INSTRUCTIONS,
        markdown=False,
    )

    print("\nEjecutando agente (sin web search)...\n")

    response = agent.run(FORMULA_EJEMPLO)
    content = response.content
    text = strip_markdown_json(content) if isinstance(content, str) else json.dumps(content, ensure_ascii=False)

    # Print raw output
    print(text)

    # Repair JSON and save
    os.makedirs("outputs", exist_ok=True)
    try:
        repaired = repair_json(text)
        data = json.loads(repaired)
        with open("outputs/kic_result.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n✅ Resultado estructurado guardado en outputs/kic_result.json")
    except Exception as e:
        with open("outputs/kic_result_raw.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n⚠️  No se pudo reparar JSON: {e}")
        print("⚠️  Guardado como texto en outputs/kic_result_raw.txt")

    # Print usage metrics if available
    if hasattr(response, "metrics") and response.metrics:
        print(f"\n📊 Tokens: {response.metrics}")


if __name__ == "__main__":
    main()
