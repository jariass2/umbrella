"""Convierte filas estructuradas de ingredientes al formato de texto del pipeline."""

from __future__ import annotations
import re

VALID_UNITS = ["mg", "g", "µg", "mcg", "% VRN", "UI"]

MAX_PRODUCT_NAME_LEN = 200
MAX_INGREDIENT_NAME_LEN = 120
MAX_INGREDIENTS = 50
MAX_DOSAGE_LEN = 20


def parse_formula(formula_text: str) -> tuple[str, list[dict]]:
    """Parsea el texto de fórmula devolviendo (product_name, ingredients)."""
    lines = formula_text.strip().splitlines()
    product_name = lines[0].strip() if lines else ""
    ingredients = []
    for line in lines[1:]:
        line = line.strip()
        if not line.startswith("- "):
            continue
        line = line[2:]
        # Extraer notas entre paréntesis al final
        notes = ""
        m = re.search(r'\(([^)]+)\)\s*$', line)
        if m:
            notes = m.group(1)
            line = line[:m.start()].strip()
        if ":" not in line:
            continue
        name, rest = line.rsplit(":", 1)  # rsplit: colons inside names like "(1:5)" don't break the split
        rest = rest.strip()
        # Detectar unidad (de mayor a menor longitud para evitar coincidencias parciales)
        unit = "mg"
        dosage = rest
        for u in sorted(VALID_UNITS, key=len, reverse=True):
            if rest.endswith(u):
                dosage = rest[:-len(u)].strip()
                unit = u
                break
        else:
            # fallback: separar número de texto
            fm = re.match(r'^([0-9.,]+)\s*(.*)$', rest)
            if fm:
                dosage, unit = fm.group(1), fm.group(2).strip() or "mg"
        ingredients.append({"name": name.strip(), "dosage": dosage, "unit": unit, "notes": notes})
    return product_name, ingredients


def rows_to_formula(product_name: str, ingredients: list[dict]) -> str:
    """Convierte filas estructuradas al texto que espera el pipeline.

    Cada ingrediente es un dict con keys: name, dosage, unit.
    Opcionalmente puede incluir: notes.
    """
    lines = [product_name, ""]
    for ing in ingredients:
        line = f"- {ing['name']}: {ing['dosage']}{ing['unit']}"
        if ing.get("notes"):
            line += f" ({ing['notes']})"
        lines.append(line)
    return "\n".join(lines)


def validate_ingredient(name: str, dosage: str, unit: str) -> str | None:
    """Valida un ingrediente. Devuelve mensaje de error o None si es válido."""
    if not name.strip():
        return "Nombre vacío"
    if len(name) > MAX_INGREDIENT_NAME_LEN:
        return f"Nombre demasiado largo (máx. {MAX_INGREDIENT_NAME_LEN})"
    if len(dosage or "") > MAX_DOSAGE_LEN:
        return f"Dosis demasiado larga (máx. {MAX_DOSAGE_LEN} caracteres)"
    try:
        float(dosage.replace(",", "."))
    except (ValueError, AttributeError):
        return f"Dosis inválida: '{dosage}'"
    if unit not in VALID_UNITS:
        return f"Unidad no reconocida: '{unit}'"
    return None
