import sys

sys.path.append("./")
sys.path.append("src/")

import streamlit as st

from frontend import page_extraction, page_generation

PAGE1 = "Extraction"
PAGE2 = "Génération"

# --- Initialize selected page in session state
if "page" not in st.session_state:
    st.session_state.page = PAGE1

# --- Navigation Buttons at the Top (Rectangles)
st.markdown(
    """
<style>
div.stButton > button {
    width: 100%;
    height: 60px;
    border-radius: 8px;
    font-size: 18px;
    font-weight: bold;
}
</style>
""",
    unsafe_allow_html=True,
)
cols = st.columns(2)

pages_details = list(
    zip(
        cols,
        [PAGE1, PAGE2],
        [page_extraction.build_page, page_generation.build_page],
    )
)

# showcase the button of the active page
for col, page, _ in pages_details:
    with col:
        type = "primary" if st.session_state.page == page else "secondary"
        if st.button(page, type=type):
            st.session_state.page = page
            st.rerun()

# build pages
for _, page, build_page in pages_details:
    if st.session_state.page == page:
        build_page()
        break
