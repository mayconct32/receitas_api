import streamlit as st  # type: ignore


def response_has_error(response):
    if not isinstance(response, dict):
        return True
    return "error" in response or "detail" in response


def clear_auth_session():
    if st is not None and hasattr(st, "session_state"):
        for key in list(st.session_state.keys()):
            st.session_state.pop(key, None)


def parse_instructions(raw_text: str):
    instructions = []
    for line in raw_text.splitlines():
        value = line.strip()
        if not value:
            continue
        if "." in value:
            step_number, description = value.split(".", 1)
            try:
                instructions.append({
                    "step_number": int(step_number.strip()),
                    "description": description.strip(),
                })
            except ValueError:
                instructions.append({
                    "step_number": len(instructions) + 1,
                    "description": value,
                })
        else:
            instructions.append({
                "step_number": len(instructions) + 1,
                "description": value,
            })
    return instructions


def parse_ingredients(raw_text: str):
    ingredients = []
    for line in raw_text.splitlines():
        value = line.strip()
        if not value:
            continue
        if ":" in value:
            ingredient_name, quantity = value.split(":", 1)
            ingredients.append({
                "ingredient_name": ingredient_name.strip(),
                "quantity": quantity.strip(),
            })
        else:
            ingredients.append({
                "ingredient_name": value,
                "quantity": "a gosto",
            })
    return ingredients


def render_recipe(recipe):
    st.write(f"### {recipe.get('recipe_name', 'Receita')}")
    st.write(f"**Descrição:** {recipe.get('description', '')}")
    st.write(f"**Tempo de preparo:** {recipe.get('prep_time', '')}")
    st.write("**Ingredientes:**")
    for ingredient in recipe.get("ingredients", []):
        st.write(f"- {ingredient.get('ingredient_name', '')}: {ingredient.get('quantity', '')}")
    st.write("**Instruções:**")
    for instruction in recipe.get("instructions", []):
        st.write(f"{instruction.get('step_number', '')}. {instruction.get('description', '')}")
    st.write(f"**Chef ID:** {recipe.get('chef_id')}")
    if recipe.get("image_url"):
        st.image(recipe["image_url"], width=300)


def render_chef(chef):
    st.write(f"**{chef.get('chef_name', 'Chef')}**")
    st.write(f"E-mail: {chef.get('email')}")
    st.write(f"ID: {chef.get('chef_id')}")


def require_token():
    if "token" not in st.session_state:
        st.warning("Você precisa entrar antes de acessar esta página.")
        st.stop()
    return st.session_state["token"]
