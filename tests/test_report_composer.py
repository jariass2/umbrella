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

from pipeline.report_composer import (  # noqa: E402
    compose_informe, fmt_portfolio, fmt_segmentos, fmt_formatos_segmentos,
)

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
    # Cabecera única de la tabla maestra (formato Excel del cliente).
    assert texto.count("Bioavailability | REGA") == 1
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
    # Las 14 entradas del Anexo II de alérgenos. El estado remite a la ficha
    # técnica del cliente: la evaluación ya existe, no la pedimos otra vez.
    assert texto.count("| Según ficha técnica |") == 14


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


def test_marketing_secciones_en_bloque3(tmp_path):
    texto = _informe(tmp_path)
    assert "### Segmentos de mercado" in texto
    assert "### Formatos × Segmentos" in texto


def test_segmentos_render_estructurado():
    clm = {"parte_f_segmentos_mercado": [
        {"segmento": "Senior 60+", "necesidad_principal": "movilidad",
         "encaje_formula": "colágeno + Mg", "mensaje_clave": "Muévete mejor"},
    ]}
    out = "\n".join(fmt_segmentos(clm))
    assert "### Segmentos de mercado" in out
    assert "Senior 60+" in out and "Muévete mejor" in out


def test_segmentos_fallback_publico_objetivo():
    clm = {"parte_d_diferenciadores": {"publico_objetivo_principal": "Deportistas 30-50"}}
    out = "\n".join(fmt_segmentos(clm))
    assert "Deportistas 30-50" in out


def test_formatos_segmentos_matriz():
    fmt = {"matriz_formato_segmento": [
        {"segmento": "Joven lifestyle", "formato_recomendado": "Gominola",
         "justificacion": "consumo lúdico", "es_innovacion": True},
    ]}
    out = "\n".join(fmt_formatos_segmentos(fmt))
    assert "### Formatos × Segmentos" in out
    assert "Joven lifestyle" in out and "✅" in out  # innovación marcada


def test_formatos_segmentos_fallback_derivado():
    fmt = {"fase_4_recomendacion_final": {
        "formato_optimo": {"nombre": "Stick", "justificacion_comercial": "premium"},
        "formato_alternativo": {"nombre": "Sobre", "escenario": "low cost"},
    }}
    out = "\n".join(fmt_formatos_segmentos(fmt))
    assert "Stick" in out and "Sobre" in out


# ── Fase 7a/7c: confidencialidad de dosis + depuración de datos ──────────────

def test_parse_pct_activo():
    from pipeline.report_composer import _parse_pct_activo
    assert _parse_pct_activo("Extracto de Boswellia serrata (30% AKBA)") == 30.0
    assert _parse_pct_activo("Astaxantina natural (2,5% en almidón)") == 2.5
    assert _parse_pct_activo("Extracto de cúrcuma (<95 % curcuminoides)") == 95.0
    assert _parse_pct_activo("Vitamina B6 HCl (Piridoxina HCl)") is None  # sin %
    assert _parse_pct_activo("") is None


def test_dosis_activo_no_expone_materia_prima():
    from pipeline.report_composer import _dosis_activo
    # 833.33 mg de Magchel al 12% → 99,9996 mg de Mg activo (nunca 833.33).
    out = _dosis_activo({"ingrediente": "Magchel (12% Mg)", "dosis_formula_mg": 833.33})
    assert out == "99.999600 mg"
    assert "833" not in out
    # Boswellia 166.67 mg al 30% → 50,001 mg AKBA.
    assert _dosis_activo({"ingrediente": "Boswellia (30% AKBA)", "dosis_formula_mg": 166.67}) == "50.001000 mg"
    # Excipiente sin % → guion, no la dosis de materia prima.
    assert _dosis_activo({"ingrediente": "Celulosa microcristalina", "dosis_formula_mg": 64.44}) == "—"


def test_fmt_pct_na_no_imprime_porcentaje():
    from pipeline.report_composer import _fmt_pct
    assert _fmt_pct("N/A") == "—"
    assert _fmt_pct("n/a") == "—"
    assert _fmt_pct("161") == "161%"
    assert _fmt_pct("26.7%") == "26.7%"


def test_spec_val_dict_no_crudo():
    from pipeline.report_composer import _spec_val
    out = _spec_val({"valor": "Cápsula opaca", "metodo": "Inspección visual"})
    assert "{'valor'" not in out
    assert "Cápsula opaca" in out and "Inspección visual" in out
    assert _spec_val("texto plano") == "texto plano"


