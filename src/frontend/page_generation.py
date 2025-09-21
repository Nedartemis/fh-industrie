import streamlit as st

import frontend.helper
from frontend.description import build_description
from frontend.upload_button import (
    build_upload_button_multiple_files,
    build_upload_button_one_file,
)


def build_page():

    if not "enable_download_generation" in st.session_state:
        st.session_state.enable_download_generation = False
        st.session_state.count_generation = 0

    # description
    build_description(
        content="""A partir
        - d'un **fichier de configuration rempli** avec les informations extraites et/ou ajoutées manuellement,
        - d'un ou plusieurs documents faisant office de **modèles**,

        cette page permet de générer des documents en récupérant les informations données dans le fichier de configuration et en les insérant dans les modèles.
        """
    )

    # uploaders
    def on_change_uploaded_files():
        st.session_state.enable_download_extraction = False

    filled_config_file = build_upload_button_one_file(
        "fichier de configuration rempli", on_change=on_change_uploaded_files
    )

    templates = build_upload_button_multiple_files(
        "modèles", on_change=on_change_uploaded_files
    )

    # generation
    col1, col2 = frontend.helper.columns(2)

    def generate():
        st.session_state.enable_download_extraction = True
        st.session_state.count_generation += 1

    col1.button(
        label="Generate",
        on_click=generate,
        disabled=not filled_config_file or not templates,
    )

    col2.download_button(
        label="Télécharger génération",
        data=b"generation",
        file_name=f"generation{st.session_state.count_generation}.txt",
        disabled=not st.session_state.enable_download_extraction,
        use_container_width=True,
    )
