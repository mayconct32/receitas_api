import streamlit as st  # type: ignore

from api.recipes import add_recipe
from helpers.ui import parse_ingredients, parse_instructions, require_token


token = require_token()

st.title("Nova receita")

with st.form("add_recipe_form"):
    recipe_name = st.text_input("Nome da receita")
    description = st.text_area("Descrição")
    prep_time = st.text_input("Tempo de preparo (HH:MM:SS)", value="00:15:00")
    instructions_text = st.text_area(
        "Instruções (uma por linha)",
        value="1. Misture os ingredientes\n2. Prepare a massa\n3. Asse por 20 minutos",
    )
    ingredients_text = st.text_area(
        "Ingredientes (um por linha no formato: nome: quantidade)",
        value="farinha: 500g\nleite: 250ml\novo: 2 unidades",
    )
    image = st.file_uploader("Imagem da receita", type=["png", "jpg", "jpeg"])
    save_submit = st.form_submit_button("Criar receita")

if save_submit:
    recipe_data = {
        "recipe_name": recipe_name,
        "description": description,
        "prep_time": prep_time,
        "instructions": parse_instructions(instructions_text),
        "ingredients": parse_ingredients(ingredients_text),
    }

    response = add_recipe(recipe_data, token, image=image)
    if "recipe_id" in response:
        st.success("Receita criada com sucesso!")
        st.session_state["selected_recipe_id"] = response["recipe_id"]
        st.switch_page("pages/auth/my_recipes_page.py")
    else:
        st.error(response.get("detail", response.get("error", "Erro ao criar receita.")))
