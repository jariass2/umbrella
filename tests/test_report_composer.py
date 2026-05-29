"""Invariantes de `report_composer.py` tras el refactor a 6 bloques (Fase 6a).

Garantiza que el informe NO vuelve a repetir contenido (feedback Xavier
2026-05-29: "Repetim masses coses"):

- El informe tiene los 6 bloques de Xavier, en orden.
- La tabla maestra de ingredientes aparece UNA sola vez (antes 4-5×).
- La tabla nutricional aparece como mucho una vez (antes 3×).
- No se cuela el bug del doble porcentaje ('%%').

Usa los JSON reales de `outputs/v2/` como fixture. Si no existen, se omite.

Uso:
    python -m pytest tests/test_report_composer.py -v
"""

import sys
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None  # type: ignore[assignment]

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.report_composer import compose_informe, fmt_portfolio  # noqa: E402

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs" / "v2"

BLOQUES_ESPERADOS = [
    "## 1. Fórmula Cuantitativa",
    "## 2. Ficha Técnica",
    "## 3. Información de Marketing",
    "## 4. Documentación Interna de Producción",
    "## 5. Plan de Calidad",
    "## 6. Portfolio recomendado",
]


def _informe(tmp_path) -> str:
    if not (OUTPUTS_DIR / "agente_1_kic_v2.json").exists():
        if pytest:
            pytest.skip("No hay outputs/v2 — ejecuta el pipeline primero")
    out = tmp_path / "informe.md"
    compose_informe("Producto de prueba\n\n- Ingrediente: 1mg",
                    str(out), output_dir=str(OUTPUTS_DIR))
    return out.read_text(encoding="utf-8")


def test_seis_bloques_en_orden(tmp_path):
    texto = _informe(tmp_path)
    posiciones = [texto.find(b) for b in BLOQUES_ESPERADOS]
    assert all(p != -1 for p in posiciones), "Falta algún bloque del índice"
    assert posiciones == sorted(posiciones), "Los bloques no están en orden"


def test_tabla_ingredientes_una_sola_vez(tmp_path):
    texto = _informe(tmp_path)
    # Cabecera única de la tabla maestra.
    assert texto.count("Biodisponibilidad | Reg.") == 1
    # La cabecera de la antigua tabla KIC ('Tipología') ya no debe existir.
    assert "Tipología" not in texto


def test_nutricional_no_se_repite(tmp_path):
    texto = _informe(tmp_path)
    # Como mucho una tabla nutricional (la canónica en Ficha Técnica).
    assert texto.count("| Nutriente | Por dosis | % VRN*") <= 1


def test_sin_doble_porcentaje(tmp_path):
    texto = _informe(tmp_path)
    assert "%%" not in texto


def test_ficha_tecnica_seis_secciones(tmp_path):
    texto = _informe(tmp_path)
    # Bloque 2 con el formato Umbrella de 6 secciones.
    for marca in [
        "### 1 · Identificación y claims activos",
        "### 2 · Ingredientes (por orden de peso)",
        "### 3 · Información nutricional",
        "### 4 · Identificación y especificaciones",
        "### 5 · Alérgenos y aptitud dietética",
        "### 6 · Datos de producto y conservación",
    ]:
        assert marca in texto, f"Falta sección FT: {marca}"


def test_ficha_tecnica_cabecera_fabricante(tmp_path):
    texto = _informe(tmp_path)
    # Cabecera corporativa fija (plantilla, no inventada por el LLM).
    assert "Umbrella F&FI, S.L." in texto
    assert "RGSEAA 26.020214/B" in texto
    # Las 14 entradas del Anexo II de alérgenos.
    assert texto.count("| Verificar |") == 14


def test_vida_util_sin_meses_duplicado(tmp_path):
    texto = _informe(tmp_path)
    assert "meses meses" not in texto


def test_etiqueta_layout_caras(tmp_path):
    texto = _informe(tmp_path)
    # Layout de Xavier: cara frontal + caras laterales con obligatorio/opcional.
    assert "#### Cara frontal" in texto
    assert "#### Caras laterales" in texto
    assert "**Obligatorio:**" in texto
    assert "**Opcional:**" in texto
    assert "Logo Ecoembes" in texto


def test_etiqueta_bilingue(tmp_path):
    texto = _informe(tmp_path)
    assert "Versión en español (ES)" in texto
    assert "Versión en inglés (EN)" in texto
    # Mención legal en ambos idiomas.
    assert "**Complemento alimenticio**" in texto
    assert "**Food supplement**" in texto


def test_portfolio_render():
    sample = {
        "fase_1_posicionamiento": {"producto_ancla": "X", "categoria": "Y", "propuesta_valor": "Z"},
        "fase_2_extensiones_linea": [{"nombre": "Ext1", "diferencia_vs_ancla": "doble dosis",
                                      "ingredientes_clave": ["a", "b"], "formato_sugerido": "Stick",
                                      "segmento_objetivo": "Senior"}],
        "fase_3_productos_complementarios": [{"nombre": "Comp1", "sinergia_con_ancla": "rutina",
                                              "ingredientes_clave": ["c"], "formato_sugerido": "Cápsula",
                                              "segmento_objetivo": "Deportista"}],
        "fase_4_gama_recomendada": {"secuencia_lanzamiento": ["1º: ancla"], "justificacion": "porque sí"},
        "fuentes_consultadas": [],
    }
    out = "\n".join(fmt_portfolio(sample))
    assert "Producto ancla:** X" in out
    assert "### Extensiones de línea" in out
    assert "### Productos complementarios" in out
    assert "### Gama recomendada (roadmap)" in out
    assert "Ext1" in out and "Comp1" in out


def test_bloque6_fallback_sin_portfolio(tmp_path):
    # Sin JSON de portfolio (outputs/v2 no lo tiene aún), Bloque 6 muestra el aviso.
    texto = _informe(tmp_path)
    assert "## 6. Portfolio recomendado" in texto
    assert "Agente 9" in texto  # mensaje de pendiente


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for fn in (test_seis_bloques_en_orden, test_tabla_ingredientes_una_sola_vez,
                   test_nutricional_no_se_repite, test_sin_doble_porcentaje,
                   test_ficha_tecnica_seis_secciones, test_ficha_tecnica_cabecera_fabricante,
                   test_vida_util_sin_meses_duplicado, test_etiqueta_layout_caras,
                   test_etiqueta_bilingue, test_bloque6_fallback_sin_portfolio):
            fn(tmp)
            print(f"✅ {fn.__name__}")
        test_portfolio_render()
        print("✅ test_portfolio_render")
