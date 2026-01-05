import itertools
import re
from dataclasses import dataclass
from typing import Any, Generic, List, Optional, TypeVar, Union

from backend.generation.replace_text import build_replace_text
from backend.info_struct import InfoValues
from backend.table.table_base import CellBase, TableBase
from logger import f, logger
from logs_label import GenerationWrongInstructionFormat

# ------------------- Constant -------------------

SPLITTER = ":"
BORDER_LEFT = "{"
BORDER_RIGHT = "}"


# ------------------- Structs -------------------


@dataclass
class RowInstruction[T]:
    text: str
    tracability: T


@dataclass
class Instruction[T]:
    words: List[str]
    tracability: T


@dataclass
class ListInstruction[T]:
    first_name: str
    start: T
    end: T


# ------------------- Helper -------------------

T = TypeVar("T")


def _get_instructions(
    text: Optional[str], tracability: Optional[T] = None
) -> Optional[List[Instruction[T]]]:
    if text is None:
        return None

    res = re.findall(
        pattern=f"{BORDER_LEFT}instruction" + SPLITTER + r"([^}]+)" + BORDER_RIGHT,
        string=text,
    )
    if not res:
        return None

    return [
        Instruction(words=match.split(SPLITTER), tracability=tracability)
        for match in res
    ]


def is_instruction(text: Optional[str]) -> bool:
    return _get_instructions(text) is not None


def _is_instruction_start_list(instruction: Instruction) -> bool:
    return instruction.words[0] == "debut_liste"


def _is_instruction_end_list(instruction: Instruction) -> bool:
    return instruction.words[0] == "fin_liste"


def _check_number_words(
    instruction: Instruction, nb_words_expected: int, title_error: str
) -> bool:
    if len(instruction.words) != nb_words_expected:
        error_generation_instruction_format(
            title_error=f"{title_error} wrong format number words",
            tracabilities=instruction.tracability,
        )
        return True

    return False


# ------------------- Column instructions -------------------


def build_fullname_info(first_name: str, sub_name: str) -> str:
    return f"{first_name}{SPLITTER}{sub_name}"


def error_generation_instruction_format(
    title_error: str,
    tracabilities: Union[Any, List[Any]],
):

    logger.error(
        f"Generation instruction {title_error} : {tracabilities}",
        extra=GenerationWrongInstructionFormat(
            tracabilities=(
                tracabilities if isinstance(tracabilities, list) else [tracabilities]
            )
        ),
    )


def preprocess_instructions(
    row_instructions: List[RowInstruction[T]],
) -> List[ListInstruction[T]]:

    lists_instructions: List[ListInstruction[T]] = []
    name_list = None
    for row_instr in row_instructions:

        for instruction in _get_instructions(row_instr.text):

            # logger.info(instruction)

            if _is_instruction_start_list(instruction):
                # start
                if _check_number_words(
                    instruction, nb_words_expected=2, title_error="start list"
                ):
                    continue

                if name_list is not None:
                    error_generation_instruction_format(
                        title_error="2 lists starts following",
                        tracabilities=row_instr.tracability,
                    )

                name_list = instruction.words[1]
                e = ListInstruction(
                    first_name=name_list, start=row_instr.tracability, end=None
                )
                lists_instructions.append(e)

            elif _is_instruction_end_list(instruction):
                # end
                if _check_number_words(
                    instruction, nb_words_expected=2, title_error="end list"
                ):
                    continue

                old_name_list = name_list
                name_list = None

                name_list_end = instruction.words[1]
                if old_name_list != name_list_end:
                    error_generation_instruction_format(
                        title_error="end without its start",
                        tracabilities=row_instr.tracability,
                    )
                    continue

                lists_instructions[-1].end = row_instr.tracability

    # start without end
    for instr in lists_instructions:
        if instr.end is None:
            error_generation_instruction_format(
                title_error="end without its start",
                tracabilities=row_instr.tracability,
            )
    lists_instructions = [
        instr for instr in lists_instructions if instr.end is not None
    ]

    return lists_instructions
