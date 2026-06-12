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
    "Bloque 1 Discovert /Frmules per Validar/FT Formula 1 MIX 250188 (1).pdf"
)


def _parsed():
    if not PDF.exists():
        if pytest:
            pytest.skip(f"PDF de muestra no disponible: {PDF}")
    return parse_ft_pdf(str(PDF))


def test_cabecera():
    d = _parsed()
    assert d["product_name"] == "MIX 250188"
    assert "1680" in d["dosage"]
    assert d["version"] == "20260424"


def test_doce_ingredientes():
    d = _parsed()
    assert len(d["ingredients"]) == 12


def test_dosis_activa_vs_materia_prima():
    d = _parsed()
    by_code = {i["code"]: i for i in d["ingredients"]}
    # Boswellia: activo 50 (AKBA) vs materia prima 166,67.
    bos = by_code["91483"]
    assert bos["active_mg"] == 50.0
    assert round(bos["raw_mg"], 2) == 166.67
    assert bos["active_name"] == "AKBA"
    assert bos["pct_active"] == "30"


def test_b6_sobredosado_lee_valor_declarado():
    # B6: 2,26 materia prima × 80,5% = 1,82, pero declarado = 1,40 (sobredosado).
    # El parser debe leer 1,40, no calcular.
    d = _parsed()
    b6 = {i["code"]: i for i in d["ingredients"]}["5029"]
    assert b6["active_mg"] == 1.40
    assert round(b6["raw_mg"], 2) == 2.26


def test_bambu_silicio_no_silice():
    # Bambú: el nombre dice "85% Silica" pero el activo real es 39,73% Silicon → 4,00.
    d = _parsed()
    bam = {i["code"]: i for i in d["ingredients"]}["4265"]
    assert bam["active_mg"] == 4.0
    assert bam["pct_active"] == "39,73"
    assert bam["active_name"] == "Silicon"


if __name__ == "__main__":
    for fn in (test_cabecera, test_doce_ingredientes, test_dosis_activa_vs_materia_prima,
               test_b6_sobredosado_lee_valor_declarado, test_bambu_silicio_no_silice):
        fn()
        print(f"✅ {fn.__name__}")
