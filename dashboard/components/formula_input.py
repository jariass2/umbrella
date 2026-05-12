"""Componente de entrada estructurada de fórmula con filas de ingredientes."""

import streamlit as st

from dashboard.utils.formula_parser import VALID_UNITS


def render_formula_input():
    """Renderiza el formulario de fórmula en la sidebar.

    Devuelve: (product_name, ingredients, analyze_clicked)
    """
    st.markdown("### Formula")

    product_name = st.text_input("Nombre del producto", placeholder="Collagen Complex Pro")

    st.markdown("#### Ingredientes")

    if "ingredients" not in st.session_state:
        st.session_state.ingredients = [
            {"name": "", "dosage": "", "unit": "mg"},
        ]

    # Renderizar filas de ingredientes
    indices_to_remove = []
    for i, ing in enumerate(st.session_state.ingredients):
        cols = st.columns([4, 1.5, 1, 0.4])
        with cols[0]:
            ing["name"] = st.text_input(
                "Ingrediente", value=ing["name"],
                key=f"ing_name_{i}", label_visibility="collapsed",
                placeholder="Ingrediente",
            )
        with cols[1]:
            ing["dosage"] = st.text_input(
                "Dosis", value=ing["dosage"],
                key=f"ing_dose_{i}", label_visibility="collapsed",
                placeholder="Dosis",
            )
        with cols[2]:
            ing["unit"] = st.selectbox(
                "Unidad", VALID_UNITS,
                index=VALID_UNITS.index(ing["unit"]) if ing["unit"] in VALID_UNITS else 0,
                key=f"ing_unit_{i}", label_visibility="collapsed",
            )
        with cols[3]:
            if st.button("✕", key=f"ing_remove_{i}", help="Eliminar"):
                indices_to_remove.append(i)

    # Eliminar ingredientes marcados
    if indices_to_remove:
        for i in sorted(indices_to_remove, reverse=True):
            st.session_state.ingredients.pop(i)
        st.rerun()

    # Añadir ingrediente
    if st.button("+ Añadir ingrediente", use_container_width=True):
        st.session_state.ingredients.append({"name": "", "dosage": "", "unit": "mg"})
        st.rerun()

    # Botón de análisis
    st.markdown("---")
    has_ingredients = any(ing["name"].strip() for ing in st.session_state.ingredients)
    has_product = bool(product_name.strip())
    analyze_clicked = st.button(
        "Analizar Formula",
        type="primary",
        use_container_width=True,
        disabled=not (has_product and has_ingredients) or st.session_state.get("pipeline_running", False),
    )

    return product_name, st.session_state.ingredients, analyze_clicked
