from typing import List

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def columns(n: int) -> List[DeltaGenerator]:
    st.markdown(
        """
    <style>
    div.stButton > button {
        width: 100%;
        height: 100%;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    return st.columns(n, border=False)
