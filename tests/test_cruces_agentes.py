"""Controles cruzados entre agentes y registro de avisos.

El pipeline encadena KIC → Regulatorio → Ficha Técnica → Claims → Etiqueta, y
cada agente ingiere el JSON del anterior como verdad. Una invención en el primer
eslabón llega al informe repetida cuatro veces, y esa unanimidad es justo lo que
la hace parecer fiable al revisar. Estos tests fijan los cruces deterministas
que la detectan, y el registro de avisos que hace que se vea.

Uso:
    python -m pytest tests/test_cruces_agentes.py -v
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import avisos as A
from pipeline.report_composer import (
    _cruce_claims_regulatorio,
    _cruce_dosis_kic_canonica,
    _cruce_etiqueta_formula,
    _cruce_vrn_etiqueta,
    _num_pct,
    _trocear_lista,
)


# ── avisos.py ──────────────────────────────────────────────────────────

def test_avisos_persisten_y_deduplican():
    with tempfile.TemporaryDirectory() as d:
        A.registrar(d, "Origen", "mensaje", "alta")
        A.registrar(d, "Origen", "mensaje", "alta")   # mismo par → uno solo
        A.registrar(d, "Otro", "otro mensaje", "info")
        got = A.cargar(d)
        assert len(got) == 2
        # La severidad alta va primero: quien mira la lista tiene que ver antes
        # lo que invalida una cifra que lo que solo la matiza.
        assert got[0]["severidad"] == "alta"
        assert A.resumen(got) == {"alta": 1, "media": 0, "info": 1}


def test_avisos_limpiar_borra_el_run_anterior():
    with tempfile.TemporaryDirectory() as d:
        A.registrar(d, "Origen", "viejo", "media")
        A.limpiar(d)
        assert A.cargar(d) == []


def test_avisos_nunca_lanza_con_directorio_inexistente():
    A.registrar("/no/existe/en/ningun/sitio", "Origen", "m", "alta")
    assert A.cargar("/no/existe/en/ningun/sitio") == []


# ── utilidades ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("txt,esperado", [
    ("50%", 50.0), ("0,8 %", 0.8), ("12.5 %", 12.5),
    ("N/A — sin VRN", None), (None, None), ("", None), ("16 mg", None),
])
def test_num_pct(txt, esperado):
    assert _num_pct(txt) == esperado


# ── cruce dosis KIC ↔ ficha canónica ───────────────────────────────────

_CANON = [{"name": "Vitamina B6", "active_mg": 0.7, "raw_mg": 1.22}]


def test_dosis_acepta_activo_y_materia_prima():
    """KIC unas veces reporta materia prima y otras activo. Ambas son legítimas."""
    for mg in (0.7, 1.22):
        kic = [{"ingrediente": "Vitamina B6", "dosis_formula_mg": mg}]
        assert _cruce_dosis_kic_canonica(kic, _CANON) == []


def test_dosis_marca_una_tercera_cifra():
    kic = [{"ingrediente": "Vitamina B6", "dosis_formula_mg": 3.5}]
    out = _cruce_dosis_kic_canonica(kic, _CANON)
    assert len(out) == 1 and out[0]["severidad"] == "alta"


# ── cruce Claims ↔ Regulatorio ─────────────────────────────────────────

def test_claim_sobre_ingrediente_no_conforme():
    reg = {"ingredientes": [
        {"nombre": "Sucralosa", "semaforo": "❌", "dictamen": "Supera el límite."}]}
    clm = {"parte_a_claims_regulatorios": {"claims_por_ingrediente": [
        {"ingrediente": "Sucralosa",
         "claims": [{"texto_claim": "x", "aplica_a_formula": True}]}]}}
    out = _cruce_claims_regulatorio(clm, reg)
    assert len(out) == 1 and out[0]["severidad"] == "alta"


def test_claim_no_aplicado_no_avisa():
    """Un claim listado pero marcado como no aplicable no contradice a nadie."""
    reg = {"ingredientes": [
        {"nombre": "Sucralosa", "semaforo": "❌", "dictamen": "Supera el límite."}]}
    clm = {"parte_a_claims_regulatorios": {"claims_por_ingrediente": [
        {"ingrediente": "Sucralosa",
         "claims": [{"texto_claim": "x", "aplica_a_formula": False}]}]}}
    assert _cruce_claims_regulatorio(clm, reg) == []


# ── cruce Etiqueta ↔ fórmula ───────────────────────────────────────────

_LISTA = ("Ingredientes: Agua; Taurina; Cafeína anhidra; "
          "Sorbato potásico (E 202, conservante); L-Citrulina.")


def test_etiqueta_no_marca_lo_que_esta_declarado():
    kic = [{"ingrediente": n} for n in
           ("Taurina", "Cafeína anhidra", "Sorbato potásico (E202)", "Agua")]
    assert _cruce_etiqueta_formula({"fase_4_lista_ingredientes_completa": _LISTA},
                                   kic, None) == []


def test_etiqueta_marca_el_ingrediente_ausente():
    kic = [{"ingrediente": "Taurina"}, {"ingrediente": "Beta-Alanina"}]
    out = _cruce_etiqueta_formula({"fase_4_lista_ingredientes_completa": _LISTA},
                                  kic, None)
    assert len(out) == 1
    assert "Beta-Alanina" in out[0]["mensaje"]
    assert "Taurina" not in out[0]["mensaje"]


def test_etiqueta_usa_kic_no_la_ficha_en_ingles():
    """La ficha del cliente viene en inglés y la etiqueta en castellano.

    Comparar entre idiomas marcaba como ausentes dos tercios de la fórmula. La
    referencia son los nombres de KIC, ya en castellano.
    """
    kic = [{"ingrediente": "Cafeína anhidra"}, {"ingrediente": "Taurina"}]
    canon = [{"name": "Caffeine Anh., 100%"}, {"name": "Taurine, 100%"}]
    assert _cruce_etiqueta_formula({"fase_4_lista_ingredientes_completa": _LISTA},
                                   kic, canon) == []


# ── cruce VRN de la Etiqueta ───────────────────────────────────────────

def test_vrn_etiqueta_discrepante():
    """El fallo #13 reproducido en otro agente: 4,9 % donde la dosis da 0,8 %."""
    kic = [{"ingrediente": "Potasio", "dosis_mg": 16}]
    canon = [{"name": "Potasio", "active_mg": 16, "raw_mg": 16}]
    etq = {"fase_3_tabla_nutricional_completa": {"filas": [
        {"nutriente": "Potasio", "cantidad": "16 mg", "porcentaje_vrd": "4,9%"}]}}
    out = _cruce_vrn_etiqueta(etq, kic, canon)
    assert len(out) == 1 and out[0]["severidad"] == "alta"


