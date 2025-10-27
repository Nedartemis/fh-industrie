from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

from backend.excel_manager import ExcelManager, Worksheet
from frontend.logger import LogLevel


@dataclass
class InfoToExtractData:
    instruction: str
    name: str
    desciption: str
    label_source: str
    value: str
    exact: bool


TYPE_INFOS_VALUE = Dict[str, Union[str, List[dict]]]
COLUMN_NAME_INFO = 2
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
    files_infos_all = _read_config_file_info_page_and_preprocess(em)

    # -- error detection (files not supported, ...)
    files_path, files_infos = _error_detection_config_file_extraction(
        files_path_all, files_infos_all, path_folder_sources
    )

    return files_path, files_infos


def read_config_file_files_infos_values(em: ExcelManager) -> TYPE_INFOS_VALUE:

    infos_all_details = _read_config_file_info_page(em)

    print([info.name for info in infos_all_details])

    # independent info
    independent_infos = {
        info.name: info.value
        for info in infos_all_details
        if info.value and not _is_info_list(info.name)
    }

    # list info

    list_infos: Dict[str, List[Dict[str, str]]] = {}

    list_name = None
    idx = None
    for info in infos_all_details:
        if not _is_info_list(info.name):
            list_name = None
            idx = None
            continue

        if _is_info_list(info.instruction):
            e1, e2 = info.instruction.split(":")
            list_name, idx = e1, int(e2) - 1

            if idx == 0:  # first element
                assert not list_name in list_infos.keys()
                list_infos[list_name] = [{}]
            else:
                assert (
                    list_name in list_infos.keys() and len(list_infos[list_name]) == idx
                )
                list_infos[list_name].append({})
        elif list_name is None or idx is None:
            raise RuntimeError("list_name and idx should not be None.")

        list_name_current, info_name = info.name.split(":")
        assert list_name_current == list_name

        list_infos[list_name][idx][info_name] = info.value

    print(
        {
            list_name: [
                {sub_name: info_value for sub_name, info_value in e.items()}
                for e in lst
            ]
            for list_name, lst in list_infos.items()
        }
    )

    # merge
    infos = dict(independent_infos)
    infos.update(list_infos)

    return infos


def fill_config_file(
    path_config_file: Path, infos: TYPE_INFOS_VALUE, path_output: Path
) -> None:

    # open
    em = ExcelManager(path_config_file)

    # get worksheet
    ws = em.get_worksheet("Infos à extraire")

    # write
    _write_independent_info(em, ws, infos)
    _write_list_info(em, ws, infos)

    # -- detect all the lists

    # save
    em.save(path_output)
    em.wb.close()


# ------------------- Private Method -------------------

# > Helper


def _is_info_list(name: str) -> bool:
    return name is not None and ":" in name


# > Write


def _write_independent_info(em: ExcelManager, ws: Worksheet, infos: TYPE_INFOS_VALUE):
    independant_infos = {
        name: value for name, value in infos.items() if isinstance(value, str)
    }

    for current_row in range(1, len(ws.row_dimensions)):
        # retrieve metadata and data of the info
        info = _read_line(em, ws, current_row)

        if info.name is None:
            continue

        # potential write value
        info_to_write = independant_infos.get(info.name)
        if info_to_write is not None:
            ws.cell(
                row=current_row,
                column=COLUMN_NAME_INFO + OFFSET_COLUMN_INFO_VALUE,
                value=info_to_write,
            )


def _write_list_info(em: ExcelManager, ws: Worksheet, infos: TYPE_INFOS_VALUE):

    # get the (start row, end row, list of the sub information, ) of each list
    lists: List[Tuple[str, int, int, List[InfoToExtractData]]] = []
    current_row = 1
    nb_rows = len(ws.row_dimensions)
    while current_row < nb_rows:
        info = _read_line(em, ws, current_row)

        if not _is_info_list(info.name):
            current_row += 1
            continue

        list_name, _ = info.name.split(":")
        if list_name in [name for name, _, _, _ in lists]:
            raise RuntimeError(
                f"List named '{list_name}' is at two different part of the config file."
            )

        start = current_row
        sub_infos = []
        while current_row < nb_rows:
            info = _read_line(em, ws, current_row)
            if not _is_info_list(info.name):
                break

            list_name_current, info_name = info.name.split(":")
            if list_name != list_name_current:
                break

            sub_info = InfoToExtractData(**info.__dict__)
            sub_info.name = info_name
            sub_infos.append(sub_info)
            current_row += 1

        end = current_row - 1

        lists.append((list_name, start, end, sub_infos))

    # filter if no informations has been found
    lists = [e for e in lists if e[0] in infos.keys()]

    print("inserted")
    # insert rows
    for idx in range(len(lists)):
        (name_list, _, end, sub_infos) = lists[idx]
        infos_extracted = infos.get(name_list)
        assert infos_extracted is not None and isinstance(infos_extracted, list)

        nb_to_add = len(sub_infos) * (len(infos_extracted) - 1)
        ws.insert_rows(end + 1, amount=nb_to_add)

        # update start and end
        for idx in range(idx + 1, len(lists)):
            name_list, start, end, sub_infos = lists[idx]
            lists[idx] = (name_list, start + nb_to_add, end + nb_to_add, sub_infos)

    # write on the rows
    for name_list, start, _, sub_infos in lists:

        for idx_ele_lst, info_extracted in enumerate(infos.get(name_list), start=0):

            row_first = start + idx_ele_lst * len(sub_infos)
            ws.cell(
                row_first, COLUMN_NAME_INFO - 1, value=f"{name_list}:{idx_ele_lst + 1}"
            )

            for idx_info, sub_info in enumerate(sub_infos):

                row = row_first + idx_info
                value = info_extracted.get(sub_info.name)

                texts = [
                    f"{name_list}:{sub_info.name}",
                    sub_info.desciption,
                    sub_info.label_source,
                    value if value is not None and value != "None" else "",
                ]
                for col, text in enumerate(texts):
                    ws.cell(row, COLUMN_NAME_INFO + col, value=text)


