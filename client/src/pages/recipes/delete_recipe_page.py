import streamlit as st  # type: ignore

from api.recipes import delete_recipe, get_my_recipes
from helpers.ui import render_recipe, require_token


token = require_token()

st.title("Excluir receita")

recipes = get_my_recipes(offset=0, limit=100, token=token)

if not isinstance(recipes, list) or not recipes:
    st.info("Você ainda não possui receitas para excluir.")
    st.stop()

recipe_ids = [recipe["recipe_id"] for recipe in recipes]
preselected = st.session_state.get("selected_recipe_id")
index = recipe_ids.index(preselected) if preselected in recipe_ids else 0

selected_recipe_id = st.selectbox(
    "Selecione a receita",
    options=recipe_ids,
    index=index,
    format_func=lambda rid: next(
        (recipe["recipe_name"] for recipe in recipes if recipe["recipe_id"] == rid), rid
    ),
)
selected_recipe = next(recipe for recipe in recipes if recipe["recipe_id"] == selected_recipe_id)

render_recipe(selected_recipe)
st.divider()

if st.button("Excluir receita", type="primary"):
    response = delete_recipe(selected_recipe_id, token)
    if isinstance(response, dict) and ("message" in response or "detail" in response):
        st.success("Receita removida com sucesso!")
        st.session_state.pop("selected_recipe_id", None)
        st.switch_page("pages/auth/my_recipes_page.py")
    else:
        st.error(response.get("detail", response.get("error", "Erro ao remover receita.")))
