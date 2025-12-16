from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from backend.info_struct import ExtractionData, InfoExtractionDatas, InfoValues
from logger import WARNING, logger
from utils.collection_ope import list_to_dict_occurences

# ------------------- TYPE -------------------


TYPE_RUNNABLE = Callable[[], None]
TYPE_EXPECTED_LOG_LABEL_CLASS = Union[Any, List]

# ------------------- Wrapper -------------------


def wrapper_test_good(runnable: TYPE_RUNNABLE, level_log_to_keep=WARNING) -> None:
    logger.reset_logs()
    runnable()
    assert len(logger.get_logs_label()) == 0
    assert len(logger.get_logs(level_to_keep=level_log_to_keep)) == 0


def wrapper_test_logs(
    runnable: TYPE_RUNNABLE,
    expected_log_label_class: TYPE_EXPECTED_LOG_LABEL_CLASS,
) -> None:

    logger.reset_logs()
    runnable()
    logs_label = logger.get_logs_label()

    if not isinstance(expected_log_label_class, list):
        expected_log_label_class = [expected_log_label_class]

    assert len(logs_label) == len(expected_log_label_class)

    occs_actual = list_to_dict_occurences([ll.__class__ for ll in logs_label])
    occs_expected = list_to_dict_occurences(expected_log_label_class)
    assert occs_actual == occs_expected


def wrapper_try(runnable: TYPE_RUNNABLE, expected_log_label_class) -> None:

    try:
        runnable()
        assert False, f"Should have raised : {expected_log_label_class}"
    except expected_log_label_class:
        assert True


# ------------------- Builder -------------------


def bed(name: str, description: Optional[str] = None, exact: bool = False):
    return ExtractionData(
        name=name, description=description, extract_exactly_info=exact, row=3
    )


def bied(
    inds: Union[List[ExtractionData], ExtractionData] = [],
    lists: Dict[str, List[ExtractionData]] = {},
) -> InfoExtractionDatas:
    if not isinstance(inds, list):
        inds = [inds]
    return InfoExtractionDatas(independant_infos=inds, list_infos=lists)


def biv(
    inds: Dict[str, str] = {},
    lists: Dict[str, List[Dict[str, str]]] = {},
) -> InfoValues:
    return InfoValues(independant_infos=inds, list_infos=lists)
