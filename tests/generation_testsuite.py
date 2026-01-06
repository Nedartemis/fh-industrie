from pathlib import Path
from typing import Dict

import pytest
from helper_testsuite import biv, wrapper_test_good, wrapper_try

from backend.excel.excel_book import ExcelBook
from backend.generation.fill_docx import fill_template_docx
from backend.generation.fill_excel import fill_template_excel
from backend.generation.fill_template import fill_template
from backend.generation.replace_text import replace_text
from backend.info_struct import InfoValues
from backend.my_docx.docx_helper import docx_equals
from backend.my_docx.my_docx import Docx
from logs_label import DuplicatesNameAfterHarmonization
from vars import PATH_TEST_DOCS_TESTSUITE

# ------------------- Replace text -------------------


@pytest.mark.parametrize(
    [
        "s",
        "pair_old_new",
        "text_expected",
        "nb_changes_expected",
        "border_left",
        "border_right",
        "do_harmonization",
    ],
    [
        # basics
        ("{n1}", {"n1": "v1"}, "v1", 1, "{", "}", True),
        ("{n1}", {"n1": "v1"}, "v1", 1, "{", "}", False),
        # borders
        ("<<n1>>", {"n1": "v1"}, "v1", 1, "<<", ">>", True),
        ("{n1}", {"n1": "v1"}, "{n1}", 0, "<<", ">>", True),
        ("<n1>>>>", {"n1": "v1"}, "v1", 1, "<", ">>>>", True),
        ("<<<<n1>", {"n1": "v1"}, "v1", 1, "<<<<", ">", True),
        # harmonization
        ("{é}", {"e": "v1"}, "v1", 1, "{", "}", True),
        ("{e}", {"è": "v1"}, "v1", 1, "{", "}", True),
        ("{é}", {"è": "v1"}, "v1", 1, "{", "}", True),
        ("{é}", {"e": "v1"}, "{é}", 0, "{", "}", False),
        # multiple
        ("{n1} {n2} {n3}", {"n1": "v1", "n3": "v3"}, "v1 {n2} v3", 2, "{", "}", True),
    ],
)
def test_replace_text_good(
    s: str,
    pair_old_new: Dict[str, str],
    text_expected: str,
    nb_changes_expected: int,
    border_left: str,
    border_right: str,
    do_harmonization: bool,
):

    def f():
        res = replace_text(
            s=s,
            pair_old_new=pair_old_new,
            border_left=border_left,
            border_right=border_right,
            do_harmonization=do_harmonization,
        )
        assert res.changed_text == text_expected
        assert res.nb_changes == nb_changes_expected

    wrapper_test_good(runnable=f)


def test_replace_text_raise():

    def f():
        replace_text(
            s="{é}",
            pair_old_new={"é": "v1", "è": "v2"},
            border_left="{",
            border_right="}",
            do_harmonization=True,
        )

    wrapper_try(runnable=f, expected_log_label_class=DuplicatesNameAfterHarmonization)


# ------------------- Docx -------------------