def test_dosis_activo_canonico_prevalece_sobre_calculo():
    from pipeline.report_composer import _dosis_activo
    # B6: cálculo daría 1,82 (2,26×80,5%), pero la canónica declara 1,40 (sobredosado).
    ing = {"ingrediente": "Vitamina B6 (80,5%)", "dosis_formula_mg": 2.26}
    assert _dosis_activo(ing, {"active_mg": 1.40, "unit": "mg"}) == "1.400000 mg"
    # Sin canónica → cae al cálculo puente.
    assert _dosis_activo({"ingrediente": "Boswellia (30% AKBA)", "dosis_formula_mg": 166.67}) == "50.001000 mg"


def test_fmt_mg_microdosis_no_colapsa_a_cero():
    from pipeline.report_composer import _fmt_mg
    assert _fmt_mg(0.00375) == "0.003750 mg"   # B12: no se trunca a "0 mg"
    assert _fmt_mg(0.01) == "0.010000 mg"
    assert _fmt_mg(1.5) == "1.500000 mg"
    assert _fmt_mg(67.91) == "67.910000 mg"
    assert _fmt_mg(0) == "0 mg"             # cero real sigue siendo "0 mg"


def test_dosis_activo_recupera_microdosis_redondeada_a_cero():
    from pipeline.report_composer import _dosis_activo
    # B12: el FT PDF redondea el activo a 0,00; se recupera desde materia prima × %.
    canon = {"active_mg": 0.0, "raw_mg": 3.75, "pct_active": "0,1", "unit": "mg"}
    assert _dosis_activo({"ingrediente": "Vitamina B12"}, canon) == "0.003750 mg"


def test_alinear_canonica_por_identidad():
    from pipeline.report_composer import _alinear_canonica
    # KIC reordena y consolida vs la canónica del FT (conteos distintos, sin
    # orden común): el emparejamiento es por IDENTIDAD, no por índice.
    kic = [
        {"ingrediente": "Magnesio (Bisglicinato de Magnesio)"},
        {"ingrediente": "Vitamina B6 (Piridoxina, como HCl)"},
        {"ingrediente": "Astaxantina (Haematococcus pluvialis, AstaMarine® CWD 1%)"},
    ]
    canon = [  # otro orden + una fila extra sin par en KIC
        {"name": "AstaMarine® CWD 1% Natural Pure Astaxanthin", "active_mg": 1.5},
        {"name": "Vit. B6 HCl, 80,5% Pyridoxine", "active_mg": 3.0},
        {"name": "Mango flavour 100%", "active_mg": 300.0},
        {"name": "Mg Bisglycinate, 12% Mg", "active_mg": 150.0},
    ]
    out = _alinear_canonica(kic, canon)
    assert out[0]["active_mg"] == 150.0   # Magnesio (no roba el Ca de nadie)
    assert out[1]["active_mg"] == 3.0     # B6 por código de vitamina
    assert out[2]["active_mg"] == 1.5     # Astaxantina por marca AstaMarine
    # El conteo distinto ya NO descarta toda la canónica (era el bug del cliente).
    assert all(o is not None for o in out)


