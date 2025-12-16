import os
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pytest
from helper_testsuite import (
    TYPE_EXPECTED_LOG_LABEL_CLASS,
    bied,
    biv,
    wrapper_test_good,
    wrapper_test_logs,
    wrapper_try,
)

from backend.config_file.config_file import fill_config_file, read_config_file
from backend.config_file.info_page.read import (
    read_info_page,
    read_info_page_and_preprocess,
    read_info_values,
)
from backend.config_file.source_page import TYPE_SOURCES, read_source_page
from backend.excel import ExcelBook
from backend.info_struct import ExtractionData, InfoExtractionDatas, InfoValues
from logger import ERROR, logger
from logs_label import (
    EmptyInfoExcel,
    EmptynessExcelCell,
    ExactnessExcelCell,
    ExcelNotExisting,
    ExtensionFileNotSupported,
    FullnessExcelCell,
    InstructionIndMustBeEmpty,
    ListCantBeExact,
    ListCantBeSepareted,
    ListCantHaveDifferentSources,
    ListEclatedNotConsistent,
    ListNotEclatedEmptyValues,
    ListTooMuchSplitter,
    NameDuplicated,
    NameListDuplicated,
    NoRightWorksheet,
    OneNameWithMultiplePaths,
    OnePathWithMultipleNames,
    PathNotExisting,
    SourceNotGiven,
    SourceNotUseful,
)
from vars import PATH_TEST_DOCS_TESTSUITE

# ------------------- Utils -------------------


def _from_folder_name_and_filename(folder_name: str, filename: str) -> Tuple[str, str]:
    path_folder = PATH_TEST_DOCS_TESTSUITE / folder_name
    path_config_file = path_folder / f"{filename}.xlsx"
    return path_folder, path_config_file


SUB_FOLDER_INFO_PAGE = "read_config_file/info_page"


# ------------------- Read sources -------------------


def _read_sources(filename: str) -> TYPE_SOURCES:
    _, path_config_file = _from_folder_name_and_filename("sources", filename)
    return read_source_page(ExcelBook(path_config_file))


# def from_folder_name(folder_name: str) -> Tuple[Path, Path]:
#     return from_folder_name_and_filename(
#         folder_name=folder_name, filename="fichier_configuration"
#     )


@pytest.mark.parametrize(
    ["filename", "expected_sources"],
    [
        ("one", {"ordonnance1": "1.txt"}),
        (
            "many",
            {"o1": "1.txt", "o2": "2.txt", "o3": "3.txt", "o4": "4.txt", "o5": "5.txt"},
        ),
        ("last_row", {"o1": "1.txt"}),
        ("gap", {"o1": "1.txt"}),
    ],
)
def test_read_source_page_good(filename: str, expected_sources: dict):
    def f():
        sources = _read_sources(filename)
        assert sources == expected_sources

    wrapper_test_good(f)


@pytest.mark.parametrize(
    ["filename", "expected_log_label_class"],
    [
        # header name
        ("bad_header_name_source", ExactnessExcelCell),
        ("bad_header_name_path", ExactnessExcelCell),
        # non optional fields lacking
        ("name_full_path_empty_one", EmptynessExcelCell),
        ("name_full_path_empty_two_among_many", [EmptynessExcelCell] * 2),
        ("name_empty_path_full_one", FullnessExcelCell),
        ("name_empty_path_full_two_among_many", [FullnessExcelCell] * 2),
        # empty info
        ("empty_info", EmptyInfoExcel),
        ("empty_info_because_one_row_path_empty", [EmptyInfoExcel, EmptynessExcelCell]),
        # inconsistency data
        ("one_name_with_differnt_paths", OneNameWithMultiplePaths),
        ("one_path_with_different_names", OnePathWithMultipleNames),
        # duplicated names
    ],
)
def test_read_source_page_wrong(
    filename: str,
    expected_log_label_class: TYPE_EXPECTED_LOG_LABEL_CLASS,
):
    wrapper_test_logs(
        runnable=lambda: _read_sources(filename),
        expected_log_label_class=expected_log_label_class,
    )


