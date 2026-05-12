"""
Genera ficheros .md a partir de los JSON existentes en outputs/v2/.
Ejecutar una sola vez para backfill.
"""

import json
import os

OUTPUT_DIR = "outputs/v2"

LABELS = {
    "agente_1_kic_v2": "Agente 1: KIC v2",
    "agente_2_regulatorio_v2": "Agente 2: Regulatorio v2",
    "agente_3_ficha_técnica_v2": "Agente 3: Ficha Técnica v2",
}


def _to_md(value, depth: int = 0) -> str:
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
    path = f"{OUTPUT_DIR}/{filename_base}.md"
    lines = [f"# {label}\n"]

    fuentes = data.pop("fuentes_consultadas", None)
    lines.append(_to_md(data))

    if fuentes:
        lines.append("\n---\n## Fuentes consultadas\n")
        for f in fuentes:
            fid = f.get("id", "")
            nombre = f.get("fuente", "")
            url = f.get("url", "")
            tipo = f.get("tipo", "")
            url_str = f" — [{url}]({url})" if url else ""
            lines.append(f"[{fid}] **{nombre}**{url_str} _{tipo}_")

    if fuentes is not None:
        data["fuentes_consultadas"] = fuentes

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ {path}")


for base, label in LABELS.items():
    json_path = f"{OUTPUT_DIR}/{base}.json"
    if os.path.exists(json_path):
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        save_markdown(data, label, base)
    else:
        print(f"⚠️  No encontrado: {json_path}")
