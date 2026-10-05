import streamlit as st  # type: ignore

from api.chefs import get_chef
from helpers.ui import render_chef


st.title("Buscar chef por ID")

with st.form("chef_by_id_form"):
    chef_id = st.text_input("ID do chef", placeholder="Digite o chef_id")
    submitted = st.form_submit_button("Buscar")

if submitted and chef_id.strip():
    chef = get_chef(chef_id.strip())
    if isinstance(chef, dict) and "chef_id" in chef:
        st.subheader("Resultado da busca")
        render_chef(chef)
    else:
        st.error(chef.get("detail", chef.get("error", "Chef não encontrado.")))