# > Read


def _read_config_file_info_page(em: ExcelManager) -> List[InfoToExtractData]:

    ws = em.get_worksheet("Infos à extraire")

    infos: List[InfoToExtractData] = []

    for current_row in range(3, ws.max_row + 1):
        # retrieve metadata and data of the info
        info = _read_line(em, ws, current_row)

        if info.name is None:
            continue

        # store infos
        infos.append(info)

    return infos


def _read_line(em: ExcelManager, ws: Worksheet, row: int) -> InfoToExtractData:
    return InfoToExtractData(
        instruction=em.get_text(ws, row, COLUMN_NAME_INFO - 1),
        name=em.get_text(ws, row, COLUMN_NAME_INFO),
        desciption=em.get_text(ws, row, COLUMN_NAME_INFO + 1),
        label_source=em.get_text(ws, row, COLUMN_NAME_INFO + 2),
        value=em.get_text(ws, row, COLUMN_NAME_INFO + OFFSET_COLUMN_INFO_VALUE),
        exact=em.get_text(ws, row, COLUMN_NAME_INFO + 4) == "X",
    )


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


def _read_config_file_info_page_and_preprocess(em: ExcelManager) -> TYPE_FILES_INFOS:

    infos = _read_config_file_info_page(em)

    # get the list who has already been extracted (fully or partially)
    list_name_done = list(
        set([info.instruction.split(":")[0] for info in infos if info.instruction])
    )

    # filter those list
    infos = [info for info in infos if info.name.split(":")[0] not in list_name_done]

    # filter those who has already a value
    infos = [info for info in infos if info.value is None]

    # group by label source
    files_infos = {}
    for info in infos:

        if not info.label_source in files_infos:
            files_infos[info.label_source] = []

        files_infos[info.label_source].append(info)

    return files_infos


# > Error detection


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
        elif not (path_folder_sources / path).resolve().exists():
            print(
                LogLevel.ERROR,
                f"Le fichier {path} n'existe pas dans l'arbre de fichier donné. ({path_folder_sources / path})",
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


# ------------------- Main -------------------

if __name__ == "__main__":
    from vars import PATH_CONFIG_FILE, PATH_TEST

    path = PATH_TEST / "list"
    if False:
        files_path, files_infos = read_config_file(
            path_config_file=path / "fichier_configuration.xlsx",
            path_folder_sources=path,
        )

        print(f"files_path : {files_path}")
        print(f"files_infos : {files_infos}")
    else:
        infos = {
            "demandeur": [
                {
                    "nom": "M. Claude MASSERE",
                    "avocat": "SCP MORIVAL AMISSE MABIRE",
                    "avocat_lieu": "Barreau de DIEPPE",
                },
                {
                    "nom": "Mme Françoise, Brigitte, Jeanne, Julia LAMAILLE épouse MASSERE",
                    "avocat": "SCP MORIVAL AMISSE MABIRE",
                    "avocat_lieu": "Barreau de DIEPPE",
                },
            ],
            "defendeur": [
                {
                    "nom": "La S.A.R.L. BRUGOT XAVIER",
                    "avocat": "SCP LENGLET, MALBESIN & Associés",
                    "avocat_lieu": "Barreau de ROUEN",
                },
                {
                    "nom": "La S.A. AXA France IARD",
                    "avocat": "SCP LENGLET, MALBESIN & Associés",
                    "avocat_lieu": "Barreau de ROUEN",
                },
                {
                    "nom": "M. Olivier BOUDET",
                    "avocat": "SELARL PATRICE LEMIEGRE PHILIPPE FOURDRIN SUNA GUNEY & Associés",
                    "avocat_lieu": "Barreau de ROUEN",
                },
                {
                    "nom": "La Société MUTUELLE DES ARCHITECTES FRANCAIS",
                    "avocat": "None",
                    "avocat_lieu": "None",
                },
            ],
        }

        fill_config_file(
            path_config_file=path / "fichier_configuration.xlsx",
            infos=infos,
            path_output=path / "fichier_configuration_rempli.xlsx",
        )