def test_tabla_nutricional_agrega_por_elemento():
    """El Anexo XIII declara NUTRIENTES, no las sales que los aportan. Xavier
    (2026-07-27) tachó la tabla porque listaba 'tri-Mg Citrate' y 'Mg
    Bisglycinate' como dos filas: debe ser un solo Magnesio con la suma.
    Los valores esperados son los que él mismo anotó sobre el informe."""
    from pipeline.report_composer import _nutricional_vitmin_rows
    kic = {"fase_2_ingredientes": [
        {"ingrediente": "Citrato de magnesio", "tipologia": "MINERAL"},
        {"ingrediente": "Bisglicinato de magnesio", "tipologia": "MINERAL"},
        {"ingrediente": "Extracto de bambú (sílice)", "tipologia": "MINERAL"},
    ]}
    canon = [
        {"name": "Tri-Mg Citrate Anh.", "active_mg": 12.88, "raw_mg": 80.5},
        {"name": "Mg Bisglycinate, 12% Mg", "active_name": "Mg",
         "active_mg": 15.08, "raw_mg": 125.67},
        {"name": "Bamboo Extract (85% Silica)", "active_name": "Silicon",
         "active_mg": 16.635, "raw_mg": 41.87},
    ]
    rows = _nutricional_vitmin_rows(kic, canon)
    por_nombre = {r[0]: r for r in rows}

    # Una sola fila de magnesio, con la suma 12,88 + 15,08 = 27,96 mg.
    assert "Magnesio" in por_nombre, f"Filas obtenidas: {rows}"
    assert sum(1 for r in rows if r[0] == "Magnesio") == 1
    assert por_nombre["Magnesio"][1] == "27,96 mg"
    # 27,96 / 375 = 7,456% → "7,5%" (VRN legal del Anexo XIII, no inventado).
    assert por_nombre["Magnesio"][2] == "7,5%"

    # El silicio no tiene VRN en el Anexo XIII: cantidad sí, porcentaje nunca.
    assert por_nombre["Silicio"][2] == "Sin VRN establecido"

    # Ninguna fila conserva el nombre de la materia prima.
    assert not any("Citrate" in r[0] or "Bisglycinate" in r[0] for r in rows)


def test_tabla_maestra_usa_canonica(tmp_path):
    """La tabla replica la Tabla Cuantitativa.xlsm del cliente: ahora muestra
    materia prima explícita (Ingredient mg+) y %Formula, junto con ACTIVE mg
    de la canónica. Las nuevas cabeceras deben estar presentes y los orígenes
    canónicos prevalecen sobre los cálculos puente."""
    from pipeline.report_composer import fmt_tabla_maestra
    kic = {"fase_2_ingredientes": [
        {"ingrediente": "Vitamina B6 (Piridoxina, 80,5%)", "dosis_formula_mg": 2.26, "porcentaje_nrv": "161"},
        {"ingrediente": "Extracto de bambú (85% sílice)", "dosis_formula_mg": 10.07},
    ]}
    canon = [
        # Con code: REF debe mostrar el código, no el nº de orden.
        {"name": "Vit. B6 HCl, 80,5% Pyridoxine", "active_mg": 1.40,
         "raw_mg": 2.26, "pct_active": "80,5", "unit": "mg", "code": "91483"},
        # Sin code: REF cae al nº de orden (fallback).
        {"name": "Extracto de Bambú 85% sílice", "active_mg": 4.0,
         "raw_mg": 4.71, "pct_active": "85", "unit": "mg"},
    ]
    # Total de cápsula para %Formula: 500 mg → B6 0,452% / bambú 0,942%.
    doc = {"fase_2_formula_cuantitativa": {"total_capsula_mg": 500}}

    out = "\n".join(fmt_tabla_maestra(kic, {}, {}, canonica=canon, doc=doc))

    # ── ACTIVE mg (canónica prevalece sobre el cálculo puente) ───────────
    assert "1.400000 mg" in out          # B6 valor declarado, no el calculado 1.82
    assert "4.000000 mg" in out          # bambú silicio, no 8.56 del 85%

    # ── Ingredient mg+ (NUEVO: materia prima explícita) ─────────────────
    assert "2.260000 mg" in out          # B6 raw de la canónica
    assert "4.705882 mg" in out          # bambú raw recalculado desde el activo (4 mg / 85 %)

    # ── %Formula (NUEVO: ratio sobre total de cápsula) ──────────────────
    # 2.26 / 500 * 100 = 0.452 → "0,452"
    assert "0,452" in out
    # 4.705882 / 500 * 100 = 0.941 → "0,941"
    assert "0,941" in out

    # ── Cabeceras del Excel del cliente (orden exacto) ──────────────────
    for h in ["REF", "Formula Ingredient Name", "List of Ingredients",
              "Active name", "% Active", "ACTIVE mg", "%VRN",
              "Ingredient mg+", "%Formula", "Bioavailability", "REGA"]:
        assert h in out, f"Falta cabecera de la tabla cliente: {h}"

    # ── REF: code de la canónica, con fallback al nº de orden ───────────
    filas = [l for l in out.splitlines() if "Vitamina B6" in l or "bambú" in l]
    assert len(filas) == 2, f"Se esperaban 2 filas de ingrediente: {filas}"
    b6, bambu = filas
    assert b6.split("|")[1].strip() == "91483"   # code de la canónica
    assert bambu.split("|")[1].strip() == "2"    # sin code → nº de orden

    # ── Cabecera antigua "Forma química" desaparece del Bloque 1 ────────
    # (puede seguir en el FT interno — se valida por contexto).
    assert "| Forma química |" not in out

    # ── Nota al pie actualizada: ya no habla de confidencialidad ────────
    assert "ACTIVE mg" in out and "Ingredient mg+" in out
    # La nota nueva describe ACTIVE mg e Ingredient mg+, no "confidencial".
    assert "confidencial" not in out.lower()
    assert "no la dosis de materia prima" not in out


