import itertools
from dataclasses import dataclass
from typing import List, Tuple

from backend.generation.list.fill_list_helper import (
    BORDER_LEFT,
    BORDER_RIGHT,
    SPLITTER,
    ListInstruction,
    RowInstruction,
    build_fullname_info,
    error_generation_instruction_format,
    is_instruction,
    preprocess_instructions,
)
from backend.generation.replace_text import build_replace_text
from backend.info_struct import InfoValues
from backend.table.table_base import CELL_TYPE, TableBase
from logger import f, logger

# ------------------- Helper -------------------


def _get_column_instructions(
    table: TableBase[CELL_TYPE],
) -> List[RowInstruction[CELL_TYPE]]:

    assert is_the_table_a_table_list(table)

    return [
        RowInstruction(cell.str, tracability=cell)
        for row in range(1, table.get_row_dimension() + 1)
        if (cell := table.get_cell(row=row, col=1)) and cell.str
    ]


# ------------------- Public -------------------


def is_the_table_a_table_list(table: TableBase[CELL_TYPE]) -> bool:

    max_row, max_col = table.get_dimensions()
    if max_row < 1 or max_col < 1:
        return False

    text = table.get_cell(row=1, col=1).str
    if text is None:
        return False

    return f"{BORDER_LEFT}instruction{SPLITTER}colonne{BORDER_RIGHT}" in text


@dataclass
class ReplaceTableListRes[CELL_TYPE]:
    nb_changes: int
    all_has_been_filled: bool
    lists_instructions_filled: List[ListInstruction[CELL_TYPE]]


def replace_table_list(
    table: TableBase[CELL_TYPE], infos: InfoValues
) -> ReplaceTableListRes[CELL_TYPE]:

    logger.debug("replace_table_list")

    # read instructions
    column_row_instruction = _get_column_instructions(table)
    first_column = 2

    # checks
    wrongs = [
        row_instr
        for row_instr in column_row_instruction
        if not is_instruction(row_instr.text)
    ]
    if wrongs:
        error_generation_instruction_format(
            title_error="wrong format",
            tracabilities=[row_instr.tracability for row_instr in wrongs],
        )
    column_row_instruction = [
        cell for cell in column_row_instruction if cell not in wrongs
    ]

    # get name, start, end (do some checks)
    lists_instructions = preprocess_instructions(column_row_instruction)
    logger.debug(
        f"lists_rows : {[(lst.start.row, lst.end.row) for lst in lists_instructions]}"
    )

    # replace
    nb_changes = 0
    for instr in lists_instructions:

        list_info = infos.list_infos.get(instr.first_name)
        if list_info is None:
            logger.info(f"{instr.first_name} not in infos")
            continue

        logger.info(
            f(
                first_name=instr.first_name,
                nb_infos=len(list_info),
                nb_max_sub_names=max(len(d) for d in list_info),
            )
        )

        logger.debug(f"infos : {list_info}")

        # insert rows
        nb_rows_list = instr.end.row - instr.start.row + 1
        nb_to_add = nb_rows_list * (len(list_info) - 1)
        table.insert_rows(row=instr.end.row + 1, amount=nb_to_add)
        logger.debug(f"nb_to_add : {nb_to_add}")

        # copy content
        for idx in range(1, len(list_info)):

            table.copy_rectangle(
                from_row=instr.start.row,
                from_col=first_column,
                to_row=instr.start.row + nb_rows_list * idx,
                to_col=first_column,
                nb_row=nb_rows_list,
            )

        # update other start and end
        for instr_other in lists_instructions:
            if instr_other.start.row <= instr.start.row:
                continue

            instr_other.start.row += nb_to_add
            instr_other.end.row += nb_to_add

        # replace text
        for idx_element, infos_list_one_element in enumerate(list_info):

            infos_list_one_element = {
                build_fullname_info(instr.first_name, sub_name): value
                for sub_name, value in infos_list_one_element.items()
                if value is not None
            }
            logger.debug(f"infos_list_one_element : {infos_list_one_element}")

            func_replace_text = build_replace_text(pair_old_new=infos_list_one_element)

            offset = idx_element * nb_rows_list
            for row, col in itertools.product(
                range(instr.start.row + offset, instr.end.row + offset + 1),
                range(first_column, table.get_col_dimension() + 1),
            ):
                nb_changes += table.replace_text_in_cell(row, col, func_replace_text)

        logger.debug(
            f"Table list changes {f(first_name=instr.first_name)} : {nb_changes}"
        )

    logger.debug(f"Table list changes : {nb_changes}")

    res = ReplaceTableListRes(
        nb_changes=nb_changes,
        all_has_been_filled=all(
            instr.first_name in infos.list_infos for instr in lists_instructions
        ),
        lists_instructions_filled=[
            instr
            for instr in lists_instructions
            if instr.first_name in infos.list_infos
        ],
    )
    logger.debug(res)
    return res
