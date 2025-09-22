import os
from pathlib import Path

import streamlit as st
from download_helper import read_data_conditionned
from page import Page

import frontend.helper
from backend.generation.fill_template import fill_template
from frontend.description import build_description
from frontend.upload_button import build_upload_button_one_file
from vars import PATH_TMP


def _build_generation_folder_path() -> Path:
    return PATH_TMP / f"generation-{st.session_state.count_generation}"


class PageGeneration(Page):

    def get_name(self):
        return "Génération"

    def reset(self):
        st.session_state.enable_download_generation = False
        st.session_state.generated_file_path = None

    def build_page(self):

        if not "count_generation" in st.session_state:
            st.session_state.count_generation = 1

            while _build_generation_folder_path().exists():
                st.session_state.count_generation += 1

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
            st.session_state.enable_download_generation = False

        filled_config_file = build_upload_button_one_file(
            french_label="fichier de configuration rempli",
            type="xlsx",
            on_change=on_change_uploaded_files,
        )

        template = build_upload_button_one_file(
            french_label="modèles",
            type=["xlsx", "docx"],
            on_change=on_change_uploaded_files,
        )

        # generation
        col1, col2 = frontend.helper.columns(2)

        def generate():
            assert filled_config_file is not None
            assert template is not None

            # call the backend for generation
            generated_file_path = fill_template(
                infos_path_file=filled_config_file.path, template_path=template.path
            )

            # update global variables
            st.session_state.generated_file_path = generated_file_path
            st.session_state.enable_download_generation = True
            st.session_state.count_generation += 1

        # button generation
        col1.button(
            label="Generate",
            on_click=generate,
            disabled=not filled_config_file or not template,
        )

        # button download
        data = read_data_conditionned(
            path=st.session_state.generated_file_path,
            condition=st.session_state.enable_download_generation,
        )

        tn = Path(template.name if template else "toto.txt")
        col2.download_button(
            label="Télécharger génération",
            data=data,
            file_name=f"{tn.stem}_généré{st.session_state.count_generation-1}{tn.suffix}",
            disabled=not st.session_state.enable_download_generation,
            use_container_width=True,
        )
