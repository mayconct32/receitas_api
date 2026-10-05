import streamlit as st  # type: ignore

from api.chefs import auth_chef


st.title("Entrar")

with st.form(key="login_form"):
    email = st.text_input("E-mail")
    password = st.text_input("Senha", type="password")
    input_button_submit = st.form_submit_button("Entrar")

if input_button_submit:
    response = auth_chef(email, password)
    if "data" in response:
        st.session_state.token = response["data"]["access_token"]
        st.switch_page("pages/recipes/recipes_page.py")
    else:
        st.markdown(f":red[Erro! {response.get('detail', response.get('error', response))}]")