@pytest.mark.parametrize(
    ["filename", "expected_log_label_class"],
    [
        ("wrong_name_worksheet", NoRightWorksheet),
        ("no_worksheet", NoRightWorksheet),
    ],
)
def test_read_source_page_raise(
    filename: str,
    expected_log_label_class,
):
    wrapper_try(lambda: _read_sources(filename), expected_log_label_class)


# ------------------- Read info page -------------------


def _read_infos(filename: str, folder: str) -> List[ExtractionData]:
    _, path_config_file = _from_folder_name_and_filename(
        f"read_config_file/info_page/{folder}", filename
    )
    return read_info_page(ExcelBook(path_config_file))


@pytest.mark.parametrize(
    ["filename", "expected_infos"],
    [
        (
            "one_just_name_and_source",
            [ExtractionData(name="n1", label_source_name="o1", row=3)],
        ),
        (
            "many_just_name_and_source",
            [
                ExtractionData(name="n1", label_source_name="o1", row=3),
                ExtractionData(name="n2", label_source_name="o2", row=4),
                ExtractionData(name="n3", label_source_name="o3", row=5),
                ExtractionData(name="n4", label_source_name="o4", row=6),
                ExtractionData(name="n5", label_source_name="o5", row=7),
            ],
        ),
        (
            "description",
            [
                ExtractionData(
                    name="n1", label_source_name="o1", description="d1", row=3
                )
            ],
        ),
        (
            "instruction",
            [
                ExtractionData(
                    name="n1:s1", label_source_name="o1", instruction="n1:1", row=3
                )
            ],
        ),
        (
            "text_exact",
            [
                ExtractionData(
                    name="n1", label_source_name="o1", extract_exactly_info=True, row=3
                )
            ],
        ),
        (
            "value",
            [ExtractionData(name="n1", label_source_name="o1", value="v1", row=3)],
        ),
        (
            "text_exact_alternatives",
            [
                ExtractionData(
                    name="n1", label_source_name="o1", row=3, extract_exactly_info=True
                ),
                ExtractionData(
                    name="n2", label_source_name="o2", row=4, extract_exactly_info=True
                ),
                ExtractionData(
                    name="n3", label_source_name="o3", row=5, extract_exactly_info=True
                ),
                ExtractionData(
                    name="n4", label_source_name="o4", row=6, extract_exactly_info=True
                ),
                ExtractionData(
                    name="n5", label_source_name="o5", row=7, extract_exactly_info=True
                ),
                ExtractionData(
                    name="n6", label_source_name="o6", row=8, extract_exactly_info=False
                ),
            ],
        ),
        ("last_row", [ExtractionData(name="n1", label_source_name="o1", row=3)]),
        ("gap", [ExtractionData(name="n1", label_source_name="o1", row=5)]),
        # list
        (
            "list_valid_one",
            [ExtractionData(name="n1:s1", label_source_name="o1", row=3)],
        ),
        (
            "list_different_sources",
            [
                ExtractionData(name="n1:s1", label_source_name="o1", row=3),
                ExtractionData(name="n2:s1", label_source_name="o2", row=4),
            ],
        ),
        (
            "list_valid_many",
            [
                ExtractionData(name="n1:s1", label_source_name="o1", row=3),
                ExtractionData(name="n2:s1", label_source_name="o2", row=4),
                ExtractionData(name="n3:s1", label_source_name="o1", row=5),
                ExtractionData(name="n3:s2", label_source_name="o1", row=6),
                ExtractionData(name="n3:s3", label_source_name="o1", row=7),
            ],
        ),
        (
            "list_valid_gap",
            [
                ExtractionData(name="n3", label_source_name="o3", row=6),
                ExtractionData(name="n1:s1", label_source_name="o1", row=3),
                ExtractionData(name="n2:s1", label_source_name="o2", row=5),
                ExtractionData(name="n4:s1", label_source_name="o4", row=7),
            ],
        ),
        # eclated list
        (
            "list_eclated_one_element",
            [
                ExtractionData(
                    name="n1:s1", label_source_name="o1", row=3, instruction="n1:1"
                ),
                ExtractionData(name="n1:s2", label_source_name="o1", row=4),
            ],
        ),
        (
            "list_eclated_two_element",
            [
                ExtractionData(
                    name="n1:s1", label_source_name="o1", row=3, instruction="n1:1"
                ),
                ExtractionData(name="n1:s2", label_source_name="o1", row=4),
                ExtractionData(
                    name="n1:s1", label_source_name="o1", row=5, instruction="n1:2"
                ),
                ExtractionData(name="n1:s2", label_source_name="o1", row=6),
            ],
        ),
        (
            "list_eclated_two_list",
            [
                ExtractionData(
                    name="n1:s1", label_source_name="o1", row=3, instruction="n1:1"
                ),
                ExtractionData(name="n1:s2", label_source_name="o1", row=4),
                ExtractionData(
                    name="n2:s1", label_source_name="o2", row=5, instruction="n2:1"
                ),
                ExtractionData(name="n2:s2", label_source_name="o2", row=6),
            ],
        ),
        (
            "list_eclated_not_same_sub_names_each_element_of_list",
            [
                ExtractionData(
                    name="n1:s1", label_source_name="o1", row=3, instruction="n1:1"
                ),
                ExtractionData(name="n1:s2", label_source_name="o1", row=4),
                ExtractionData(name="n1:s3", label_source_name="o1", row=5),
                ExtractionData(
                    name="n1:s1", label_source_name="o1", row=6, instruction="n1:2"
                ),
                ExtractionData(
                    name="n1:s1", label_source_name="o1", row=7, instruction="n1:3"
                ),
                ExtractionData(name="n1:s3", label_source_name="o1", row=8),
            ],
        ),
    ],
)
def test_read_info_page_good(filename: str, expected_infos: List[ExtractionData]):
    def f():
        sources = _read_infos(filename, "good")
        assert sources == expected_infos

    wrapper_test_good(f)