def test_claim_en_espera_botanico():
    from pipeline.report_composer import _claim_en_espera, fmt_claims
    # "Ninguno autorizado" (texto del LLM para botánicos) = en espera.
    assert _claim_en_espera({"texto_claim": "Ninguno autorizado"}) is True
    assert _claim_en_espera({"texto_claim": "No autorizado"}) is True
    # Un claim real NO está en espera.
    assert _claim_en_espera({"texto_claim": "Magnesium contributes to..."}) is False
    # En el render: botánico → etiqueta "En espera (botánico)", no "Ninguno autorizado".
    out = "\n".join(fmt_claims({"parte_a_claims_regulatorios": {"claims_por_ingrediente": [
        {"ingrediente": "Boswellia (30% AKBA)", "claims": [{"texto_claim": "Ninguno autorizado"}]},
    ]}}))
    assert "En espera (botánico)" in out
    assert "Ninguno autorizado" not in out


def test_dosis_de_activo_en_tablas_cliente(tmp_path):
    texto = _informe(tmp_path)
    # Cabecera renombrada en tabla maestra y tabla de activos FT.
    assert "Dosis de activo" in texto
    # Echo de fórmula con mg de materia prima eliminado de la cabecera.
    assert "## Fórmula analizada" not in texto
    # Nota de confidencialidad presente.
    assert "Confidencialidad" in texto


def test_analisis_ingredientes_tolera_no_strings_en_lista():
    """Regresión run_53: el agente KIC devolvió un int mezclado en
    `factores_positivos`; `"; ".join(...)` revienta, compose_informe caía y el
    PDF revertía al volcado crudo por agente (la tabla nutricional salía como
    texto `Parametro:/Unidad:/…`). El composer debe coercer a str."""
    from pipeline.report_composer import fmt_analisis_ingredientes
    kic = {"fase_2_ingredientes": [{
        "ingrediente": "Magnesio",
        "biodisponibilidad": {"factores_positivos": ["quelato", 100, "aminoácido"]},
    }]}
    out = "\n".join(fmt_analisis_ingredientes(kic))
    assert "100" in out            # el int se renderiza como str, no rompe
    assert "quelato" in out