# ── volumen de toma y suma de la fórmula ───────────────────────────────

from pipeline.report_composer import (  # noqa: E402
    _alertas_de_agentes,
    _cruce_nutricional_ft_etiqueta,
    _cruce_nutricional_por_100,
    _cruce_suma_formula_volumen,
    _cruce_volumen_toma,
    _volumenes_mL,
)

_FT_50 = {
    "fase_1_identificacion": {"formato_comercial": "Envase unidosis de ~50 mL",
                              "peso_neto_por_unidad": "~50 mL"},
    "fase_3_informacion_nutricional": {
        "declaracion_nutricional_por_dosis_diaria": {
            "base_calculo": "Dosis de 50 mL",
            "seccion_obligatoria": {"proteinas_g": 7.34, "sal_g": 0.02}}},
}
_ETQ_50 = {"fase_3_tabla_nutricional_completa": {
    "dosis_referencia": "1 stick (50 mL ≈ 50 g)",
    "filas": [{"nutriente": "Proteínas", "valor_por_100g": "14,68 g",
               "valor_por_dosis": "7,34 g", "porcentaje_vrd": "-"}]}}
_CANON_50 = [{"name": "Agua", "raw_mg": 50000.0, "active_mg": 50000.0}]


def test_volumenes_ignora_gotas_de_aroma():
    """Un '0,5 mL' de aroma no es un envase; incluirlo rompía la moda."""
    assert _volumenes_mL("aroma 0,5 mL en un stick de 50 mL") == [50.0]


def test_volumen_toma_coherente_no_avisa():
    reg = {"evaluacion_global": {"resumen": "35 mg en 50 mL"}}
    assert _cruce_volumen_toma(_FT_50, _ETQ_50, reg, _CANON_50) == []


def test_volumen_toma_discrepante():
    """El caso real: Regulatorio dosificaba sobre 40 mL y el resto sobre 50."""
    reg = {"evaluacion_global": {
        "bloqueantes": ["Sucralosa: 35 mg en 40 mL ≈ 875 mg/kg"]}}
    out = _cruce_volumen_toma(_FT_50, _ETQ_50, reg, _CANON_50)
    assert len(out) == 1
    assert out[0]["severidad"] == "alta"
    assert "40" in out[0]["mensaje"] and "50" in out[0]["mensaje"]


def test_suma_formula_cuadra_con_el_envase():
    assert _cruce_suma_formula_volumen(_CANON_50, _FT_50) == []


def test_suma_formula_descuadrada():
    canon = [{"name": "Agua", "raw_mg": 42000.0}]
    out = _cruce_suma_formula_volumen(canon, _FT_50)
    assert len(out) == 1 and out[0]["severidad"] == "media"


# ── tabla nutricional ──────────────────────────────────────────────────

def test_nutricional_ft_y_etiqueta_coinciden():
    assert _cruce_nutricional_ft_etiqueta(_FT_50, _ETQ_50) == []


