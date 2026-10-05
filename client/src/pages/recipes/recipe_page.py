import streamlit as st  # type: ignore

from api.recipes import get_recipe
from helpers.ui import render_recipe


st.title("Buscar receita por ID")

with st.form("recipe_by_id_form"):
    recipe_id = st.text_input("ID da receita", placeholder="Digite o ID da receita")
    search_submit = st.form_submit_button("Buscar")

if search_submit and recipe_id.strip():
    recipe = get_recipe(recipe_id.strip())
    if isinstance(recipe, dict) and "recipe_id" in recipe:
        st.subheader("Detalhes da receita")
        render_recipe(recipe)
    else:
        st.error(recipe.get("detail", recipe.get("error", "Receita não encontrada.")))