@pytest.mark.parametrize(
    ["filename", "infos"],
    [
        ("ind", biv(inds={"n1": "v1", "n3": "v3"})),
        ("bold", biv(inds={"n1": "v1"})),
        ("background", biv(inds={"n1": "v1"})),
        ("background_mix", biv(inds={"n1": "v1"})),
        ("mix_style", biv(inds={"n1": "v1"})),
        ("split_run", biv(inds={"n1": "v1"})),
        ("table_ind", biv(inds={"n1": "v1", "n2": "v2", "n3": "v3"})),
        ("table_style", biv(inds={"n1": "v1", "n2": "v2", "n3": "v3"})),
        ("image", biv()),
        (
            "image_between_text",
            biv(inds={"n1": "v1", "n2": "v2", "n3": "v3", "n4": "v4"}),
        ),
        ("hyperlink", biv()),
        ("hyperlink_between_text", biv({"n1": "v1", "n2": "v2"})),
        ("ind_none", biv(inds={"n1": None, "n2": "v2"})),
        # list table
        ("list_table", biv(lists={"n1": [{"s1": "v1", "s2": "v2"}]})),
        ("list_table_same_row", biv(lists={"n1": [{"s1": "v1"}]})),
        ("list_table_two_elements", biv(lists={"n1": [{"s1": "v1"}, {"s1": "v2"}]})),
        (
            "list_table_big",
            biv(
                lists={
                    "n1": [
                        {
                            "s1": "v11",
                            "s2": "v12",
                            "s3": "v13",
                            "s4": "v14",
                            "s5": "v15",
                            "s6": "v16",
                        },
                        {"s1": "v21", "s3": "v23"},
                        {"s1": "v31", "s6": "v36"},
                    ]
                }
            ),
        ),
        # list sin table
        ("list_sin_table_simple", biv(lists={"n1": [{"s1": "v1"}]})),
        (
            "list_sin_table_many_lines",
            biv(
                lists={
                    "n1": [
                        {"s1": "v1", "s2": "v2", "s3": "v3"},
                        {"s1": "v4", "s2": "v5", "s3": "v6"},
                    ]
                }
            ),
        ),
        (
            "list_sin_table_three_elements",
            biv(lists={"n1": [{"s1": "v1"}, {"s1": "v2"}, {"s1": "v3"}]}),
        ),
        (
            "list_sin_table_two_lists",
            biv(
                lists={
                    "n1": [{"s1": "v1"}, {"s1": "v2"}],
                    "n2": [{"s1": "v3"}, {"s1": "v4"}],
                }
            ),
        ),
        ("list_sin_table_styles", biv(lists={"n1": [{"s1": "v1", "s2": "v2"}]})),
        ("list_sin_table_empty_infos", biv(lists={})),
    ],
)
def test_fill_docx(filename: str, infos: InfoValues):

    path = PATH_TEST_DOCS_TESTSUITE / "generation/docx"
    path_input = path / f"{filename}.docx"
    path_output = path / f"{filename}_actual.docx"
    path_expected = path / f"{filename}_expected.docx"

    def f():
        fill_template_docx(
            template_path=path_input, infos=infos, path_output=path_output
        )
        assert docx_equals(d1=Docx(path_output), d2=Docx(path_expected))

    wrapper_test_good(runnable=f)


# ------------------- Excel -------------------


@pytest.mark.parametrize(
    ["filename", "infos"],
    [
        # ind
        ("ind", biv(inds={"n1": "v1"})),
        ("ind_two_same_cell", biv(inds={"n1": "v1", "n2": "v2"})),
        (
            "ind_two_same_cell2",
            biv(
                inds={
                    "libelle_demandeurs": "MASSERES",
                    "libelle_defendeurs": "SARL BRUGOT & Autres",
                }
            ),
        ),
        # list
        ("list_simple", biv(lists={"n1": [{"s1": "v1", "s2": "v2"}]})),
        ("list_start_end_same_line", biv(lists={"n1": [{"s1": "v1"}]})),
        (
            "list_two_elements",
            biv(lists={"n1": [{"s1": "v1", "s2": "v2"}, {"s1": "v3", "s2": "v4"}]}),
        ),
        ("list_copy_all", biv(lists={"n1": [{"s1": "v1", "s2": "v2", "s3": "v3"}]})),
        (
            "list_replace_and_dont_replace",
            biv(lists={"n1": [{"s1": "v1", "s2": "v2"}]}),
        ),
        ("list_empty_infos", biv(lists={})),
        ("list_empty_half_infos", biv(lists={"n1": [{"s1": "v1", "s2": "v2"}]})),
    ],
)
def test_fill_xlsx(filename: str, infos: InfoValues):

    path = PATH_TEST_DOCS_TESTSUITE / "generation/xlsx"
    path_input = path / f"{filename}.xlsx"
    path_output = path / f"{filename}_actual.xlsx"
    path_expected = path / f"{filename}_expected.xlsx"

    def runnable():
        fill_template_excel(path_excel=path_input, infos=infos, path_output=path_output)
        assert ExcelBook(path_output).equals(ExcelBook(path_expected))

    wrapper_test_good(runnable=runnable)


# ------------------- General -------------------


@pytest.mark.parametrize(
    ["template_filename"],
    [
        ("excel_ind.xlsx",),
        ("docx_ind.docx",),
    ],
)
def test_fill_template_general(template_filename: str):

    path = PATH_TEST_DOCS_TESTSUITE / "generation/general"
    tfp = Path(template_filename)
    template_path = path / template_filename
    infos_path_file = path / f"{tfp.stem}_config_file.xlsx"
    expected_generated_path = path / f"{tfp.stem}_expected{tfp.suffix}"

    def runnable():
        generated_file = fill_template(
            infos_path_file=infos_path_file,
            template_path=template_path,
            path_folder_output=path,
        )

        if tfp.suffix == ".docx":
            assert docx_equals(
                d1=Docx(generated_file), d2=Docx(expected_generated_path)
            )
        elif tfp.suffix == ".xlsx":
            assert ExcelBook(generated_file).equals(ExcelBook(expected_generated_path))
        else:
            assert False

    wrapper_test_good(runnable=runnable)
