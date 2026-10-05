import streamlit as st  # type: ignore


chefs_page = st.Page("pages/chefs/chefs_page.py", title="Chefs")
chef_page = st.Page("pages/chefs/chef_page.py", title="Detalhe do chef")

recipes_page = st.Page("pages/recipes/recipes_page.py", title="Receitas públicas")
recipe_page = st.Page("pages/recipes/recipe_page.py", title="Detalhe da receita")
add_recipe_page = st.Page("pages/recipes/add_recipe_page.py", title="Nova receita")
update_recipe_page = st.Page("pages/recipes/update_recipe_page.py", title="Atualizar receita")
delete_recipe_page = st.Page("pages/recipes/delete_recipe_page.py", title="Excluir receita")

register_page = st.Page("pages/auth/register_page.py", title="Cadastrar")
register_page2 = st.Page("pages/auth/register_page.py", title="Cadastrar", visibility="hidden")
my_recipes_page = st.Page("pages/auth/my_recipes_page.py", title="Minhas receitas")
profile_page = st.Page("pages/auth/profile_page.py", title="Meu perfil")
edit_profile_page = st.Page("pages/auth/edit_profile_page.py", title="Editar perfil")
delete_account_page = st.Page("pages/auth/delete_account_page.py", title="Excluir conta")
login_page = st.Page("pages/auth/login_page.py", title="Entrar")
login_page2 = st.Page("pages/auth/login_page.py", title="Entrar", visibility="hidden")

if "token" in st.session_state:
    pg = st.navigation({
        "Receitas": [
            recipes_page,
            recipe_page,
            my_recipes_page,
            add_recipe_page,
            update_recipe_page,
            delete_recipe_page,
        ],
        "Chefs": [
            chefs_page,
            chef_page,
        ],
        "Conta": [
            profile_page,
            edit_profile_page,
            delete_account_page,
            register_page2,
            login_page2
        ],
    })
else:
    pg = st.navigation({
        "Receitas": [
            recipes_page,
            recipe_page,
        ],
        "Chefs": [
            chefs_page,
            chef_page,
        ],
        "Conta": [
            register_page,
            login_page,
        ],
    })

pg.run()
