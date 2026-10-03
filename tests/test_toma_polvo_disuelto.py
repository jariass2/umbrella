"""Un polvo que se disuelve se dosifica por los gramos de polvo, no por el agua.

En el run_66 (MIX 240306, 55 g en 400-500 mL) los 500 mL de agua se tomaron
por la toma y saltaron dos avisos falsos: volumen de toma y tabla nutricional.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.report_composer import (  # noqa: E402
    _cruce_nutricional_por_100,
    _cruce_volumen_toma,
    _toma_polvo_g,
    _volumen_declarado,
)

DOSIS_POLVO = "1 toma de 55 g disuelta en 400-500 mL de fase acuosa"


def test_toma_polvo_lee_los_gramos():
    assert _toma_polvo_g(DOSIS_POLVO) == 55
    assert _toma_polvo_g("Disolver 55 g de polvo en 400-500 mL de agua") == 55
    assert _volumen_declarado(DOSIS_POLVO) == 55


def test_liquido_sigue_leyendo_mL():
    assert _toma_polvo_g("1 vial de 50 mL") is None
    assert _volumen_declarado("1 vial de 50 mL") == 50


def test_polvo_disuelto_no_dispara_cruce_de_volumen():
    etq = {"fase_3_tabla_nutricional_completa": {"dosis_referencia": DOSIS_POLVO}}
    canonica = [{"raw_mg": 50_000}, {"raw_mg": 5_000}]
    assert _cruce_volumen_toma({}, etq, {}, canonica) == []


def test_tabla_nutricional_proporcional_sobre_los_gramos():
    etq = {"fase_3_tabla_nutricional_completa": {
        "dosis_referencia": DOSIS_POLVO,
        "filas": [{"nutriente": "Valor energético",
                   "valor_por_100g": "755 kJ", "valor_por_dosis": "415 kJ"}],
    }}
    assert _cruce_nutricional_por_100(etq, {}) == []


def _tabla(filas):
    return {"fase_3_tabla_nutricional_completa": {
        "dosis_referencia": DOSIS_POLVO, "filas": filas}}


def test_g_frente_a_mg_y_redondeo_no_son_descuadre():
    etq = _tabla([
        {"nutriente": "L-Glutamina", "valor_por_100g": "9,09 g", "valor_por_dosis": "5000 mg"},
        {"nutriente": "azúcares", "valor_por_100g": "0,4 g", "valor_por_dosis": "0,2 g"},
    ])
    assert _cruce_nutricional_por_100(etq, {}) == []


def test_descuadre_real_sigue_avisando_y_las_microdosis_no_se_tapan():
    etq = _tabla([
        {"nutriente": "L-Glutamina", "valor_por_100g": "9,09 g", "valor_por_dosis": "500 mg"},
        {"nutriente": "Vitamina B12", "valor_por_100g": "0,0073 mg", "valor_por_dosis": "0,04 mg"},
    ])
    avisos = _cruce_nutricional_por_100(etq, {})
    assert len(avisos) == 1
    assert "2 fila(s)" in avisos[0]["mensaje"]
    assert "55 g" in avisos[0]["mensaje"]


# ── run_67 (MIX 260025): 7 g de polvo en 200 mL ──────────────────────────

def test_agua_de_reconstitucion_sin_gramos_no_es_la_toma():
    from pipeline.report_composer import _volumen_declarado
    assert _volumen_declarado("Recomendar disolver cada toma en 200 mL de fase acuosa") is None
    assert _volumen_declarado("Diluir en 400-500 mL de agua") is None
    assert _volumen_declarado("1 vial de 50 mL") == 50


def test_kic_en_microgramos_no_es_cifra_inventada():
    from pipeline.report_composer import _cruce_dosis_kic_canonica
    canon = [{"raw_mg": 6.19, "active_mg": 0.01125}]
    ok = [{"ingrediente": "Vitamina K2", "dosis_formula_mg": 11.25, "dosis_formula_unidad": "µg"}]
    assert _cruce_dosis_kic_canonica(ok, canon) == []
    mal = [{"ingrediente": "Vitamina K2", "dosis_formula_mg": 11.25, "dosis_formula_unidad": "mg"}]
    assert len(_cruce_dosis_kic_canonica(mal, canon)) == 1


def test_vrn_de_sales_se_expresa_como_vitamina():
    from pipeline.report_composer import _vrn_ingrediente
    b5 = _vrn_ingrediente({"ingrediente": "Vitamina B5 (D-pantotenato cálcico)"},
                          {"name": "Vit. B5, 90,16% Calcium D-Pantothenate",
                           "active_name": "Calcium D-Pantothenate", "active_mg": 0.9})
    assert b5.startswith("13,7%") and "ácido pantoténico" in b5
    b9 = _vrn_ingrediente({"ingrediente": "Vitamina B9 (L-metilfolato cálcico)"},
                          {"name": "Metafolin, 100% Calcium L-Methylfolate",
                           "active_name": "Calcium L-Methylfolate", "active_mg": 0.03})
    assert b9.startswith("13,3%") and "folato" in b9
    # Una sal que la ficha ya da como vitamina no se convierte dos veces.
    assert _vrn_ingrediente({"ingrediente": "Vitamina B5"},
                            {"name": "Pantothenic acid", "active_mg": 0.9}) == "15%"


def test_claims_de_vitamina_bajo_15_vrn_no_aplican():
    from pipeline.report_composer import fmt_claims
    claim = {"texto_traduccion_es": "El ácido pantoténico contribuye a disminuir el cansancio y la fatiga",
             "referencia_efsa": "Reg. (UE) 432/2012"}
    clm = {"parte_a_claims_regulatorios": {"claims_por_ingrediente": [
        {"ingrediente": "Vitamina B5 (D-pantotenato cálcico)", "claims": [claim]}]}}
    kic = {"fase_2_ingredientes": [{"ingrediente": "Vitamina B5 (D-pantotenato cálcico)",
                                    "dosis_formula_mg": 0.9}]}
    canon = [{"name": "Vit. B5, 90,16% Calcium D-Pantothenate",
              "active_name": "Calcium D-Pantothenate", "raw_mg": 1.21, "active_mg": 0.9}]
    out = "\n".join(fmt_claims(clm, kic=kic, canonica=canon))
    assert "No aplicable" in out and "cansancio" not in out
    # Con dosis suficiente el claim se publica.
    canon[0]["active_mg"] = 1.2
    out = "\n".join(fmt_claims(clm, kic=kic, canonica=canon))
    assert "cansancio" in out and "No aplicable" not in out


def test_tabla_nutricional_declara_la_vitamina_no_la_sal():
    from pipeline.report_composer import _nutricional_vitmin_rows
    kic = {"fase_2_ingredientes": [
        {"ingrediente": "Vitamina B5 (D-pantotenato cálcico)", "tipologia": "VITAMINA"},
        {"ingrediente": "Vitamina B9 (L-metilfolato cálcico)", "tipologia": "VITAMINA"}]}
    canon = [{"name": "Vit. B5, 90,16% Calcium D-Pantothenate",
              "active_name": "Calcium D-Pantothenate", "raw_mg": 1.21, "active_mg": 0.9},
             {"name": "Metafolin (Coemzime B9), 100% Calcium L-Methylfolate",
              "active_name": "Calcium L-Methylfolate", "raw_mg": 0.04, "active_mg": 0.03}]
    filas = {r[0]: r for r in _nutricional_vitmin_rows(kic, canon)}
    assert filas["Ácido pantoténico (B5)"][2] == "13,7%"
    assert filas["Folato (B9)"][2] == "13,3%"


# ── run_68 (MIX 260047): dos fuentes del mismo mineral ───────────────────

def test_vrd_de_etiqueta_se_compara_con_la_suma_de_fuentes(monkeypatch):
    import pipeline.report_composer as rc
    vrn = {"Citrato de magnesio": "3,4%", "Bisglicinato de magnesio": "4%"}
    monkeypatch.setattr(rc, "_vrn_ingrediente", lambda ing, c: vrn[ing["ingrediente"]])
    monkeypatch.setattr(rc, "_buscar_por_nombre", lambda n, filas, k: filas[0])
    etq = {"fase_3_tabla_nutricional_completa": {"filas": [
        {"nutriente": "Magnesio", "porcentaje_vrd": "7,5%"}]}}
    kic = [{"ingrediente": n} for n in vrn]
    assert rc._cruce_vrn_etiqueta(etq, kic, [None, None]) == []
    etq["fase_3_tabla_nutricional_completa"]["filas"][0]["porcentaje_vrd"] = "15%"
    avisos = rc._cruce_vrn_etiqueta(etq, kic, [None, None])
    assert len(avisos) == 1 and "Magnesio" in avisos[0]["mensaje"]


def test_bloqueantes_negados_o_potenciales():
    from pipeline.report_composer import _alertas_de_agentes
    reg = {"evaluacion_global": {"bloqueantes": [
        "Ninguno confirmado como bloqueante.",
        "Potencial: extracto de bambú, si no se acredita la especie.",
        "Sucralosa por encima del límite legal."]}}
    out = _alertas_de_agentes(reg, {})
    assert [a["severidad"] for a in out] == ["media", "alta"]


def test_sal_con_elemento_adjetivo_se_encuentra_en_la_etiqueta():
    from pipeline.report_composer import _cruce_etiqueta_formula
    etq = {"fase_4_lista_ingredientes_completa":
           "Bisglicinato de magnesio, colecalciferol (vitamina D3), "
           "bisglicinato cúprico, picolinato de cromo, molibdato de sodio."}
    kic = [{"ingrediente": "Molibdato sódico dihidrato (molibdeno)"},
           {"ingrediente": "Bisglicinato de cobre"}]
    assert _cruce_etiqueta_formula(etq, kic, None) == []


# ── run_69 (MIX 210074) ──────────────────────────────────────────────────

def test_vrd_del_mismo_lado_del_15_es_media(monkeypatch):
    import pipeline.report_composer as rc
    monkeypatch.setattr(rc, "_vrn_ingrediente", lambda ing, c: "22,9%")
    monkeypatch.setattr(rc, "_buscar_por_nombre", lambda n, filas, k: filas[0])
    etq = {"fase_3_tabla_nutricional_completa": {"filas": [
        {"nutriente": "Ácido pantoténico", "porcentaje_vrd": "25%"}]}}
    kic = [{"ingrediente": "Vitamina B5"}]
    assert rc._cruce_vrn_etiqueta(etq, kic, [None])[0]["severidad"] == "media"
    etq["fase_3_tabla_nutricional_completa"]["filas"][0]["porcentaje_vrd"] = "10%"
    assert rc._cruce_vrn_etiqueta(etq, kic, [None])[0]["severidad"] == "alta"


def test_aromas_declarados_con_el_generico():
    from pipeline.report_composer import _cruce_etiqueta_formula
    etq = {"fase_4_lista_ingredientes_completa":
           "Colágeno hidrolizado, L-glicina, bisglicinato de magnesio, aromas, "
           "maltodextrina, edulcorante (sucralosa [E 955])."}
    kic = [{"ingrediente": "Aroma de pomelo (Drycell Pompelmo)"},
           {"ingrediente": "Aroma natural de fruta roja"}]
    assert _cruce_etiqueta_formula(etq, kic, None) == []
    etq["fase_4_lista_ingredientes_completa"] = etq["fase_4_lista_ingredientes_completa"].replace("aromas, ", "")
    assert len(_cruce_etiqueta_formula(etq, kic, None)) == 1


def test_rol_secundario_nulo_es_valido():
    from agents.kic_agent_v2 import FuncionIngrediente
    assert FuncionIngrediente(rol_primario="Aroma", rol_secundario=None).rol_secundario is None


# ── run_70 (MIX 99200052) ────────────────────────────────────────────────

def test_estandarizacion_en_dos_niveles_no_es_conflicto():
    from pipeline.report_composer import incoherencias_fila
    canon = {"name": "Amaranthus hypochondriacus Extract, 100% Extract; 9% Nitric Oxide (NO)",
             "pct_active": "100"}
    assert incoherencias_fila("Extracto de Amaranthus (estandarizado al 9% «NO»)", canon) == []
    # El potasio del #13: el 77,3 % no está en el nombre de la ficha.
    k = {"name": "Tri-Potassium Citrate, 35,6% K", "pct_active": "77,3"}
    assert len(incoherencias_fila("Citrato tripotásico (35,6% K)", k)) == 1


def test_soporte_y_parentesis_no_esconden_el_ingrediente():
    from pipeline.report_composer import _cruce_etiqueta_formula
    etq = {"fase_4_lista_ingredientes_completa":
           "Ingredientes: Agua, dextrosa anhidra, D-fructosa anhidra, L-citrulina, "
           "colorante: ácido carmínico (E 120)."}
    kic = [{"ingrediente": "Ácido carmínico con maltodextrina de patata (Linicol IPHL20)"},
           {"ingrediente": "Fase acuosa (agua)"}]
    assert _cruce_etiqueta_formula(etq, kic, None) == []


def test_liquido_mas_denso_que_el_agua_no_descuadra():
    from pipeline.report_composer import _cruce_suma_formula_volumen
    ft = {"fase_1_identificacion": {"formato_comercial": "Vial de 41 mL"}}
    assert _cruce_suma_formula_volumen([{"raw_mg": 41_280}], ft) == []
    out = _cruce_suma_formula_volumen([{"raw_mg": 39_000}], ft)
    assert len(out) == 1 and "39.000,0 mg" in out[0]["mensaje"]


def test_vida_util_condicional_es_valida():
    from agents.product_qc_agent_v2 import VidaUtilEstimadaQC
    assert VidaUtilEstimadaQC(alcanzable="Condicional: no demostrable a priori").alcanzable
