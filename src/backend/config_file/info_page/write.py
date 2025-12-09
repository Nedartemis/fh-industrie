from typing import Dict, List, Tuple

from backend.config_file.info_page import Datas, get_excel_sheet
from backend.config_file.info_page.info_list_helper import (
    combine,
    get_first_name,
    is_info_list,
    split_name,
)
from backend.config_file.info_page.read import InfoValues, read_line
from backend.excel.excel_book import ExcelBook
from backend.excel.excel_sheet import ExcelSheet
from backend.info_struct.extraction_data import ExtractionData
from backend.info_struct.info_values import InfoValues

# ------------------- Public Method -------------------


def write_values(eb: ExcelBook, infos: InfoValues) -> None:

    es = get_excel_sheet(eb)
    _write_values_independent_info(es, infos)
    _write_values_list_info(es, infos)


# ------------------- Private Method -------------------


def _write_values_independent_info(es: ExcelSheet, infos: InfoValues) -> None:

    for current_row in range(1, es.get_row_dimension() + 1):
        # retrieve metadata and data of the info
        info = read_line(es, current_row)

        if info.name is None:
            continue

        # potential write value
        info_to_write = infos.independant_infos.get(info.name)
        if info_to_write is not None:
            es.ws.cell(
                row=current_row,
                column=Datas.VALUE.col,
                value=info_to_write,
            )


def _write_values_list_info(es: ExcelSheet, infos: InfoValues):

    # get the (first_name, start row, end row, list of the sub information) of each list
    lists: List[Tuple[str, int, int, List[ExtractionData]]] = []
    current_row = 1
    max_row = es.get_row_dimension() + 1
    while current_row < max_row:

        # find the beginning of a list info
        info = read_line(es, current_row)

        if not is_info_list(info.name):
            current_row += 1
            continue

        fist_name = get_first_name(info.name)
        if fist_name in [name for name, _, _, _ in lists]:
            raise RuntimeError(
                f"List named '{first_name}' is at two different part of the config file."
            )

        start = current_row

        # search the end of this list
        sub_infos = []
        while current_row < max_row:
            info = read_line(es, current_row)
            if not is_info_list(info.name):
                break

            first_name_current, info_name = split_name(info.name)
            if first_name != first_name_current:
                break

            sub_info = ExtractionData(**info.__dict__)
            sub_info.name = info_name

            sub_infos.append(sub_info)
            current_row += 1

        # store
        end = current_row - 1
        lists.append((first_name, start, end, sub_infos))

    # filter the list that any of their information have been found
    lists = [e for e in lists if e[0] in infos.list_infos.keys()]

    # insert rows
    for idx, (first_name, _, end, sub_infos) in enumerate(lists):

        infos_extracted = infos.list_infos.get(first_name)

        nb_to_add = len(sub_infos) * (len(infos_extracted) - 1)
        es.ws.insert_rows(end + 1, amount=nb_to_add)

        # update start and end
        for idx in range(idx + 1, len(lists)):
            first_name, start, end, sub_infos = lists[idx]
            lists[idx] = (first_name, start + nb_to_add, end + nb_to_add, sub_infos)

    # write on the rows
    for first_name, start, _, sub_infos in lists:

        for idx_ele_lst, info_extracted in enumerate(infos.list_infos.get(first_name)):

            # compute row
            row_first = start + idx_ele_lst * len(sub_infos)

            # write on instuction column
            es.ws.cell(
                row_first,
                Datas.INSTRUCTION.col,
                value=f"{first_name}:{idx_ele_lst + 1}",
            )

            # write sub information
            for idx_sub_info, sub_info in enumerate(sub_infos):

                row = row_first + idx_sub_info
                value = info_extracted.get(sub_info.name)

                es.ws.cell(row, Datas.NAME.col, combine(first_name, sub_info.name))
                es.ws.cell(row, Datas.DESCRIPTION.col, sub_info.desciption)
                es.ws.cell(row, Datas.LABEL_SOURCE_NAME.col, sub_info.label_source_name)
                if value:
                    es.ws.cell(row, Datas.VALUE.col, value)
