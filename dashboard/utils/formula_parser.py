"""Convierte filas estructuradas de ingredientes al formato de texto del pipeline."""

from __future__ import annotations

VALID_UNITS = ["mg", "g", "µg", "mcg", "% VRN", "UI"]


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
    try:
        float(dosage.replace(",", "."))
    except (ValueError, AttributeError):
        return f"Dosis inválida: '{dosage}'"
    if unit not in VALID_UNITS:
        return f"Unidad no reconocida: '{unit}'"
    return None
