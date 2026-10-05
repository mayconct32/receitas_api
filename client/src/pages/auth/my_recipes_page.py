import streamlit as st  # type: ignore

from api.recipes import get_my_recipes
from helpers.ui import render_recipe, require_token


token = require_token()

st.title("Minhas receitas")

if "my_recipes_offset" not in st.session_state:
    st.session_state["my_recipes_offset"] = 0
if "my_recipes_limit" not in st.session_state:
    st.session_state["my_recipes_limit"] = 20

limit = st.number_input(
    "Itens por página",
    min_value=1,
    max_value=100,
    value=st.session_state["my_recipes_limit"],
    step=1,
)

if limit != st.session_state["my_recipes_limit"]:
    st.session_state["my_recipes_limit"] = limit
    st.session_state["my_recipes_offset"] = 0

offset = st.number_input(
    "Offset",
    min_value=0,
    value=st.session_state["my_recipes_offset"],
    step=limit,
)

st.session_state["my_recipes_offset"] = int(offset)

recipes = get_my_recipes(offset=offset, limit=limit, token=token)

if isinstance(recipes, list):
    if not recipes:
        st.info("Você ainda não cadastrou receitas. Use a página **Nova receita** para criar a primeira.")
    for recipe in recipes:
        render_recipe(recipe)
        col_edit, col_delete = st.columns(2)
        with col_edit:
            if st.button("Editar", key=f"edit_{recipe['recipe_id']}"):
                st.session_state["selected_recipe_id"] = recipe["recipe_id"]
                st.switch_page("pages/recipes/update_recipe_page.py")
        with col_delete:
            if st.button("Excluir", key=f"delete_{recipe['recipe_id']}"):
                st.session_state["selected_recipe_id"] = recipe["recipe_id"]
                st.switch_page("pages/recipes/delete_recipe_page.py")
        st.divider()

    col_prev, col_next = st.columns(2)
    with col_prev:
        if offset > 0 and st.button("⬅️ Anterior"):
            st.session_state["my_recipes_offset"] = offset - limit
            st.rerun()
    with col_next:
        if len(recipes) == limit and st.button("Próximo ➡️"):
            st.session_state["my_recipes_offset"] = offset + limit
            st.rerun()
else:
    st.error(recipes.get("detail", recipes.get("error", "Erro ao listar receitas.")))
