"""Formula input matching the wireframe exactly."""

import streamlit as st

from dashboard.utils.formula_parser import VALID_UNITS


def render_formula_input():
    """Renderiza el formulario de fórmula en la sidebar con estilo wireframe."""
    # Título sidebar
    st.markdown('<div class="sidebar-title">Umbrella</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">Análisis Regulatorio Inteligente</div>', unsafe_allow_html=True)

    # Sección Fórmula
    st.markdown('<div class="sidebar-section-title">Fórmula</div>', unsafe_allow_html=True)
    product_name = st.text_input("Nombre del producto", value="", label_visibility="collapsed",
                                  placeholder="Nombre del producto")

    # Sección Ingredientes
    st.markdown('<div class="sidebar-section-title" style="margin-top:16px">Ingredientes</div>',
                unsafe_allow_html=True)

    if "ingredients" not in st.session_state:
        st.session_state.ingredients = [{"name": "", "dosage": "", "unit": "mg"}]

    ingredients = st.session_state.ingredients
    indices_to_remove = []

    for i, ing in enumerate(ingredients):
        col_name, col_dose, col_unit, col_remove = st.columns([4, 1.5, 1, 0.3])

        with col_name:
            ing["name"] = st.text_input(
                f"ing_name_{i}", value=ing["name"],
                placeholder="Ingrediente", label_visibility="collapsed", key=f"ing_name_{i}"
            )
        with col_dose:
            ing["dosage"] = st.text_input(
                f"ing_dose_{i}", value=ing["dosage"],
                placeholder="Dosis", label_visibility="collapsed", key=f"ing_dose_{i}"
            )
        with col_unit:
            ing["unit"] = st.selectbox(
                f"ing_unit_{i}", options=VALID_UNITS,
                index=VALID_UNITS.index(ing["unit"]) if ing["unit"] in VALID_UNITS else 0,
                label_visibility="collapsed", key=f"ing_unit_{i}"
            )
        with col_remove:
            if st.button("×", key=f"ing_remove_{i}"):
                indices_to_remove.append(i)

    if indices_to_remove:
        for i in sorted(indices_to_remove, reverse=True):
            if len(ingredients) > 1:
                ingredients.pop(i)
        st.session_state.ingredients = ingredients
        st.rerun()

    st.session_state.ingredients = ingredients

    # Botón añadir ingrediente
    if st.button("+ Añadir ingrediente", use_container_width=True, key="add_ingredient"):
        st.session_state.ingredients.append({"name": "", "dosage": "", "unit": "mg"})
        st.rerun()

    # Botón analizar
    has_ingredients = any(ing["name"].strip() for ing in ingredients)
    has_product = bool(product_name.strip())
    analyze_clicked = st.button(
        "Analizar Fórmula",
        type="primary",
        use_container_width=True,
        disabled=not (has_product and has_ingredients) or st.session_state.get("pipeline_running", False),
        key="analyze_btn",
    )

    return product_name, ingredients, analyze_clicked
