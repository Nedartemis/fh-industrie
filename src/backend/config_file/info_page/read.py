from typing import Dict, List

import backend.config_file.info_page.info_list_helper as info_list_helper
from backend.config_file.info_page import (
    FIRST_ROW_INFO,
    NAME_WORKSHEET,
    Datas,
    check_header,
    get_excel_sheet,
)
from backend.config_file.info_page.info_ind_helper import checks_and_filter_info_ind
from backend.config_file.info_page.info_list_helper import (
    checks_and_filter_info_list,
    get_first_name,
    get_first_names_of_info_list_extracted,
    is_info_ind,
    is_info_list,
    rearange_structure_info_list,
)
from backend.excel import ExcelBook, ExcelSheet
from backend.info_struct import ExtractionData, InfoExtractionDatas, InfoValues
from logger import f, logger
from logs_label import EmptyInfoExcel, NameDuplicated

# ------------------------- Utils -------------------------


def accepted_str_as_true_value(s: str) -> bool:
    return s is not None and s.lower() in ["true", "oui", "vrai", "x"]


PREPROCESS_INFO = {Datas.EXTRACT_EXACTLY_INFO: accepted_str_as_true_value}


def _preprocess_info(data: Datas, content: str):
    func = PREPROCESS_INFO.get(data, lambda x: x)
    return func(content)


def read_line(es: ExcelSheet, row: int) -> ExtractionData:
    d = {
        data.name.lower(): _preprocess_info(
            data=data, content=es.get_text_cell(row, data.col)
        )
        for data in Datas
    }
    return ExtractionData(row=row, **d)


# ------------------------- Main -------------------------


def read_info_page(eb: ExcelBook) -> List[ExtractionData]:

    es = get_excel_sheet(eb)

    # checks
    check_header(es)

    # rest cols
    cols_except_name = [(d.header_name, d.col) for d in Datas if d != Datas.NAME]
    mandatory_cols = [
        (d.header_name, d.col)
        for d in Datas
        if d in [Datas.NAME, Datas.LABEL_SOURCE_NAME]
    ]

    # read data
    infos: List[ExtractionData] = []

    for current_row in range(FIRST_ROW_INFO, es.get_row_dimension() + 1):
        # retrieve metadata and data of the info
        info = read_line(es, current_row)

        # checks
        if info.name is None:
            es.check_emptiness_row(
                page_name=NAME_WORKSHEET,
                row=current_row,
                header_name_cols=cols_except_name,
            )
            continue

        if es.check_fullness_row(
            page_name=NAME_WORKSHEET, row=current_row, header_name_cols=mandatory_cols
        ):
            continue

        # store infos
        infos.append(info)

    # checks and filter
    infos = checks_and_filter(infos, excel_name=eb.get_excel_name())

    return infos


def checks_and_filter(
    eds: List[ExtractionData], excel_name: str
) -> List[ExtractionData]:

    # separate for separetad checks
    eds_lst = [ed for ed in eds if is_info_list(ed.name)]
    eds_ind = [ed for ed in eds if is_info_ind(ed.name)]

    # inds
    eds_ind = checks_and_filter_info_ind(eds_ind)

    # checks on list
    eds_lst = checks_and_filter_info_list(eds_lst)

    # duplicate names between list and ind
    first_names_lst = {get_first_name(ed.name) for ed in eds_lst}
    names_ind = {ed.name for ed in eds_ind}
    duplicates = first_names_lst.intersection(names_ind)
    for name in duplicates:
        logger.error(
            f"The name '{name}' is both name of independant and list information.\n"
            + "Remove from both.",
            extra=NameDuplicated(name=name),
        )
    eds_ind = [ed for ed in eds_ind if ed.name not in duplicates]
    eds_lst = [ed for ed in eds_lst if get_first_name(ed.name) not in duplicates]

    # merge
    eds = eds_ind + eds_lst

    # empty infos
    if len(eds) == 0:
        ll = EmptyInfoExcel(excel_name=excel_name, page_name=NAME_WORKSHEET)
        logger.error(msg=ll.msg(), extra=ll)

    return eds


# def checks_and_filter_global(eds : List[ExtractionData]) -> ExtractionData:


def read_info_page_and_preprocess(em: ExcelBook) -> Dict[str, InfoExtractionDatas]:
    """
    Purposes :
    1. Read, from config file, the info page
    2. Separate list and independant infos
    3. List : Filter the infos already extracted
    4. Independant : Filter the infos already extracted
    5. Merge list and independant
    6. Group them by the label source
    7. Rearange structure
    """

    # 1.
    eds = read_info_page(em)

    # 2.
    eds_lst = [ed for ed in eds if is_info_list(ed.name)]
    eds_ind = [ed for ed in eds if is_info_ind(ed.name)]

    # 3.
    list_name_dones = get_first_names_of_info_list_extracted(eds_lst)
    logger.info(list_name_dones)

    # - filter those list
    eds_lst = [
        info
        for info in eds_lst
        if info_list_helper.get_first_name(info.name) not in list_name_dones
    ]

    # 4.
    eds_ind = [info for info in eds_ind if info.value is None]

    # 5.
    eds = eds_ind + eds_lst

    # 6.
    label_sources = list(set([ed.label_source_name for ed in eds]))
    info_per_sources = {label: [] for label in label_sources}

    for ed in eds:
        info_per_sources[ed.label_source_name].append(ed)

    # 7.
    return {
        label_source: InfoExtractionDatas(
            independant_infos=[ed for ed in eds if is_info_ind(ed.name)],
            list_infos=rearange_structure_info_list(eds),
        )
        for label_source, eds in info_per_sources.items()
    }


def read_info_values(em: ExcelBook) -> InfoValues:

    extraction_datas = read_info_page(em)

    logger.info([info.name for info in extraction_datas])

    # ind : filter those without values
    ind_infos = {
        info.name: info.value
        for info in extraction_datas
        if is_info_ind(info.name) and info.value
    }

    # list info
    list_infos = info_list_helper.get_info_list_values(extraction_datas)

    return InfoValues(indepedant_infos=ind_infos, list_infos=list_infos)


# ------------------------- Test -------------------------

if __name__ == "__main__":
    pass
