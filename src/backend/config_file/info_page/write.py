from typing import List, NamedTuple

from backend.config_file.info_page import Datas
from backend.config_file.info_page.info_list_helper import (
    combine,
    get_first_name,
    is_info_list,
    split_name,
)
from backend.config_file.info_page.read import InfoValues, read_line
from backend.config_file.info_page.utils import get_excel_sheet
from backend.excel.excel_book import ExcelBook
from backend.excel.excel_sheet import ExcelSheet
from backend.info_struct.extraction_data import ExtractionData
from backend.info_struct.info_values import InfoValues
from logger import logger

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

    row_info_type = NamedTuple(
        "row_info",
        [
            ("first_name", str),
            ("start_row", int),
            ("end_row", int),
            ("sub_infos", List[ExtractionData]),
        ],
    )

    lists: List[row_info_type] = []
    current_row = 1
    max_row = es.get_row_dimension() + 1
    while current_row < max_row:

        # find the beginning of a list info
        info = read_line(es, current_row)

        if not is_info_list(info.name):
            current_row += 1
            continue

        first_name = get_first_name(info.name)
        assert not first_name in [e.first_name for e in lists]

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
        lists.append(
            row_info_type(
                first_name=first_name, start_row=start, end_row=end, sub_infos=sub_infos
            )
        )

    # filter by keeping the lists that any of their information have been found
    lists = [e for e in lists if e.first_name in infos.list_infos.keys()]

    # insert rows
    for idx_row_info, row_info in enumerate(lists):

        infos_extracted = infos.list_infos.get(row_info.first_name)

        nb_to_add = len(row_info.sub_infos) * (len(infos_extracted) - 1)
        if nb_to_add == 0:
            continue

        # insert
        es.insert_rows(row=row_info.end_row + 1, amount=nb_to_add)

        # copy content
        for idx in range(len(infos_extracted) - 1):

            es.copy_rectangle(
                from_row=row_info.start_row,
                from_col=1,
                to_row=row_info.end_row + 1 + idx * len(row_info.sub_infos),
                to_col=1,
                nb_row=len(row_info.sub_infos),
            )

        # update start and end
        for idx in range(idx_row_info + 1, len(lists)):
            row_info_to_update = lists[idx]
            lists[idx] = row_info_type(
                first_name=row_info_to_update.first_name,
                start_row=row_info_to_update.start_row + nb_to_add,
                end_row=row_info_to_update.end_row + nb_to_add,
                sub_infos=row_info_to_update.sub_infos,
            )

    # write on the rows
    for row_info in lists:

        for idx_ele_lst, info_extracted in enumerate(
            infos.list_infos.get(row_info.first_name)
        ):

            # compute row
            row_first = row_info.start_row + idx_ele_lst * len(sub_infos)

            # write on instuction column
            es.ws.cell(
                row_first,
                Datas.INSTRUCTION.col,
                value=f"{row_info.first_name}:{idx_ele_lst + 1}",
            )

            # write sub information
            for idx_sub_info, sub_info in enumerate(row_info.sub_infos):

                row = row_first + idx_sub_info
                value = info_extracted.get(sub_info.name)

                if value:
                    es.ws.cell(row, Datas.VALUE.col, value)
