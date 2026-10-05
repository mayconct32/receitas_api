import streamlit as st  # type: ignore

from api.chefs import get_chefs
from helpers.ui import render_chef


st.title("Chefs")

with st.form("list_chefs_form"):
    offset = st.number_input("Offset", min_value=0, value=0, step=1)
    limit = st.number_input("Limit", min_value=1, value=10, step=1)
    list_submit = st.form_submit_button("Listar chefs")

if list_submit:
    chefs = get_chefs(offset, limit)
    if isinstance(chefs, list):
        if not chefs:
            st.info("Nenhum chef encontrado.")
        for chef in chefs:
            render_chef(chef)
            st.divider()
    else:
        st.error(chefs.get("detail", chefs.get("error", "Não foi possível listar chefs.")))
