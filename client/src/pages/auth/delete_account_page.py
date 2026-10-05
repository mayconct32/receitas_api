import streamlit as st  # type: ignore

from api.chefs import delete_chef, get_myself
from helpers.ui import clear_auth_session, require_token, response_has_error


token = require_token()

st.title("Excluir conta")

current_chef = get_myself(token)

if not isinstance(current_chef, dict) or "chef_id" not in current_chef:
    st.error(current_chef.get("detail", current_chef.get("error", "Não foi possível carregar seu perfil.")))
    st.stop()

st.warning(
    f"Esta ação é irreversível. A conta **{current_chef.get('chef_name')}** "
    "e seu acesso serão removidos."
)

confirm = st.checkbox("Confirmo que desejo excluir minha conta permanentemente.")

if st.button("Excluir conta", type="primary", disabled=not confirm):
    response = delete_chef(current_chef["chef_id"], token)
    if not response_has_error(response):
        clear_auth_session()
        st.success("Conta excluída com sucesso.")
        st.switch_page("pages/auth/login_page.py")
    else:
        st.error(response.get("detail", response.get("error", "Não foi possível excluir a conta.")))
