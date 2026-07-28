"""Tests del parser del FT PDF (`dashboard/utils/ft_pdf_parser.py`).

Usa el PDF de muestra de Xavier en Google Drive como fixture. Si no está
disponible (otra máquina, sin sincronizar), los tests se omiten — el PDF NO se
commitea porque contiene la fórmula confidencial.

Uso:
    python -m pytest tests/test_ft_pdf_parser.py -v
"""

import sys
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None  # type: ignore[assignment]

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard.utils.ft_pdf_parser import parse_ft_pdf  # noqa: E402

PDF = Path(
    "/Users/jordiariassantaella/Library/CloudStorage/"
    "GoogleDrive-jariass2@gmail.com/Mi unidad/Consulting/Umbrella Group/"
    "Bloque 1 Discovert /Formules per Validar/FT Formula 4 MIX 260047.pdf"
)


def _parsed():
    if not PDF.exists():
        if pytest:
            pytest.skip(f"PDF de muestra no disponible: {PDF}")
    return parse_ft_pdf(str(PDF))


def test_cabecera():
    d = _parsed()
    assert d["product_name"] == "MIX 260047"
    assert d["dosage"] == '500 mg / Capsule "0"'
    assert d["version"] == "20260513"


def test_dieciocho_ingredientes_con_codigo():
    d = _parsed()
    assert len(d["ingredients"]) == 18
    assert all(i["code"] for i in d["ingredients"])
    assert len({i["code"] for i in d["ingredients"]}) == 18


def test_dosis_activa_vs_materia_prima():
    d = _parsed()
    by_code = {i["code"]: i for i in d["ingredients"]}
    # Boswellia: activo 4,829 (AKBA) vs materia prima 16,1.
    bos = by_code["91483"]
    assert bos["active_mg"] == 4.829
    assert bos["raw_mg"] == 16.1
    assert bos["active_name"] == "AKBA"
    assert bos["pct_active"] == "30"


def test_microdosis_y_estandarizados_se_parsean():
    d = _parsed()
    by_code = {i["code"]: i for i in d["ingredients"]}
    # D3 is recovered from raw dose × 0,25% because the PDF rounds it to 0,00.
    d3 = by_code["5067"]
    assert d3["active_mg"] == 0.003
    assert d3["raw_mg"] == 1.3
    # Silicon uses the explicit 39,73% active declaration, not the 85% silica.
    silicon = by_code["4265"]
    assert silicon["active_mg"] == 16.635
    assert silicon["pct_active"] == "39,73"
    assert silicon["active_name"] == "Silicon"


def test_todos_los_registros_conservan_esquema():
    d = _parsed()
    required = {"code", "name", "active_name", "pct_active", "active_mg", "raw_mg", "unit"}
    assert all(required <= set(i) for i in d["ingredients"])
    assert all(i["unit"] == "mg" for i in d["ingredients"])


if __name__ == "__main__":
    for fn in (test_cabecera, test_doce_ingredientes, test_dosis_activa_vs_materia_prima,
               test_b6_sobredosado_lee_valor_declarado, test_bambu_silicio_no_silice):
        fn()
        print(f"✅ {fn.__name__}")
