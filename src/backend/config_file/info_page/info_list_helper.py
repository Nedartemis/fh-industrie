import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from backend.info_struct.extraction_data import ExtractionData
from logger import f, logger
from logs_label import (
    ListCantBeExact,
    ListCantBeSepareted,
    ListCantHaveDifferentSources,
    ListEclatedNotConsistent,
    ListNotEclatedEmptyValues,
    ListTooMuchSplitter,
    NameListDuplicated,
)
from utils.collection_ope import find_duplicates

SPLITTER = ":"

# ------------------------- Split -------------------------


def valid_list_instruction(instruction: Optional[str]) -> bool:
    if instruction is None:
        return False

    return (
        re.match(pattern=f"[^{SPLITTER}]*{SPLITTER}[0-9]+", string=instruction)
        is not None
    )


def split_instruction(instruction: str) -> Tuple[str, int]:
    first_name, nb_list_element = split_name(instruction)
    return first_name, int(nb_list_element) - 1


def split_name(s: str) -> Tuple[str, str]:
    return tuple(s.split(SPLITTER))


def get_first_name(s: str) -> str:
    return split_name(s)[0]


def get_sub_name(name: str) -> str:
    return split_name(name)[1]


def is_invalid_name(name: str) -> bool:
    return name.count(SPLITTER) > 1


# ------------------------- Combine -------------------------


def combine(first_name: str, sub_name: str) -> str:
    return f"{first_name}{SPLITTER}{sub_name}"


# ------------------------- Predicate -------------------------


def is_info_list(name: Optional[str]) -> bool:
    return name is not None and SPLITTER in name


def is_info_ind(name: Optional[str]) -> bool:
    return not is_info_list(name)


# ------------------------- Conversion -------------------------


def get_info_list_values(eds: List[ExtractionData]) -> Dict[str, List[dict]]:

    assert all(is_info_list(ed.name) for ed in eds)

    # we suppose the list completly valid because checks have been made earlier

    grouped_by_first_name: Dict[str, List[ExtractionData]] = {
        get_first_name(ed.name): [] for ed in eds
    }

    for ed in eds:
        grouped_by_first_name[get_first_name(ed.name)].append(ed)

    # filter those not eclated
    grouped_by_first_name = {
        first_name: eds
        for first_name, eds in grouped_by_first_name.items()
        if any(valid_list_instruction(ed.instruction) for ed in eds)
    }

    # filter those without values (by taking all the list)
    grouped_by_first_name = {
        first_name: eds
        for first_name, eds in grouped_by_first_name.items()
        if not all(ed.value is None for ed in eds)
    }

    # rearange

    list_infos: Dict[List[dict]] = {}

    for first_name, eds in grouped_by_first_name.items():

        list_infos[first_name] = []

        for ed in eds:
            if is_info_list(ed.instruction):
                # new element of the list
                first_name, idx = split_instruction(ed.instruction)
                assert len(list_infos[first_name]) == idx
                list_infos[first_name].append({})
            else:
                # same element of the list
                pass

            # get sub name
            first_name_check, info_sub_name = split_name(ed.name)
            assert first_name_check == first_name

            # store the value
            list_infos[first_name][-1][info_sub_name] = ed.value

    return list_infos


def rearange_structure_info_list(
    eds: List[ExtractionData],
) -> Dict[str, List[ExtractionData]]:

    # filter not list info
    eds = [ed for ed in eds if is_info_list(ed.name)]

    # rearange the structure and split the name in two
    list_infos: Dict[str, List[ExtractionData]] = {}
    for ed in eds:

        first_name, sub_name = split_name(ed.name)
        if not first_name in list_infos:
            list_infos[first_name] = []

        new_info = ExtractionData(**ed.__dict__)
        new_info.name = sub_name
        list_infos[first_name].append(new_info)

    return list_infos


# ------------------------- Other -------------------------


def get_first_names_of_info_list_extracted(
    extraction_datas: List[ExtractionData],
) -> List[str]:
    """
    If in the instructions there is the sign that a vlist has been extracted,
    we consider that all the info of the vlist do not have to be extracted anymore
    even if some sub variables were not extracted.
    """

    list_name_done = [
        get_first_name(ed.name) for ed in extraction_datas if ed.instruction is not None
    ]
    # unify
    return list(set(list_name_done))


