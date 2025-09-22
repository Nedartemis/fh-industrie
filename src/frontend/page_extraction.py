import os
from pathlib import Path

import streamlit as st
from download_helper import read_data_conditionned

import frontend.helper
import io_helper
from backend.extract_info_from_config_file_and_documents import (
    extract_infos_from_tree_and_config_file,
)
from frontend.description import build_description
from frontend.upload_button import (
    build_upload_button_multiple_files,
    build_upload_button_one_file,
)
from vars import PATH_TMP


def _build_extraction_folder_path() -> Path:
    return PATH_TMP / f"extraction-{st.session_state.count_extraction}"


def build_page():

    if not "enable_download_extraction" in st.session_state:
        st.session_state.infos_path_file = None
        st.session_state.enable_download_extraction = False
        st.session_state.count_extraction = 1

        while _build_extraction_folder_path().exists():
            st.session_state.count_extraction += 1

    # description
    build_description(
        content="""
        A partir
        - d'un **fichier de configuration** précisant quelles informations extraire et où les chercher,
        - de **documents** contenant les informations,

        cette page permet d'**extraire** des informations et de les stocker dans un fichier excel.
        """
    )

    # uploaders
    def on_change_uploaded_files():
        st.session_state.enable_download_extraction = False

    config_file = build_upload_button_one_file(
        "fichier de configuration", type="xlsx", on_change=on_change_uploaded_files
    )

    documents = build_upload_button_multiple_files(
        "documents", type=["pdf", "xlsx", "zip"], on_change=on_change_uploaded_files
    )

    # extraction
    col1, col2 = frontend.helper.columns(2)

    def extract():
        assert config_file is not None
        assert documents != []

        # create folder of the extraction
        dir_extraction = _build_extraction_folder_path()
        os.makedirs(dir_extraction)

        # create symbolic links
        for doc in documents:
            os.symlink(src=doc.path, dst=dir_extraction / doc.name)

        # call the backend for extraction
        infos_file_path = extract_infos_from_tree_and_config_file(
            path_config_file=config_file.path, path_folder_sources=dir_extraction
        )

        # update global variables
        st.session_state.infos_path_file = infos_file_path
        st.session_state.enable_download_extraction = True
        st.session_state.count_extraction += 1

    # button extraction
    col1.button(
        label="Extraire",
        on_click=extract,
        disabled=not config_file or not documents,
    )

    # button download extraction
    data = read_data_conditionned(
        path=st.session_state.infos_path_file,
        condition=st.session_state.enable_download_extraction,
    )

    col2.download_button(
        label="Télécharger extraction",
        data=data,
        file_name=f"extraction{st.session_state.count_extraction-1}.xlsx",
        disabled=not st.session_state.enable_download_extraction,
        use_container_width=True,
    )