@pytest.mark.parametrize(
    ["filename", "expected_infos"],
    [
        (
            "names_duplicated_ind",
            [
                ExtractionData(name="n2", label_source_name="o3", row=5),
            ],
        ),
        (
            "list_one_source_is_none",
            [
                ExtractionData(
                    name="n1:s1",
                    label_source_name="o1",
                    row=3,
                    value="t1",
                    instruction="n1:1",
                ),
                ExtractionData(name="n1:s2", label_source_name=None, row=4, value="t2"),
            ],
        ),
    ],
)
def test_read_info_page_partial_good(
    filename: str, expected_infos: List[ExtractionData]
):
    sources = _read_infos(filename, "wrong")
    assert sources == expected_infos


@pytest.mark.parametrize(
    ["filename", "expected_log_label_class", "nb_expected_info"],
    [
        # no optional fields lacking
        ("no_name", FullnessExcelCell, 1),
        ("only_description", FullnessExcelCell, 1),
        ("no_source", EmptynessExcelCell, 1),
        ("source_is_str_none", EmptynessExcelCell, 1),
        # wrong header
        ("wrong_header_instruction", ExactnessExcelCell, 1),
        ("wrong_header_name", ExactnessExcelCell, 1),
        ("wrong_header_description", ExactnessExcelCell, 1),
        ("wrong_header_source", ExactnessExcelCell, 1),
        ("wrong_header_value", ExactnessExcelCell, 1),
        ("wrong_header_exact", ExactnessExcelCell, 1),
        # empty info
        ("no_info", EmptyInfoExcel, 0),
        # list
        ("list_cant_be_exact", ListCantBeExact, 1),
        ("list_too_much_splitter", ListTooMuchSplitter, 1),
        ("list_cant_have_different_sources", ListCantHaveDifferentSources, 1),
        ("list_cant_be_separeted_by_ind", ListCantBeSepareted, 1),
        ("list_cant_be_separeted_by_list", ListCantBeSepareted, 1),
        ("list_cant_be_separeted_by_blank", ListCantBeSepareted, 1),
        # list eclated
        ("list_eclated_no_instruction_beginning", ListEclatedNotConsistent, 1),
        ("list_eclated_instruction_bad_format", ListEclatedNotConsistent, 1),
        ("list_eclated_instruction_name_invalid", ListEclatedNotConsistent, 1),
        ("list_eclated_instruction_idx_element_invalid", ListEclatedNotConsistent, 1),
        ("list_eclated_duplicate_in_element", ListEclatedNotConsistent, 1),
        # list not eclated
        ("list_not_eclated_with_values", ListNotEclatedEmptyValues, 1),
        ("list_not_eclated_with_values2", ListNotEclatedEmptyValues, 1),
        # instructions
        ("instruction_ind_must_be_empty", InstructionIndMustBeEmpty, 1),
        # duplicates
        ("names_duplicated_ind", NameDuplicated, 1),
        ("names_duplicated_list", NameListDuplicated, 1),
        ("names_duplicated_between_ind_and_lst", NameDuplicated, 1),
    ],
)
def test_read_info_page_wrong(
    filename: str,
    expected_log_label_class: TYPE_EXPECTED_LOG_LABEL_CLASS,
    nb_expected_info: int,
):
    def f():
        eds = _read_infos(filename, "wrong")
        assert len(eds) == nb_expected_info

    wrapper_test_logs(
        runnable=f,
        expected_log_label_class=expected_log_label_class,
    )