def checks_and_filter_info_list(eds_list: List[ExtractionData]) -> List[ExtractionData]:
    """
    Checks :
    - List cant be exact
    - Name validity (not too much splitter)
    - Should not be separated
    - List cant have different sources
    - Check each element of the list
    > if no instructions :
    --> no duplicates
    --> all value must be empty
    > if instructions (ecclated list) :
    --> Check existence instruction
    --> Check instruction format
    --> Check instruction name
    --> Check idx element
    --> Check no duplicates in an element of the list
    """

    assert all(is_info_list(ed.name) for ed in eds_list)

    # List cant be exact
    exacts = [ed.name for ed in eds_list if ed.extract_exactly_info]
    if exacts:
        logger.warning(
            f"Some list info needs to be extracted exactly but this feature does not work on list info.\n"
            + f"List of these variables : {exacts}",
            extra=ListCantBeExact(exacts),
        )

    # Name validity (not too much splitter)
    invalid_names = [ed.name for ed in eds_list if is_invalid_name(ed.name)]
    if invalid_names:
        logger.error(
            f"Config file : Information name with more than one '{SPLITTER}' are not handled : {[invalid_names]}",
            extra=ListTooMuchSplitter(invalid_names),
        )
        eds_list = [ed for ed in eds_list if not is_invalid_name(ed.name)]

    # Should not be separated

    grouped_by_first_name: Dict[str, List[ExtractionData]] = {
        get_first_name(ed.name): [] for ed in eds_list
    }

    for ed in eds_list:
        grouped_by_first_name[get_first_name(ed.name)].append(ed)

    separated_list = [
        first_name
        for first_name, eds in grouped_by_first_name.items()
        if (rows := [ed.row for ed in eds])
        if rows != list(range(min(rows), max(rows) + 1))
    ]
    if separated_list:
        logger.error(
            msg=f"Those list {separated_list} are separeted by other information name.\n"
            + "They are not going to be treated.",
            extra=ListCantBeSepareted(names=separated_list),
        )

    eds_list = [ed for ed in eds_list if get_first_name(ed.name) not in separated_list]

    # List cant have different sources except one have a none source
    sources_per_first_names = {
        get_first_name(ed.name): ed.label_source_name for ed in eds_list
    }
    different_first_name = [
        get_first_name(ed.name)
        for ed in eds_list
        if (label_expected := sources_per_first_names[get_first_name(ed.name)])
        and ed.label_source_name
        and label_expected != ed.label_source_name
    ]
    if different_first_name:
        logger.error(
            f"Some list info does not have their source from the same file, it is not allowed.\n"
            + f"Therefore these information {different_first_name} won't be extracted.",
            extra=ListCantHaveDifferentSources(different_first_name),
        )

        eds_list = [
            ed for ed in eds_list if get_first_name(ed.name) not in different_first_name
        ]

    # Check each element of the list

    first_names_to_filter: List[str] = []
    for first_name, eds in grouped_by_first_name.items():

        if any(ed.instruction for ed in eds):
            # with instruction --> eclated list
            consistent = _check_eclated_list(first_name=first_name, eds=eds)
            if not consistent:
                logger.error(
                    msg=f"The list '{first_name}' is eclated but is not consistent.",
                    extra=ListEclatedNotConsistent(first_name=first_name),
                )
                first_names_to_filter.append(first_name)
        else:
            # without instructions

            # check no duplicates
            duplicates = find_duplicates([ed.name for ed in eds])
            if duplicates:
                logger.error(
                    "If there is no instruction, there must not be any duplicates name in the list.\n"
                    + f(first_name=first_name, duplicates=duplicates),
                    extra=NameListDuplicated(
                        first_name=first_name, duplicate_names=duplicates
                    ),
                )
                first_names_to_filter.append(first_name)

            # all values must be empty
            not_empty_values = [ed.name for ed in eds if ed.value is not None]
            if not_empty_values:
                logger.error(
                    "Values of not eclated list must all be none.\n"
                    + f"Not empty values for names : {not_empty_values}",
                    extra=ListNotEclatedEmptyValues(first_name=first_name),
                )
                first_names_to_filter.append(first_name)

    eds_list = [
        ed for ed in eds_list if get_first_name(ed.name) not in first_names_to_filter
    ]

    return eds_list


def _check_eclated_list(first_name: str, eds: List[ExtractionData]) -> bool:

    log_title = f"List eclated '{first_name}'"

    idx_element_expected = 0
    idx = 0
    while idx < len(eds):
        ed = eds[idx]

        # check existence instruction
        if ed.instruction is None:
            logger.info(f"{log_title} : No instruction when needed")
            return False

        # check instruction format
        if not valid_list_instruction(ed.instruction):
            logger.info(
                f"{log_title} : instruction '{ed.instruction}' not good format."
            )
            return False

        first_name_instr, idx_element = split_instruction(ed.instruction)

        # check instruction name
        if first_name != first_name_instr:
            logger.info(f"{log_title} : Mismatch instruction name and first name list")
            return False

        # check idx element
        if idx_element != idx_element_expected:
            logger.info(
                f"{log_title}: Invalid element number {f(expected=idx_element_expected+1, actual=idx_element+1)}"
            )
            return False

        # go through an element of the list (sequence of subnames)
        sub_names: List[str] = [eds[idx].name]
        idx += 1
        while idx < len(eds) and eds[idx].instruction is None:
            sub_names.append(eds[idx].name)
            idx += 1

        # check no duplicates
        duplicates = find_duplicates(sub_names)
        if duplicates:
            logger.info(
                f"{log_title} : Some duplicates in the element {idx_element} : {duplicates}"
            )
            return False

        idx_element_expected += 1

    return True
