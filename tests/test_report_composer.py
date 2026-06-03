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
    # 833.33 mg de Magchel al 12% → 100 mg de Mg activo (nunca 833.33).
    out = _dosis_activo({"ingrediente": "Magchel (12% Mg)", "dosis_formula_mg": 833.33})
    assert out == "100 mg"
    assert "833" not in out
    # Boswellia 166.67 mg al 30% → 50 mg AKBA.
    assert _dosis_activo({"ingrediente": "Boswellia (30% AKBA)", "dosis_formula_mg": 166.67}) == "50 mg"
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
    assert _dosis_activo(ing, {"active_mg": 1.40, "unit": "mg"}) == "1.4 mg"
    # Sin canónica → cae al cálculo puente.
    assert _dosis_activo({"ingrediente": "Boswellia (30% AKBA)", "dosis_formula_mg": 166.67}) == "50 mg"


def test_alinear_canonica_por_indice():
    from pipeline.report_composer import _alinear_canonica
    kic = [{"ingrediente": "a"}, {"ingrediente": "b"}]
    canon = [{"active_mg": 1}, {"active_mg": 2}]
    assert _alinear_canonica(kic, canon) == canon          # conteos iguales → empareja
    assert _alinear_canonica(kic, [{"active_mg": 1}]) == [None, None]  # distinto → fallback


def test_tabla_maestra_usa_canonica(tmp_path):
    from pipeline.report_composer import fmt_tabla_maestra
    kic = {"fase_2_ingredientes": [
        {"ingrediente": "Vitamina B6 (80,5%)", "dosis_formula_mg": 2.26, "porcentaje_nrv": "161"},
        {"ingrediente": "Extracto de bambú (85% sílice)", "dosis_formula_mg": 10.07},
    ]}
    canon = [{"active_mg": 1.40, "unit": "mg"}, {"active_mg": 4.0, "unit": "mg"}]
    out = "\n".join(fmt_tabla_maestra(kic, {}, {}, canonica=canon))
    assert "1.4 mg" in out          # B6 valor declarado, no el calculado 1.82
    assert "4 mg" in out            # bambú silicio, no 8.56 del 85%
    assert "según la ficha de fórmula" in out
    assert "833" not in out and "10.07" not in out  # nunca la materia prima


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
                   test_alinear_canonica_por_indice):
            fn()
            print(f"✅ {fn.__name__}")
        for fn in (test_tabla_maestra_usa_canonica,):
            fn(tmp)
            print(f"✅ {fn.__name__}")
        test_claim_en_espera_botanico()
        print("✅ test_claim_en_espera_botanico")