def test_alinear_canonica_consolida_formas_y_cubre_minerales():
    """Regresión run_53: la canónica (FT PDF, EN, N filas) y KIC (ES, menos filas
    y consolidadas) no cuadran por índice. (1) minerales antes en '—' (K, Se…)
    ahora alinean; (2) las formas consolidadas se SUMAN (Magnesio = citrato +
    bisglicinato); (3) el silicio de bambú y el OSA no se cruzan entre sí."""
    from pipeline.report_composer import _alinear_canonica
    kic = [
        {"ingrediente": "Potasio (tri-K citrato)"},
        {"ingrediente": "Magnesio (tri-Mg citrato + Mg bisglicinato)"},
        {"ingrediente": "Selenio (levadura enriquecida)"},
        {"ingrediente": "Silicio (extracto de bambú al 85% sílice)"},
        {"ingrediente": "Silicio (ácido ortosilícico, OSA, Orgono Powder)"},
    ]
    canon = [
        {"name": "tri-K Citrate, 35,6% K", "active_name": "K", "active_mg": 8.95, "raw_mg": 25.14, "unit": "mg"},
        {"name": "Tri-Mg Citrate, 16% Mg", "active_name": "Mg", "active_mg": 12.88, "raw_mg": 80.5, "unit": "mg"},
        {"name": "Mg Bisglycinate, 12% Mg", "active_name": "Mg", "active_mg": 15.08, "raw_mg": 125.67, "unit": "mg"},
        {"name": "Selenium Yeast, 0,2% Se", "active_name": "Se", "active_mg": 0.006, "raw_mg": 3.02, "unit": "mg"},
        {"name": "Bamboo Extract, 85% Silica", "active_name": "Silicon", "active_mg": 16.63, "raw_mg": 41.87, "unit": "mg"},
        {"name": "Orgono Powder OSA Orthosilicic acid", "active_name": "Si", "active_mg": 0.225, "raw_mg": 15.0, "unit": "mg"},
    ]
    res = _alinear_canonica(kic, canon)
    assert res[0] is not None and res[0]["active_name"] == "K"          # antes '—'
    assert res[1] is not None and round(res[1]["active_mg"], 2) == 27.96  # 12,88 + 15,08
    assert res[2] is not None and res[2]["active_name"] == "Se"          # antes '—'
    assert res[3] is not None and round(res[3]["active_mg"], 2) == 16.63  # bambú
    assert res[4] is not None and round(res[4]["active_mg"], 3) == 0.225  # OSA, sin cruzarse


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for fn in (test_seis_bloques_en_orden, test_tabla_ingredientes_una_sola_vez,
                   test_nutricional_no_se_repite, test_sin_doble_porcentaje,
                   test_ficha_tecnica_seis_secciones, test_ficha_tecnica_cabecera_fabricante,
                   test_vida_util_sin_meses_duplicado, test_etiqueta_layout_caras,
                   test_etiqueta_bilingue, test_bloque6_fallback_sin_portfolio,
                   test_marketing_secciones_en_bloque3,
                   test_dosis_de_activo_en_tablas_cliente):
            fn(tmp)
            print(f"✅ {fn.__name__}")
        for fn in (test_portfolio_render, test_segmentos_render_estructurado,
                   test_segmentos_fallback_publico_objetivo, test_formatos_segmentos_matriz,
                   test_formatos_segmentos_fallback_derivado,
                   test_parse_pct_activo, test_dosis_activo_no_expone_materia_prima,
                   test_fmt_pct_na_no_imprime_porcentaje, test_spec_val_dict_no_crudo,
                   test_dosis_activo_canonico_prevalece_sobre_calculo,
                   test_alinear_canonica_por_indice,
                   test_alinear_canonica_consolida_formas_y_cubre_minerales,
                   test_analisis_ingredientes_tolera_no_strings_en_lista):
            fn()
            print(f"✅ {fn.__name__}")
        for fn in (test_tabla_maestra_usa_canonica,):
            fn(tmp)
            print(f"✅ {fn.__name__}")
        test_claim_en_espera_botanico()
        print("✅ test_claim_en_espera_botanico")


def test_detecta_fuga_de_idioma_cjk():
    """El LLM coló chino en los agentes 6 y 7 de run_56 ("sin esfuerzo de撕裂").
    Helvetica no tiene esos glifos, así que en el PDF salen como cuadrados
    negros y el cliente los ve. El composer debe avisar, no silenciarlo."""
    from pipeline.report_composer import _detectar_fuga_idioma
    assert _detectar_fuga_idioma("stick: solo si la apertura es fácil (sin esfuerzo de撕裂)")
    assert _detectar_fuga_idioma("premix para均匀 distribución")
    # Un informe correcto en español, con acentos y símbolos técnicos, no avisa.
    assert _detectar_fuga_idioma(
        "Magnesio 27,96 mg — 7,5% VRN · Na2MoO4·2H2O · µg/día") == []


# ── Correcciones de Xavier sobre la fórmula #13 (2026-08-25) ────────────────
# Las 11 notas de su PDF caen todas en la Tabla Cuantitativa y ninguna toca el
# criterio regulatorio: son aritmética y mapeo de columnas.

def test_raw_mg_a_precision_completa():
    """El cobre: 1 mg de activo al 14 % son 7,142857 mg de gluconato, no los
    7,14 que la ficha PDF redondea a dos decimales."""
    from pipeline.report_composer import _raw_mg_preciso
    preciso = _raw_mg_preciso({"active_mg": 1.0, "pct_active": "14", "raw_mg": 7.14})
    assert abs(preciso - 7.142857) < 1e-5


def test_raw_mg_incoherente_no_se_reescribe():
    """Una discrepancia grande no es redondeo: se respeta el dato de la ficha
    y se deja que la coherencia lo señale, en vez de inventar un valor."""
    from pipeline.report_composer import _raw_mg_preciso
    assert _raw_mg_preciso({"active_mg": 16.0, "pct_active": "35.6", "raw_mg": 127.5}) == 127.5


