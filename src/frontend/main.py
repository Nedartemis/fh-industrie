import sys

sys.path.append("./")
sys.path.append("src/")

from typing import List, Tuple

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

import file_helper
from frontend import page_extraction, page_generation
from frontend.page import Page
from vars import PATH_TMP

# pages
pages: List[Page] = [page_extraction.PageExtraction(), page_generation.PageGeneration()]


# launch
if "page" not in st.session_state:
    # Initialize selected page in session state
    st.session_state.page = pages[0]
    st.session_state.page.reset()

    # remove all
    file_helper.rmtree(
        PATH_TMP,
        rm_root=False,
        ext_file_to_avoid_removing_at_the_root=["py", "gitkeep"],
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

pages_details: List[Tuple[DeltaGenerator, Page]] = list(zip(cols, pages))

# build buttons to choose the page
for col, page in pages_details:
    with col:
        # showcase the button of the active page
        type = (
            "primary"
            if st.session_state.page.get_name() == page.get_name()
            else "secondary"
        )

        # build button
        pressed = col.button(page.get_name(), type=type, use_container_width=True)

        # change button
        if pressed and st.session_state.page != page:
            page.reset()
            st.session_state.page = page
            st.rerun()

# build page
st.session_state.page.build_page()