@pytest.mark.parametrize(
    ["filename", "expected_log_label_class"],
    [
        ("no_worksheet", NoRightWorksheet),
    ],
)
def test_read_info_page_raise(
    filename: str,
    expected_log_label_class,
):
    wrapper_try(lambda: _read_infos(filename, "wrong"), expected_log_label_class)


# ------------------- Read info page and preprocess -------------------


def _read_infos_and_preprocess(filename: str) -> Dict[str, InfoExtractionDatas]:
    _, path_config_file = _from_folder_name_and_filename(
        f"{SUB_FOLDER_INFO_PAGE}/good", filename
    )
    return read_info_page_and_preprocess(ExcelBook(path_config_file))


ED_N1 = ExtractionData(name="n1", label_source_name="o1", row=3)
ED_N2 = ExtractionData(name="n2", label_source_name="o2", row=4)
ED_S1 = ExtractionData(name="s1", label_source_name="o1", row=3)


@pytest.mark.parametrize(
    ["filename", "expected_infos"],
    [
        # keep all (ind, list)
        ("one_just_name_and_source", {"o1": bied(inds=ED_N1)}),
        ("list_valid_one", {"o1": bied(lists={"n1": [ED_S1]})}),
        (
            "many_all",
            {
                "o1": bied(
                    inds=ED_N1,
                    lists={
                        "n3": [
                            ExtractionData(name="s1", label_source_name="o1", row=5),
                            ExtractionData(name="s2", label_source_name="o1", row=6),
                        ]
                    },
                ),
                "o2": bied(
                    inds=[
                        ExtractionData(name="n2", label_source_name="o2", row=4),
                        ExtractionData(name="n4", label_source_name="o2", row=7),
                    ]
                ),
            },
        ),
        # filter already done
        ("filter_done_ind", {"o2": bied(inds=ED_N2)}),
        ("filter_done_eclated", {"o1": bied(inds=ED_N1)}),
        (
            "filter_done_eclated2",
            {
                "o1": bied(
                    inds=ED_N1,
                    lists={
                        "n3": [ExtractionData(name="s1", label_source_name="o1", row=6)]
                    },
                )
            },
        ),
    ],
)
def test_read_info_page_preprocess_good(
    filename: str, expected_infos: Dict[str, InfoExtractionDatas]
):
    def f():
        infos = _read_infos_and_preprocess(filename)
        assert infos == expected_infos

    wrapper_test_good(f)


@pytest.mark.parametrize(
    ["filename"],
    [
        (filename,)
        for filename in os.listdir(
            PATH_TEST_DOCS_TESTSUITE / f"{SUB_FOLDER_INFO_PAGE}/good"
        )
    ],
)
def test_read_info_page_preprocess_all(filename):
    def f():
        _read_infos_and_preprocess(filename[:-5])
        logger.filter_logs_level(log_level_to_keep=ERROR)

    wrapper_test_logs(f, [])


