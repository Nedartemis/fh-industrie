import os
import zipfile
from typing import Callable, List, Optional

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

import helper
from backend.backend import Backend
from frontend.logger import LogLevel, create_console, log
from vars import PATH_CONFIG_FILE, PATH_TMP

if "app_just_started" not in st.session_state:
    print("-----------------")
    st.session_state.app_launched = True
    st.session_state.app_just_started = True
    st.session_state.logs = []
    log(LogLevel.INFO, "This is the first launch of the app.")

    backend = Backend()
    st.session_state.backend = backend
else:
    st.session_state.app_just_started = False
    backend = st.session_state.backend

# Page config
TITLE = "Demo"

st.set_page_config(page_title=TITLE, layout="centered")

st.title(TITLE)


def add_layer_upload(
    name: str,
    label_upload: str,
    event_action: Callable[[UploadedFile], None],
    types_file: Optional[List[str]] = None,
    conditions: List[str] = list(),
) -> str:

    event_name = "event_" + name
    event_condition = "condition_" + name

    # conditions
    if not all(st.session_state.get(cond) for cond in conditions):
        return event_condition

    def on_change(*args, **kwargs):
        st.session_state[event_name] = True

    # container
    col1 = st.container(border=True)

    # uploader
    uploaded_file = col1.file_uploader(
        f"**{label_upload}**",
        type=types_file,
        label_visibility="visible",
        on_change=on_change,
    )

    # on change and there is a new uploaded file
    if st.session_state.get(event_name) and uploaded_file is not None:
        st.session_state[event_name] = False
        event_action(uploaded_file)
        log(LogLevel.INFO, f"Le fichier '{uploaded_file.name}' a été enregistré.")
        st.session_state[event_condition] = True

    return event_condition


def extract_zip_file(
    uploaded_file: UploadedFile,
) -> None:
    try:
        helper.extract_zip_file(uploaded_file.getvalue(), PATH_TMP)
    except zipfile.BadZipFile:
        log(LogLevel.ERROR, "Le fichier enregistré n'est pas un fichier ZIP valide.")


def dowload_config_file(uploaded_file: UploadedFile) -> None:
    helper.write(uploaded_file.getvalue(), path_dst=PATH_CONFIG_FILE)


def dowload_template_file(uploaded_file: UploadedFile) -> None:
    path = PATH_TMP / uploaded_file.name
    helper.write(uploaded_file.getvalue(), path_dst=path)
    backend.set_template_path(str(path))


def add_layer_download(
    name: str,
    label_button: str,
    fill_file_and_get_path: Callable[[], Optional[str]],
    conditions: List[str] = list(),
) -> str:

    event_path = name + "_path"
    event_condition = name + "_condition"

    if not all(st.session_state.get(cond) for cond in conditions):
        return event_condition

    def on_click():
        st.session_state[event_path] = fill_file_and_get_path()

    # container and sub containers
    container = st.container(border=True)
    col1, col2, col3 = container.columns(3, border=False)

    # action button
    col1.button(label=label_button, on_click=on_click)

    path = st.session_state.get(event_path)
    if not path:
        # the action button has not been clicked or something failed
        col2.markdown("**Pas de fichier généré**")
        return event_condition

    # the action button has been clicked and the path file given
    filename = os.path.basename(path)
    col2.markdown(f"**Fichier généré:** {filename}")
    st.session_state[event_condition] = True

    try:
        file_data = helper.read(path)
    except FileNotFoundError:
        st.error(f"Fichier pas trouvé au chemin: {path}")
        return event_condition

    # download button
    col3.download_button(
        label="Télécharger",
        data=file_data,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    return event_condition


def extract_infos_from_tree_and_config_file() -> Optional[str]:
    try:
        return backend.extract_infos_from_tree_and_config_file()
    except Exception as e:
        log(LogLevel.ERROR, e.args[0])
        return None


def fill_template() -> Optional[str]:
    try:
        return backend.fill_template()
    except Exception as e:
        log(LogLevel.ERROR, e.args[0])
        return None


# layers
zip_cond = add_layer_upload(
    "enter_zip_file",
    "Entrer arborescence zip",
    event_action=extract_zip_file,
    types_file=["zip"],
)
config_cond = add_layer_upload(
    "enter_config_file",
    "Entrer fichier configuration excel",
    event_action=dowload_config_file,
    types_file=["xlsx"],
)

extract_infos_cond = add_layer_download(
    "extract_infos",
    label_button="Extraire infos",
    fill_file_and_get_path=extract_infos_from_tree_and_config_file,
    conditions=[config_cond],
)

template_cond = add_layer_upload(
    "enter_template_file",
    "Entrer modèle fichier",
    event_action=dowload_template_file,
    types_file=["docx", "xlsx"],
    conditions=[extract_infos_cond],
)

add_layer_download(
    "fill_template",
    label_button="Remplir modèle",
    fill_file_and_get_path=fill_template,
    conditions=[template_cond],
)


create_console()
