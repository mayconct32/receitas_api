import streamlit as st  # type: ignore

from api.chefs import get_myself, put_chef
from helpers.ui import require_token


token = require_token()

st.title("Editar perfil")

current_chef = get_myself(token)

if not isinstance(current_chef, dict) or "chef_id" not in current_chef:
    st.error(current_chef.get("detail", current_chef.get("error", "Não foi possível carregar seu perfil.")))
    st.stop()

with st.form("update_profile_form"):
    chef_name = st.text_input("Nome do chef", value=current_chef["chef_name"])
    email = st.text_input("E-mail", value=current_chef["email"])
    password = st.text_input("Nova senha (opcional)", type="password")
    update_submit = st.form_submit_button("Salvar alterações")

if update_submit:
    response = put_chef(
        chef_id=current_chef["chef_id"],
        token=token,
        chef_name=chef_name,
        email=email,
        password=password,
    )
    if "chef_id" in response:
        st.success("Perfil atualizado com sucesso!")
        st.switch_page("pages/auth/profile_page.py")
    else:
        st.error(response.get("detail", response.get("error", "Falha ao atualizar perfil.")))