# ------------------- Read info page info values -------------------


def _read_infos_values(filename: str) -> InfoValues:
    _, path_config_file = _from_folder_name_and_filename(
        f"{SUB_FOLDER_INFO_PAGE}/good", filename
    )
    return read_info_values(ExcelBook(path_config_file))


@pytest.mark.parametrize(
    ["filename", "expected_infos"],
    [
        ("values_one_ind_info", biv(inds={"n1": "t1"})),
        ("values_one_ind_info_without_source", biv(inds={"n1": "t1"})),
        ("values_one_ind_info_filter_one_without_value", biv(inds={"n1": "t1"})),
        ("values_one_lst_info", biv(lists={"n1": [{"s1": "t1"}]})),
        (
            "values_two_lst_info",
            biv(lists={"n1": [{"s1": "t1"}], "n2": [{"s1": "t2"}]}),
        ),
        (
            "values_one_lst_two_sub",
            biv(lists={"n1": [{"s1": "t1", "s2": "t2"}]}),
        ),
        (
            "values_one_lst_two_elements",
            biv(lists={"n1": [{"s1": "t1"}, {"s1": "t2"}]}),
        ),
        ("values_lst_not_eclated", biv()),
        ("values_lst_eclated_without_values", biv()),
        (
            "values_big",
            biv(
                inds={"n2": "t6", "n6": "t8"},
                lists={
                    "n1": [
                        {"s1": "t1", "s2": "t2", "s3": "t3"},
                        {"s1": "t4", "s2": "t5"},
                    ],
                    "n5": [{"s1": "t7"}],
                },
            ),
        ),
    ],
)
def test_read_info_page_values(
    filename: str, expected_infos: Dict[str, InfoExtractionDatas]
):
    def f():
        infos = _read_infos_values(filename)
        logger.filter_logs(EmptynessExcelCell)

        assert infos == expected_infos

    wrapper_test_good(f)


# ------------------- Read config file -------------------


def _read_config_file(
    filename: str, folder: str
) -> Tuple[TYPE_SOURCES, Dict[str, InfoExtractionDatas]]:
    path_folder, path_config_file = _from_folder_name_and_filename(
        filename=filename, folder_name=f"read_config_file/{folder}"
    )
    return read_config_file(path_config_file, path_folder_sources=path_folder)


@pytest.mark.parametrize(
    ["filename"],
    [
        ("ext_txt",),
        ("ext_pdf",),
    ],
)
def test_read_config_file_wrong(
    filename: str,
):
    wrapper_test_good(runnable=lambda: _read_config_file(filename, "good"))


DEFAULT_SOURCE = {"o1": "1.txt"}
DEFAULT_INFOS = {
    "o1": InfoExtractionDatas(
        independant_infos=[ExtractionData(name="n1", row=3, label_source_name="o1")],
        list_infos={},
    )
}


@pytest.mark.parametrize(
    ["filename", "expected_log_label_class", "expected_sources", "expected_infos"],
    [
        # ext
        ("ext_toto", ExtensionFileNotSupported, DEFAULT_SOURCE, DEFAULT_INFOS),
        ("ext_zip", ExtensionFileNotSupported, DEFAULT_SOURCE, DEFAULT_INFOS),
        ("ext_docx", ExtensionFileNotSupported, DEFAULT_SOURCE, DEFAULT_INFOS),
        ("ext_xlsx", ExtensionFileNotSupported, DEFAULT_SOURCE, DEFAULT_INFOS),
        # source
        ("source_not_useful", SourceNotUseful, DEFAULT_SOURCE, DEFAULT_INFOS),
        ("source_not_given", SourceNotGiven, DEFAULT_SOURCE, DEFAULT_INFOS),
        # empty because other problem
        (
            "ext_toto_so_empty_source",
            [ExtensionFileNotSupported, EmptyInfoExcel, EmptyInfoExcel],
            {},
            {},
        ),
        (
            "source_not_given_and_not_useful_so_all_empty",
            [SourceNotUseful, SourceNotGiven, EmptyInfoExcel, EmptyInfoExcel],
            {},
            {},
        ),
        # path not existing
        ("path_not_existing", [PathNotExisting], DEFAULT_SOURCE, DEFAULT_INFOS),
    ],
)
def test_read_config_file_no_warning(
    filename: str,
    expected_log_label_class: TYPE_EXPECTED_LOG_LABEL_CLASS,
    expected_sources,
    expected_infos,
):
    def f():
        sources, infos = _read_config_file(filename, "wrong")
        assert sources == expected_sources and infos == expected_infos

    wrapper_test_logs(
        runnable=f,
        expected_log_label_class=expected_log_label_class,
    )


