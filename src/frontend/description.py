import streamlit as st


def build_description(content: str):
    with st.container(border=True):
        st.write(f"""**Description** : {content}""".replace("  ", ""))
