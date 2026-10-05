import streamlit as st  # type: ignore

from api.chefs import get_myself
from helpers.ui import clear_auth_session, require_token


token = require_token()

st.title("Meu perfil")

current_chef = get_myself(token)

if not isinstance(current_chef, dict) or "chef_id" not in current_chef:
    st.error(current_chef.get("detail", current_chef.get("error", "Não foi possível carregar seu perfil.")))
    st.stop()

st.write(f"**Nome:** {current_chef.get('chef_name')}")
st.write(f"**E-mail:** {current_chef.get('email')}")
st.write(f"**ID:** {current_chef.get('chef_id')}")

st.divider()

if st.button("Sair"):
    clear_auth_session()
    st.switch_page("pages/auth/login_page.py")
