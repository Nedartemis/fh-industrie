import itertools
from pathlib import Path
from typing import Dict, Tuple

from backend.excel.excel_book import ExcelBook
from backend.excel.excel_sheet import ExcelSheet
from backend.generation.list.fill_table_list import (
    is_the_table_a_table_list,
    replace_table_list,
)
from backend.generation.replace_text import replace_text
from backend.info_struct import InfoValues
from logger import logger

# ------------------- Public Method -------------------


def fill_template_excel(path_excel: Path, infos: InfoValues, path_output: Path) -> int:

    eb = ExcelBook(path_excel=path_excel)
    nb_changes = _fill_excel(eb, infos)
    eb.save(path_output)

    return nb_changes


# ------------------- Private Method -------------------


def _fill_excel(eb: ExcelBook, infos: InfoValues) -> None:

    nb_changes = 0

    for es in eb:
        nb_changes += _fill_worksheet(es, infos)

    return nb_changes


def _fill_worksheet(es: ExcelSheet, infos: InfoValues) -> int:

    nb_changes = 0

    # instruction column
    has_column_instruction = is_the_table_a_table_list(es)

    # ind info
    nb_changes += _replace_ind_info(
        es, infos, first_column=2 if has_column_instruction else 1
    )

    # list info
    if has_column_instruction:
        # fill
        res = replace_table_list(table=es, infos=infos)
        nb_changes += res.nb_changes

        # erase instruction column
        if res.all_has_been_filled:
            es.erase_cell(row=1, col=1)

        # erase those filled
        for instr in res.lists_instructions_filled:
            es.erase_cell(row=instr.start.row, col=1)
            es.erase_cell(row=instr.end.row, col=1)

    return nb_changes


def _build_replace_text(pair_old_new: Dict[str, str]):

    def replace_text_custom(s: str) -> Tuple[str, int]:
        res = replace_text(s, pair_old_new=pair_old_new)
        return res.changed_text, res.nb_changes

    return replace_text_custom


# ------------------- Independant infos -------------------


def _replace_ind_info(es: ExcelSheet, infos: InfoValues, first_column: int) -> int:

    # build replace text
    pair_old_new = {
        name: value
        for name, value in infos.independant_infos.items()
        if value is not None
    }
    replace_text = _build_replace_text(pair_old_new=pair_old_new)
    # logger.info(pair_old_new)

    # replace
    nb_changes = 0
    max_row, max_col = es.get_dimensions()
    for row, col in itertools.product(
        range(1, max_row + 1), range(first_column, max_col + 1)
    ):
        nb_changes += es.replace_text_in_cell(
            row=row, col=col, replace_text=replace_text
        )

    logger.info(f"Excel changes indenpendent : {nb_changes}")

    return nb_changes
