import streamlit as st  # type: ignore

from api.chefs import post_chef


st.title("Cadastrar")

with st.form(key="register_form"):
    username = st.text_input("Nome de usuário")
    email = st.text_input("E-mail")
    password = st.text_input("Senha", type="password")
    input_button_submit = st.form_submit_button("Cadastrar")

if input_button_submit:
    response = post_chef(username, email, password)
    if "data" in response:
        st.success("Cadastro realizado com sucesso! Faça login para continuar.")
        st.switch_page("pages/auth/login_page.py")
    else:
        st.markdown(f":red[Erro! {response.get('detail', response.get('error', response))}]")
