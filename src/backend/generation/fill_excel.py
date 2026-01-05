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
        nb_changes += replace_table_list(table=es, infos=infos)

        for row in range(1, es.get_row_dimension() + 1):
            es.erase_cell(row=row, col=1)

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


# ------------------- List infos -------------------


# def _replace_list_info(
#     es: ExcelSheet, infos: InfoValues, column_instruction: List[Cell], first_column: int
# ) -> int:

#     if not column_instruction:
#         return 0

#     # read instructions
#     # logger.info(column_instruction)

#     # - checks
#     wrongs = [cell for cell in column_instruction if not _is_instruction(cell)]
#     if wrongs:
#         _error_generation_instruction_format(
#             cells=wrongs, title_error="wrong format", obj=wrongs
#         )
#     column_instruction = [cell for cell in column_instruction if cell not in wrongs]

#     # - get name, begin, end (do some checks)
#     lists_instructions = _from_column_instructions_to_instructions(column_instruction)
#     logger.info(f"lists_rows : {lists_instructions}")

#     # - replace
#     nb_changes = 0
#     for instr in lists_instructions:

#         list_info = infos.list_infos.get(instr.first_name)
#         logger.info(
#             f(
#                 first_name=instr.first_name,
#                 nb_infos=len(list_info),
#                 nb_max_sub_names=max(len(d) for d in list_info),
#             )
#         )
#         logger.info(f"infos : {list_info}")
#         if list_info is None:
#             continue

#         # insert rows
#         nb_rows_list = instr.end_row - instr.start_row + 1
#         nb_to_add = nb_rows_list * (len(list_info) - 1)
#         es.insert_rows(row=instr.end_row + 1, amount=nb_to_add)
#         logger.info(f"nb_to_add : {nb_to_add}")

#         # copy content
#         for idx in range(1, len(list_info)):

#             es.copy_rectangle(
#                 from_row=instr.start_row,
#                 from_col=first_column,
#                 to_row=instr.start_row + nb_rows_list * idx,
#                 to_col=first_column,
#                 nb_row=nb_rows_list,
#             )

#         # update other start and end
#         for instr_other in lists_instructions:
#             if instr_other.start_row <= instr.start_row:
#                 continue

#             instr_other.start_row += nb_to_add
#             instr_other.end_row += nb_to_add

#         # replace text
#         for idx_element, infos_list_one_element in enumerate(list_info):

#             infos_list_one_element = {
#                 _build_fullname_info(instr.first_name, sub_name): value
#                 for sub_name, value in infos_list_one_element.items()
#                 if value is not None
#             }
#             logger.info(f"infos_list_one_element : {infos_list_one_element}")

#             func_replace_text = _build_replace_text(pair_old_new=infos_list_one_element)

#             offset = idx_element * nb_rows_list
#             for row, col in itertools.product(
#                 range(instr.start_row + offset, instr.end_row + offset + 1),
#                 range(first_column, es.get_col_dimension() + 1),
#             ):
#                 nb_changes += es.replace_text_in_cell(row, col, func_replace_text)

#         logger.info(
#             f"Excel changes list {f(first_name=instr.first_name)} : {nb_changes}"
#         )

#     logger.info(f"Excel changes list : {nb_changes}")

#     return nb_changes