def test_nutricional_ft_y_etiqueta_discrepan():
    etq = {"fase_3_tabla_nutricional_completa": {
        "dosis_referencia": "50 mL",
        "filas": [{"nutriente": "Proteínas", "valor_por_100g": "14,68 g",
                   "valor_por_dosis": "3,20 g"}]}}
    out = _cruce_nutricional_ft_etiqueta(_FT_50, etq)
    assert len(out) == 1 and out[0]["severidad"] == "alta"


def test_nutricional_por_100_proporcional():
    assert _cruce_nutricional_por_100(_ETQ_50, _FT_50) == []


def test_nutricional_por_100_error_de_factor():
    """El clásico: la columna por dosis calculada como si la toma fuera 100 mL."""
    etq = {"fase_3_tabla_nutricional_completa": {
        "dosis_referencia": "1 stick (50 mL)",
        "filas": [{"nutriente": "Proteínas", "valor_por_100g": "14,68 g",
                   "valor_por_dosis": "14,68 g"}]}}
    out = _cruce_nutricional_por_100(etq, _FT_50)
    assert len(out) == 1 and out[0]["severidad"] == "alta"


# ── alertas que los agentes ya producían ───────────────────────────────

def test_bloqueante_regulatorio_sube_a_aviso():
    reg = {"evaluacion_global": {"bloqueantes": ["Sucralosa supera 400 mg/kg"]}}
    out = _alertas_de_agentes(reg, {})
    assert len(out) == 1
    assert out[0]["severidad"] == "alta"
    # Se sube tal cual: reinterpretarlo sería volver a opinar sobre el dictamen.
    assert out[0]["mensaje"] == "Sucralosa supera 400 mg/kg"


def test_menciones_pendientes_de_etiqueta():
    etq = {"fase_6_menciones_ausentes_incompletas": [
        {"mencion": "Operador responsable", "estado": "PENDIENTE"},
        {"mencion": "Lote", "estado": "OK"}]}
    out = _alertas_de_agentes({}, etq)
    assert len(out) == 1
    assert "Operador responsable" in out[0]["mensaje"]
    assert "Lote" not in out[0]["mensaje"]


def _cruce_lista(ingredientes, lista):
    etq = {"fase_4_lista_ingredientes_completa": lista}
    return _cruce_etiqueta_formula(etq, [{"ingrediente": n} for n in ingredientes], None)


class TestMatcherEtiqueta:
    """El cruce etiqueta ↔ fórmula señalaba como ausentes ingredientes que sí
    estaban declarados, solo que con otra denominación. Tres causas reales
    encontradas en el run_59 y el run_57_v3."""

    def test_estado_de_hidratacion_no_es_denominacion(self):
        # «anhidro» no forma parte de la denominación legal: la etiqueta hace
        # bien en omitirlo.
        avisos = _cruce_lista(
            ["Ácido cítrico anhidro"],
            "Agua; acidulante: ácido cítrico (E 330); aroma de limón",
        )
        assert avisos == []

    def test_ratio_identifica_el_ingrediente_sin_tokens_comunes(self):
        # «BCAAs (Leu:Iso:Val = 2:1:1)» y su desarrollo reglamentario no
        # comparten ni un token; la proporción sí.
        avisos = _cruce_lista(
            ["BCAAs (Leu:Iso:Val = 2:1:1, 95% pureza)"],
            "Agua; mezcla de aminoácidos de cadena ramificada "
            "(L-Leucina, L-Isoleucina, L-Valina en proporción 2:1:1)",
        )
        assert avisos == []

    def test_lista_separada_por_comas_se_trocea(self):
        # Con solo «;» la lista entera era un segmento y el score se diluía:
        # once ingredientes presentes salían marcados como ausentes.
        avisos = _cruce_lista(
            ["Bisglicinato de magnesio", "Bitartrato de colina", "L-citrulina"],
            "Agua, dextrosa, D-fructosa, L-citrulina, bisglicinato de magnesio, "
            "acidulante: ácido cítrico (E330), bitartrato de colina, aroma de fresa",
        )
        assert avisos == []

    def test_coma_dentro_de_parentesis_no_separa(self):
        seg = _trocear_lista("agua, mezcla (L-Leucina, L-Valina), sal")
        assert [s.strip() for s in seg] == ["agua", "mezcla (L-Leucina, L-Valina)", "sal"]

    def test_omision_real_sigue_detectandose(self):
        avisos = _cruce_lista(
            ["Cafeína anhidra", "Creatina monohidrato"],
            "Agua, dextrosa, D-fructosa, aroma de fresa, sal, acidulante: ácido cítrico (E330)",
        )
        assert len(avisos) == 1
        assert "Cafeína" in avisos[0]["mensaje"]
        assert "Creatina" in avisos[0]["mensaje"]
