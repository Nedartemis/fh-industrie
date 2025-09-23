from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from backend.excel_manager import ExcelManager
from frontend.logger import LogLevel


@dataclass
class InfoToExtractData:
    instruction: str
    name: str
    desciption: str
    label_source: str
    value: str
    long: bool


OFFSET_COLUMN_INFO_VALUE = 3
TYPE_FILES_PATH = Dict[str, str]
TYPE_FILES_INFOS = Dict[str, List[InfoToExtractData]]


# ------------------- Public Method -------------------


def read_config_file(
    path_config_file: Path, path_folder_sources: Path
) -> Tuple[TYPE_FILES_PATH, TYPE_FILES_INFOS]:

    # open the excel
    em = ExcelManager(path_config_file)

    # read the source page : read the label and the path of each file
    files_path_all = _read_config_file_source_page(em)

    # read the info page
    files_infos_all = _read_config_file_files_infos_per_label(em)

    # -- error detection (files not supported, ...)
    files_path, files_infos = _error_detection_config_file_extraction(
        files_path_all, files_infos_all, path_folder_sources
    )

    return files_path, files_infos


def read_config_file_files_infos_values(em: ExcelManager) -> Dict[str, str]:

    infos_all_details = _manage_config_file_info_page(em)
    return {
        info.name: info.value
        for info in infos_all_details
        if info.value and info.value != "None"
    }


def fill_config_file(path_config_file: Path, infos: dict, path_output: Path) -> None:

    # open
    em = ExcelManager(path_config_file)

    # write
    _manage_config_file_info_page(em, get_info_value_to_write=infos.get)

    # save
    em.save(path_output)
    em.wb.close()


# ------------------- Private Method -------------------


def _manage_config_file_info_page(
    em: ExcelManager,
    get_info_value_to_write: Callable[[str], Optional[str]] = lambda _: None,
) -> List[InfoToExtractData]:

    ws = em.get_worksheet("Infos à extraire")

    infos: List[InfoToExtractData] = []

    column = 2
    for current_row in range(1, len(ws.row_dimensions)):
        # retrieve metadata and data of the info
        info = InfoToExtractData(
            instruction=em.get_text(ws, current_row, column - 1),
            name=em.get_text(ws, current_row, column),
            desciption=em.get_text(ws, current_row, column + 1),
            label_source=em.get_text(ws, current_row, column + 2),
            value=em.get_text(ws, current_row, column + OFFSET_COLUMN_INFO_VALUE),
            long=em.get_text(ws, current_row, column - 1) == "X",
        )

        if info.name is None or info.name == "None":
            continue

        # store infos
        infos.append(info)

        # potential write value
        info_to_write = get_info_value_to_write(info.name)
        if info_to_write is not None:
            ws.cell(current_row, column + OFFSET_COLUMN_INFO_VALUE, value=info_to_write)

    return infos


def _read_config_file_source_page(em: ExcelManager) -> TYPE_FILES_PATH:
    ws = em.get_worksheet(name="Sources")

    files_path: Dict[str, str] = {}
    column, current_row = 2, 3
    while True:
        name_source = ws.cell(current_row, column).value
        path_source = ws.cell(current_row, column + 1).value
        if not name_source or not path_source:
            break
        current_row += 1

        files_path[name_source] = path_source

    return files_path


def _read_config_file_files_infos_per_label(em: ExcelManager) -> TYPE_FILES_INFOS:

    infos = _manage_config_file_info_page(em)

    files_infos = {}
    for info in infos:

        # if the value has not been yet filled
        if not (info.value is None or info.value == "None"):
            continue

        if not info.label_source in files_infos:
            files_infos[info.label_source] = []

        files_infos[info.label_source].append(info)

    return files_infos


def _error_detection_config_file_extraction(
    files_path: TYPE_FILES_PATH,
    files_infos: TYPE_FILES_INFOS,
    path_folder_sources: Path,
) -> Tuple[TYPE_FILES_PATH, TYPE_FILES_INFOS]:

    # check and filter files path
    files_path_filtered = {}
    for name_source, path in files_path.items():
        if not path.endswith(".pdf"):
            p = Path(path)
            print(
                LogLevel.ERROR,
                f"L'extension '{p.suffix}' du fichier '{p.name}' n'est pas supporté en extraction d'information",
            )
        elif not (path_folder_sources / path).exists():
            print(
                LogLevel.ERROR,
                f"Le fichier {path} n'existe pas dans l'arbre de fichier donné.",
            )
        elif not name_source in files_infos.keys():
            print(
                LogLevel.WARNING,
                f"Aucune information est à extraire de la source de fichier '{name_source}'.",
            )
        else:
            files_path_filtered[name_source] = path

    # check and filter files infos
    files_infos_filtered = {}
    for name_source, info in files_infos.items():
        if name_source not in files_path:
            print(
                LogLevel.ERROR,
                f"Le label '{name_source}' n'est pas une source présente dans la page des sources.",
            )
            continue
        files_infos_filtered[name_source] = info

    return files_path_filtered, files_infos_filtered


if __name__ == "__main__":
    from vars import PATH_CONFIG_FILE

    files_path, files_infos = read_config_file(PATH_CONFIG_FILE)

    print(f"files_path : {files_path}")
    print(f"files_infos : {files_infos}")
