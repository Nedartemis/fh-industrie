from collections import Counter
from typing import List

from backend.config_file.info_page.info_list_helper import is_info_ind
from backend.info_struct import ExtractionData
from logger import f, logger
from logs_label import InstructionIndMustBeEmpty, NameDuplicated


def checks_and_filter_info_ind(eds_ind: List[ExtractionData]):
    """
    Checks :
    - Duplicates
    - Instructions must be empty
    """

    assert all(is_info_ind(ed.name) for ed in eds_ind)

    # duplicates
    duplicates = [
        name
        for name, nb_occurences in Counter([ed.name for ed in eds_ind]).items()
        if nb_occurences > 1
    ]
    for name_duplicated in duplicates:
        rows = [ed.row for ed in eds_ind if ed.name == name_duplicated]
        logger.error(
            f"Name {name_duplicated} is duplicated : {f(rows=rows)}.\n"
            + "Not any of them will be used.",
            extra=NameDuplicated(name=name_duplicated, rows=rows),
        )
    eds_ind = [ed for ed in eds_ind if ed.name not in duplicates]

    # instructions must be empty
    not_empty_instructions = [ed for ed in eds_ind if ed.instruction is not None]
    if not_empty_instructions:
        names_and_rows = [(ed.name, ed.row) for ed in eds_ind]
        logger.error(
            "The instruction column for independant information must be empty.\n"
            + f"Here is the row and information name where it is not respected : {names_and_rows}",
            extra=InstructionIndMustBeEmpty(names_and_rows=names_and_rows),
        )
    eds_ind = [ed for ed in eds_ind if ed.instruction is None]

    return eds_ind
