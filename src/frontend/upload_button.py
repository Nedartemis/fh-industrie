import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

import streamlit as st
from streamlit.elements.widgets.audio_input import UploadedFile

import io_helper
from vars import PATH_TMP

TYPE_ON_CHANGE = Callable[[], None]


@dataclass
class SavedFile:
    name: str
    id: str
    path: Path


# ------------------- Public Method -------------------


def build_upload_button_one_file(
    french_label: str, type: Union[str, List[str]], on_change: TYPE_ON_CHANGE
) -> Optional[SavedFile]:
    res = _build_upload_button(
        french_label, type=type, on_change=on_change, accept_multiple_files=False
    )
    return res[0] if res else None


def build_upload_button_multiple_files(
    french_label: str, type: Union[str, List[str]], on_change: TYPE_ON_CHANGE
) -> List[SavedFile]:
    return _build_upload_button(
        french_label, type=type, on_change=on_change, accept_multiple_files=True
    )


# ------------------- Private Method -------------------


def _build_upload_button(
    french_label: str,
    type: Union[str, List[str]],
    on_change: TYPE_ON_CHANGE,
    accept_multiple_files: bool,
) -> List[Path]:

    # create button
    col = st.container(border=True)
    col.markdown(
        f"<h3 style='font-size:16px; '>📂 Déposer {french_label}</h3>",
        unsafe_allow_html=True,
    )
    uploaded_file = col.file_uploader(
        label="Must not be seen",
        type=type,
        label_visibility="collapsed",
        accept_multiple_files=accept_multiple_files,
        on_change=on_change,
        key=french_label,
    )

    # no file uploaded yet
    if uploaded_file is None:
        return []

    # harmonize (element -> list ; list -> list)
    if not isinstance(uploaded_file, list):
        uploaded_file = [uploaded_file]

    saved_files: List[SavedFile] = []

    # save the uploaded files
    for file in uploaded_file:

        # build the path to save
        filename = Path(file.name)
        ext = filename.suffix.lower()[1:]

        filename_dst = (
            f"{filename.stem}-{file.file_id}{filename.suffix if ext != 'zip' else ''}"
        )
        path_dst = PATH_TMP / filename_dst

        # already saved ?
        if not path_dst.exists():
            print(f"Saving uploaded file : {filename_dst}")

            # save it according to its extension
            if ext in ["xlsx", "pdf"]:
                io_helper.write(file.getvalue(), path_dst=path_dst)
            elif ext == "zip":
                _extract_zip_file(file, path_dst=path_dst)
            else:
                raise RuntimeError(f"The extension '{ext}' is not supported.")

        # store the path(s)
        if ext == "zip":
            for rep in os.listdir(path=path_dst):
                sf = SavedFile(name=rep, id=file.file_id, path=path_dst / rep)
                saved_files.append(sf)
        else:
            sf = SavedFile(name=file.name, id=file.file_id, path=path_dst)
            saved_files.append(sf)

    return saved_files


def _extract_zip_file(uploaded_file: UploadedFile, path_dst: Path) -> None:
    try:
        io_helper.extract_zip_file(uploaded_file.getvalue(), path_dst=path_dst)
    except zipfile.BadZipFile:
        # print("Le fichier enregistré n'est pas un fichier ZIP valide.")
        print("The uploaded file is not a valid ZIP file.")
