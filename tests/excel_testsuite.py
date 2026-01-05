import os

import pytest
from helper_testsuite import wrapper_test_good

from backend.excel.excel_book import ExcelBook
from backend.excel.excel_sheet_equality import equals_cell
from logger import f, logger
from vars import PATH_TEST_DOCS_TESTSUITE

# ------------------- Get cell -------------------


@pytest.mark.parametrize(
    ("filename", "text_expected"),
    [
        ("cell_rich_text", "le toto"),
    ],
)
def test_get_cell(filename: str, text_expected: str):
    path_folder = PATH_TEST_DOCS_TESTSUITE / "excel/get_cell"
    path = path_folder / f"{filename}.xlsx"

    def g():
        eb = ExcelBook(path)
        cell = eb.first_es.get_cell(row=1, col=1)
        assert cell.str == text_expected

    wrapper_test_good(runnable=g)


# ------------------- Equals -------------------


@pytest.mark.parametrize(
    ("filename"),
    [
        "text",
        "text2",
        "rich_cell_text",
        "bold",
        "bold_mix",
        "color_text",
        "color_background",
        "border",
        "underline",
        "second_cell",
        "merged_cell",
    ],
)
def test_not_equals(filename: str):
    path_folder = PATH_TEST_DOCS_TESTSUITE / "excel/equals"
    path1 = path_folder / f"{filename}.xlsx"
    path2 = path_folder / f"{filename}_not.xlsx"

    def runnable():
        assert not ExcelBook(path1).equals(ExcelBook(path2))

    wrapper_test_good(runnable=runnable)


@pytest.mark.parametrize(
    ("filename"),
    [
        "empty",
        "bold",
        "bold_mix",
        "color_text",
        "color_background",
        "border",
        "underline",
    ],
)
def test_equals_with_himself(filename: str):
    path_folder = PATH_TEST_DOCS_TESTSUITE / "excel/equals"
    path = path_folder / f"{filename}.xlsx"

    assert ExcelBook(path).equals(ExcelBook(path))


# ------------------- Copy -------------------


@pytest.mark.parametrize(
    ("filename"),
    [
        filename
        for filename in os.listdir(path=PATH_TEST_DOCS_TESTSUITE / "excel" / "equals")
        if not filename.endswith("_not.xlsx")
    ],
)
def test_copy_cell(filename: str):

    path_folder = PATH_TEST_DOCS_TESTSUITE / "excel" / "equals"
    path_input = path_folder / filename

    def runnable():
        # open
        eb = ExcelBook(path_excel=path_input)
        es = eb.first_es

        # copy
        cell_expected = es.get_cell(row=1, col=1)
        es.copy_cell(cell_expected, row=2, col=1)
        cell_actual = es.get_cell(row=2, col=1)

        # equals
        assert equals_cell(cell_actual, cell_expected, eb.wb)

    wrapper_test_good(runnable=runnable)


@pytest.mark.parametrize(
    ("filename"),
    ["rectangle"],
)
def test_copy_cell_rectangle(filename: str):

    path_folder = PATH_TEST_DOCS_TESTSUITE / "excel" / "copy"
    path_input = path_folder / f"{filename}.xlsx"
    path_output = path_folder / f"{filename}_actual.xlsx"
    path_expected = path_folder / f"{filename}_expected.xlsx"

    def runnable():
        # open
        eb = ExcelBook(path_excel=path_input)
        es = eb.first_es

        # copy
        es.copy_rectangle(
            from_row=1, from_col=1, nb_row=2, nb_col=3, to_row=4, to_col=2
        )
        eb.save(path_output)

        # equals
        assert eb.equals(ExcelBook(path_excel=path_expected))

    wrapper_test_good(runnable=runnable)
