"""Parser del FT PDF de Umbrella (hoja de fórmula con dosis activa).

Xavier entrega la fórmula como un PDF tipo `FT Formula <MIX>.pdf` cuyo nombre de
ingrediente codifica el activo y su %, y que trae DOS columnas de dosis por dosis
diaria:

    Code  Ingredient (", X% Activo")  mg_activo  %mezcla  g_box  kg_prod  mg_materia_prima  L.M.(g)  L.M.(Kg)

- `mg_activo` (1ª columna numérica, "Main Active or Excipient") = dosis de ACTIVO
  aportado → PÚBLICA (bloques cliente).
- `mg_materia_prima` (5ª columna numérica) = dosis de materia prima → CONFIDENCIAL
  (solo bloques internos de producción/calidad).

El activo NO siempre es materia prima × %: p. ej. la vitamina B6 lleva sobredosado
(2,26mg materia prima → 1,40mg declarados). Por eso se lee del PDF, no se calcula.

Requiere `pypdfium2` (ya en el entorno).
"""

from __future__ import annotations

import re

import pypdfium2 as pdfium

# Un número con coma decimal y, opcionalmente, puntos de millar: "2,26", "24.900,79".
_NUM = r"\d{1,3}(?:\.\d{3})*,\d+"
# Fila de ingrediente: código + nombre + 7 columnas numéricas.
_ROW = re.compile(rf"^(\d{{3,6}})\s+(.*?)\s+((?:{_NUM}\s+){{6}}{_NUM})\s*$")
# Activo dentro del nombre: "..., 80,5% Vit. B6" / "..., <95 % Curcuminoids".
_ACTIVE = re.compile(r",\s*(<?\s*[\d.,]+)\s*%\s*(.+)$")


def _to_float(s: str) -> float:
    """'24.900,79' -> 24900.79 (punto de millar europeo, coma decimal)."""
    return float(s.replace(".", "").replace(",", "."))


def _extract_text(source) -> str:
    """Texto plano del PDF. `source` puede ser una ruta o bytes."""
    pdf = pdfium.PdfDocument(source)
    try:
        return pdf[0].get_textpage().get_text_range()
    finally:
        pdf.close()


def _parse_header(text: str) -> dict:
    """Nombre de producto, dosis y versión de la cabecera del PDF."""
    product_name, dosage, version = "", "", ""
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^Mix\s+(.+)$", line, re.IGNORECASE)
        if m and not product_name:
            # "Mix 250188 1" -> "MIX 250188" (descarta el contador final).
            product_name = "MIX " + m.group(1).split()[0]
        m = re.match(r"^Dosage:\s*(.+)$", line, re.IGNORECASE)
        if m and not dosage:
            dosage = m.group(1).strip()
        m = re.match(r"^Version:\s*(\S+)", line, re.IGNORECASE)
        if m and not version:
            version = m.group(1).strip()
    return {"product_name": product_name, "dosage": dosage, "version": version}


def parse_ft_pdf(source) -> dict:
    """Parsea el FT PDF. `source` es una ruta (str) o los bytes del PDF.

    Devuelve::

        {
          "product_name": "MIX 250188",
          "dosage": "1680 mg/ 3 Cap \"00\" White",
          "version": "20260424",
          "ingredients": [
            {"code": "91483", "name": "Boswellia serrata Ext., 30% AKBA",
             "active_name": "AKBA", "pct_active": "30",
             "active_mg": 50.0, "raw_mg": 166.67, "unit": "mg"},
            ...
          ],
        }

    Lanza `ValueError` si no encuentra ninguna fila de ingrediente.
    """
    text = _extract_text(source)
    result = _parse_header(text)
    ingredients: list[dict] = []

    for line in text.splitlines():
        m = _ROW.match(line.strip())
        if not m:
            continue
        code, name, nums = m.groups()
        cols = nums.split()
        active_mg = _to_float(cols[0])
        raw_mg = _to_float(cols[4])

        am = _ACTIVE.search(name)
        pct_active = am.group(1).replace("<", "").strip() if am else ""
        active_name = am.group(2).strip() if am else ""

        # El PDF redondea la columna de activo a 2 decimales, así que una
        # microdosis (B12: 0,1% → 0,004 mg) llega como 0,00. Recupérala desde
        # materia prima × %. No afecta a los sobredosados (B6: 1,40 ≠ 0).
        if active_mg == 0 and pct_active and raw_mg:
            try:
                active_mg = raw_mg * float(pct_active.replace(",", ".")) / 100.0
            except ValueError:
                pass

        ingredients.append({
            "code": code,
            "name": name.strip(),
            "active_name": active_name,
            "pct_active": pct_active,
            "active_mg": active_mg,
            "raw_mg": raw_mg,
            "unit": "mg",
        })

    if not ingredients:
        raise ValueError("No se reconoció ninguna fila de ingrediente en el PDF.")

    result["ingredients"] = ingredients
    return result