def test_read_config_file_raise():
    wrapper_try(lambda: _read_config_file("not_existing", "wrong"), ExcelNotExisting)


# ------------------- Fill config file -------------------


def _fill_config_file(filename: str, folder: str, infos: InfoValues) -> None:
    folder_name = f"fill_config_file/{folder}"
    _, path_config_file = _from_folder_name_and_filename(
        filename=filename, folder_name=folder_name
    )
    output_path = PATH_TEST_DOCS_TESTSUITE / f"{folder_name}/{filename}_generated.xlsx"
    fill_config_file(
        path_config_file=path_config_file,
        infos=infos,
        path_output=output_path,
    )
    return output_path


def _excel_equals(path1: Path, path2: Path) -> bool:
    eb1 = ExcelBook(path1)
    eb2 = ExcelBook(path2)
    return eb1.equals(eb2)


@pytest.mark.parametrize(
    ["filename", "infos_values"],
    [
        ("ind_one", biv(inds={"n1": "t1"})),
        ("ind_two", biv(inds={"n1": "t1", "n2": "t2"})),
        ("lst_one", biv(lists={"n1": [{"s1": "t1"}]})),
        ("lst_two_elements", biv(lists={"n1": [{"s1": "t1"}, {"s1": "t2"}]})),
        (
            "lst_two_elements_description",
            biv(lists={"n1": [{"s1": "t1"}, {"s1": "t2"}]}),
        ),
        (
            "lst_only_second_found",
            biv(lists={"n1": [{"s2": "t2"}]}),
        ),
        (
            "list_and_ind",
            biv(
                inds={"n4": "t7"},
                lists={
                    "n3": [{"s1": "t3", "s2": "t4"}],
                },
            ),
        ),
        (
            "list_gap_ind",
            biv(
                inds={"n4": "t7"},
                lists={
                    "n3": [{"s1": "t3", "s2": "t4"}],
                },
            ),
        ),
        (
            "list_two_subnames_and_ind",
            biv(
                inds={"n4": "t7"},
                lists={
                    "n3": [{"s1": "t3", "s2": "t4"}, {"s1": "t5", "s2": "t6"}],
                },
            ),
        ),
        (
            "big",
            biv(
                inds={"n1": "t1", "n2": "t2", "n4": "t7"},
                lists={
                    "n3": [{"s1": "t3", "s2": "t4"}, {"s1": "t5", "s2": "t6"}],
                    "n5": [{"s1": "t8"}, {"s1": "t9", "s2": "t10"}],
                },
            ),
        ),
    ],
)
def test_fill_config_file_good(filename: str, infos_values: InfoValues):
    actual_path = _fill_config_file(filename, folder="good", infos=infos_values)
    expected_path = (
        PATH_TEST_DOCS_TESTSUITE / f"fill_config_file/good/{filename}_expected.xlsx"
    )
    assert _excel_equals(actual_path, expected_path)


@pytest.mark.parametrize(
    ["filename", "expected_log_label_class"],
    [
        ("not_existing", ExcelNotExisting),
        ("infos_not_existing", NoRightWorksheet),
    ],
)
def test_fill_config_file_raise(filename: str, expected_log_label_class):
    wrapper_try(
        lambda: _fill_config_file(filename, "wrong", biv()),
        expected_log_label_class,
    )
