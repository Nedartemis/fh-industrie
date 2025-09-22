import sys

sys.path.append("./")
sys.path.append("src/")

import streamlit as st

import file_helper
from frontend import page_extraction, page_generation
from vars import PATH_TMP

# pages
PAGE1 = "Extraction"
PAGE2 = "Génération"

# launch
if "page" not in st.session_state:
    # Initialize selected page in session state
    st.session_state.page = PAGE1

    # remove all
    file_helper.rmtree(
        PATH_TMP, rm_root=False, file_to_avoid_removing_at_the_root=["py"]
    )


# Navigation Buttons at the Top (Rectangles)
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