def test_incoherencia_pct_activo_potasio():
    """El fallo del #13: la ficha traía 77,3 % (pureza del citrato) y el nombre
    declara 35,6 % K. Multiplicar por el primero publicó 98,56 mg y 4,9 % VRN
    cuando son 16 mg y 0,8 %."""
    from pipeline.report_composer import incoherencias_fila
    avisos = incoherencias_fila(
        "Potasio (como tri-K Citrato H2O 35,6% K)",
        {"active_mg": 98.56, "pct_active": "77.3", "raw_mg": 127.5},
    )
    assert any("conflicto" in a for a in avisos)


def test_fila_coherente_no_genera_aviso():
    from pipeline.report_composer import incoherencias_fila
    assert incoherencias_fila(
        "Cobre (como Copper Gluconate 14%)",
        {"active_mg": 1.0, "pct_active": "14", "raw_mg": 7.142857},
    ) == []


def test_sodio_no_tiene_vrn_y_el_cloruro_si():
    """Xavier: 'el sodi (Na) no en té VRN; el clorur sí'. La fila NaCl declaraba
    un 1,2 % inventado por el LLM sobre una base de 2000 mg que no existe."""
    from pipeline.report_composer import _vrn_ingrediente
    vrn = _vrn_ingrediente(
        {"ingrediente": "Cloruro sódico (NaCl)", "porcentaje_nrv": "1,2%"},
        {"active_mg": 60.0, "raw_mg": 152.671754},
    )
    assert "Cl" in vrn and "no tiene VRN" in vrn
    assert "1,2" not in vrn


def test_cloruro_y_sodio_no_secuestran_otros_minerales():
    """'Sodium selenite' es selenio y 'zinc chloride' es zinc: el anión y el
    catión de acompañamiento nunca deben ganar al mineral específico."""
    from pipeline.report_composer import _ing_ident_key
    assert _ing_ident_key("Sodium Selenite") == "min:se"
    assert _ing_ident_key("Zinc chloride") == "min:zn"
    assert _ing_ident_key("Cloruro sódico (NaCl)") == "min:cl"


def test_aditivo_no_secuestra_el_mineral_de_su_contraion():
    """La raíz de cuatro de las once notas del #13: «Potassium Sorbate E202» se
    identificaba como potasio y se fusionaba con el citrato tri-K, sumando
    44,94 + 82,56 = 127,5 mg de materia prima y 16 + 82,56 = 98,56 mg de activo.
    De ahí salían el 77,3 % de estandarización y el 4,9 % VRN."""
    from pipeline.report_composer import _ing_ident_key
    assert _ing_ident_key("Potassium Sorbate E202") is None
    assert _ing_ident_key("Sorbato potásico (E202)") is None
    assert _ing_ident_key("Sodium Benzoate") is None
    # El potasio de verdad sigue identificándose.
    assert _ing_ident_key("tri-K Citrate H2O Fine Usual, 35,6% K") == "min:k"


def test_score_tokens_acepta_subconjunto():
    """«Goma xantana (Satiaxane CX 911)» contra «Satiaxane CX 911» daba 1/3 en
    Jaccard y se caía por una milésima del umbral de 0,34."""
    from pipeline.report_composer import _score_tokens
    assert _score_tokens({"goma", "xanthan", "satiaxane"}, {"satiaxane"}) == 1.0
    assert _score_tokens({"a", "b", "c"}, {"d", "e", "f"}) == 0.0


def test_excipientes_es_en_casan_con_la_canonica():
    """Diez de las 21 filas del #13 (agua, dextrosa, ácido cítrico…) no casaban
    con la canónica y publicaban la cifra del LLM en vez del dato de la ficha."""
    from pipeline.report_composer import _alinear_canonica
    kic = [{"ingrediente": n} for n in [
        "Agua", "Ácido cítrico anhidro", "D-Fructosa anhidra",
        "Dextrosa anhidra (D-glucosa)", "L-Citrulina", "Sorbato potásico (E202)",
    ]]
    canon = [{"name": n} for n in [
        "Water H2O", "Citric Acid anh 100%", "D-Fructose Anh.",
        "Dextrose Anh.", "L-Citrulline 100%", "Potassium Sorbate E202",
    ]]
    assert all(c is not None for c in _alinear_canonica(kic, canon))
