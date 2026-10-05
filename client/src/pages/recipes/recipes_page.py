import streamlit as st  # type: ignore

from api.recipes import get_recipes
from helpers.ui import render_recipe


st.title("Receitas públicas")

with st.form("public_recipes_list"):
    offset = st.number_input("Offset", min_value=0, value=0, step=1)
    limit = st.number_input("Limit", min_value=1, value=10, step=1)
    list_submit = st.form_submit_button("Listar receitas")

if list_submit:
    recipes = get_recipes(offset=offset, limit=limit)
    if isinstance(recipes, list):
        if not recipes:
            st.info("Nenhuma receita encontrada.")
        for recipe in recipes:
            render_recipe(recipe)
            st.divider()
    else:
        st.error(recipes.get("detail", recipes.get("error", "Falha ao carregar receitas.")))
