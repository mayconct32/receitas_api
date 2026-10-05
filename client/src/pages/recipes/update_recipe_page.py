import streamlit as st  # type: ignore

from api.recipes import get_my_recipes, update_recipe
from helpers.ui import parse_ingredients, parse_instructions, require_token


token = require_token()

st.title("Atualizar receita")

recipes = get_my_recipes(offset=0, limit=100, token=token)

if not isinstance(recipes, list) or not recipes:
    st.info("Você ainda não possui receitas para atualizar.")
    st.stop()

recipe_by_id = {recipe["recipe_id"]: recipe for recipe in recipes}
recipe_ids = list(recipe_by_id)
preselected_id = st.session_state.get("selected_recipe_id")
selected_index = recipe_ids.index(preselected_id) if preselected_id in recipe_ids else 0

selected_recipe_id = st.selectbox(
    "Selecione a receita",
    options=recipe_ids,
    index=selected_index,
    format_func=lambda recipe_id: recipe_by_id[recipe_id]["recipe_name"],
)
selected_recipe = recipe_by_id[selected_recipe_id]

with st.form("update_recipe_form"):
    recipe_name = st.text_input(
        "Nome da receita",
        value=selected_recipe.get("recipe_name", ""),
    )
    description = st.text_area(
        "Descrição",
        value=selected_recipe.get("description", ""),
    )
    prep_time = st.text_input(
        "Tempo de preparo (HH:MM:SS)",
        value=selected_recipe.get("prep_time", "00:15:00"),
    )
    instructions_text = st.text_area(
        "Instruções (uma por linha)",
        value="\n".join(
            f"{instruction['step_number']}. {instruction['description']}"
            for instruction in selected_recipe.get("instructions", [])
        ),
    )
    ingredients_text = st.text_area(
        "Ingredientes (um por linha no formato: nome: quantidade)",
        value="\n".join(
            f"{ingredient['ingredient_name']}: {ingredient['quantity']}"
            for ingredient in selected_recipe.get("ingredients", [])
        ),
    )
    image = st.file_uploader(
        "Nova imagem da receita (opcional)",
        type=["png", "jpg", "jpeg"],
    )
    update_submit = st.form_submit_button("Salvar alterações")

if update_submit:
    recipe_data = {
        "recipe_name": recipe_name,
        "description": description,
        "prep_time": prep_time,
        "instructions": parse_instructions(instructions_text),
        "ingredients": parse_ingredients(ingredients_text),
    }

    response = update_recipe(selected_recipe_id, recipe_data, token, image=image)

    if "recipe_id" in response:
        st.success("Receita atualizada com sucesso!")
        st.session_state.pop("selected_recipe_id", None)
        st.switch_page("pages/auth/my_recipes_page.py")
    else:
        st.error(response.get("detail", response.get("error", "Erro ao atualizar receita.")))
