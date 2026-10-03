"""Los tres gates que salieron del run_59.

En ese run se publicaron cuatro fragmentos en chino dentro del informe y el
agente regulatorio dictaminó sobre 40 mL cuando la fórmula suma 50. Ninguna de
las dos cosas rompía nada: por eso llegaron al PDF.
"""
import json
import pytest

from pipeline import orchestrator as orq
from pipeline.report_composer import _detectar_fuga_idioma


class TestReglaIdioma:
    def test_la_regla_menciona_los_tres_alfabetos(self):
        r = orq._REGLA_IDIOMA
        for palabra in ("castellano", "chino", "japonés", "coreano"):
            assert palabra in r

    @pytest.mark.parametrize("frag", ["接近", "反复", "ひらがな", "한글"])
    def test_cjk_se_detecta(self, frag):
        assert orq._CJK_RE.search(f"texto en castellano con {frag} dentro")

    def test_castellano_con_acentos_y_simbolos_no_se_marca(self):
        # Ni «≈», ni «µg», ni «°C», ni las tildes pueden disparar el gate.
        txt = "Sucralosa: 35 mg ≈ 700 mg/kg; 0,56 µg a 30-35 °C — validación ✅"
        assert orq._CJK_RE.search(txt) is None

    def test_valueerror_es_determinista_luego_hay_reintento(self):
        # El gate lanza ValueError a propósito: así el agente responde otra vez
        # en lugar de abortar el run.
        assert orq._is_transient_error(ValueError("Fuga de idioma")) is False


class TestMasaDeToma:
    def _canonica(self, tmp_path, ings):
        (tmp_path / "formula_canonica.json").write_text(
            json.dumps({"product_name": "X", "ingredients": ings}), encoding="utf-8")
        return str(tmp_path)

    def test_se_inyecta_la_suma_de_materia_prima(self, tmp_path):
        d = self._canonica(tmp_path, [
            {"name": "A", "raw_mg": 40270.6, "active_mg": None},
            {"name": "B", "raw_mg": 9729.4, "active_mg": 100, "active_name": "b"},
        ])
        out = orq._enriquecer_formula("FORMULA", d)
        assert "MASA DE TOMA: 50.0 g por toma (50000 mg)" in out
        assert "~50 mL" in out
        assert "AUTORITATIVO" in out

    def test_tambien_cuando_ningun_ingrediente_tiene_activo(self, tmp_path):
        # Sin activos la función salía antes por el `return F` y el volumen
        # nunca llegaba al prompt.
        d = self._canonica(tmp_path, [{"name": "A", "raw_mg": 20000}])
        out = orq._enriquecer_formula("FORMULA", d)
        assert "MASA DE TOMA: 20.0 g" in out

    def test_sin_canonica_no_toca_la_formula(self, tmp_path):
        assert orq._enriquecer_formula("FORMULA", str(tmp_path)) == "FORMULA"

    def test_raw_mg_no_numerico_no_rompe(self, tmp_path):
        d = self._canonica(tmp_path, [{"name": "A", "raw_mg": "n/d"},
                                      {"name": "B", "raw_mg": 5000}])
        assert "MASA DE TOMA: 5.0 g" in orq._enriquecer_formula("F", d)


def test_fuga_de_idioma_es_severidad_alta():
    """Un carácter ilegible publicado invalida la página, no la matiza."""
    import re, pathlib
    src = pathlib.Path(orq.__file__).parent / "report_composer.py"
    txt = src.read_text(encoding="utf-8")
    bloque = txt[txt.index("_detectar_fuga_idioma(texto_provisional)"):][:300]
    assert '"severidad": "alta"' in bloque


def test_detector_devuelve_contexto_alrededor_del_fragmento():
    frags = _detectar_fuga_idioma("un texto largo con 接近 en medio de la frase")
    assert len(frags) == 1 and "接近" in frags[0]
