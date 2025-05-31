import io
import os
import zipfile
from typing import Any, Callable, List, Optional

import streamlit as st

from backend.backend import Backend
from frontend.logger import LogLevel, create_console, log
from vars import PATH_CONFIG_FILE, PATH_TMP

# Function to add a log entry


# Detect app start
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
    event_action: Callable,
    types_file: Optional[List[str]] = None,
    conditions: List[str] = list(),
) -> str:

    event_name = "event_" + name
    event_condition = "condition_" + name

    if not all(st.session_state.get(cond) for cond in conditions):
        return event_condition

    col1 = st.container(border=True)

    def on_change(*args, **kwargs):
        # print(f"On change : {event_name}")
        st.session_state[event_name] = True

    uploaded_file = col1.file_uploader(
        f"**{label_upload}**",
        type=types_file,
        label_visibility="visible",
        on_change=on_change,
    )

    if st.session_state.get(event_name, False) and uploaded_file is not None:
        st.session_state[event_name] = False
        event_action(uploaded_file)
        log(LogLevel.INFO, f"Le fichier '{uploaded_file.name}' a été enregistré.")
        st.session_state[event_condition] = True

    return event_condition


def extract_zip_file(uploaded_file):
    try:
        with zipfile.ZipFile(io.BytesIO(uploaded_file.getvalue())) as zf:
            zf.extractall(path=PATH_TMP)
    except zipfile.BadZipFile:
        log(LogLevel.ERROR, "Le fichier enregistré n'est pas un fichier ZIP valide.")


def dowload_config_file(uploaded_file):
    with open(PATH_CONFIG_FILE, "wb") as f:
        f.write(uploaded_file.getvalue())


def dowload_template_file(uploaded_file):
    path = PATH_TMP / uploaded_file.name
    with open(path, "wb") as f:
        f.write(uploaded_file.getvalue())
    backend.set_template_path(str(path))


def add_layer_download(
    name: str,
    label_button: str,
    callback: Callable[[], Optional[str]],
    conditions: List[str] = list(),
) -> str:

    event_path = name + "_path"
    event_condition = name + "_condition"

    if not all(st.session_state.get(cond) for cond in conditions):
        return event_condition

    container = st.container(border=True)
    col1, col2, col3 = container.columns(3, border=False)

    def func():
        st.session_state[event_path] = callback()

    col1.button(label=label_button, on_click=func)

    # Download button to serve the file
    path = st.session_state.get(event_path, None)
    if not path:
        col2.markdown("**Pas de fichier généré**")
    else:
        filename = os.path.basename(path)
        col2.markdown(f"**Fichier généré:** {filename}")
        st.session_state[event_condition] = True

        try:
            with open(path, "rb") as f:
                file_data = f.read()
        except FileNotFoundError:
            st.error(f"Fichier pas trouvé au chemin: {path}")

        col3.download_button(
            label="Télécharger",
            data=file_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=name + "_key",
        )

    return event_condition


def extract_infos() -> Optional[str]:
    try:
        return backend.extract_infos()
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
    callback=extract_infos,
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
    callback=fill_template,
    conditions=[template_cond],
)


create_console()
