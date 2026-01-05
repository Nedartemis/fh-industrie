import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pytest
from helper_testsuite import (
    bed,
    bied,
    biv,
    wrapper_test_good,
    wrapper_test_logs,
    wrapper_try,
)

from backend.excel.excel_book import ExcelBook
from backend.extraction.extract_from_txt import extract_from_txt
from backend.extraction.extract_info_from_config_file_and_documents import (
    extract_infos_from_config_file_and_files_tree,
)
from backend.extraction.extract_info_from_natural_language import (
    extract_info_from_natural_language,
)
from backend.extraction.extract_info_from_pdf import extract_info_from_pdf
from backend.info_struct import InfoExtractionDatas, InfoValues
from backend.llm.llm_test import LlmTest
from logger import ERROR, logger
from logs_label import (
    ExtensionFileNotSupported,
    ExtractionNotFoundInfo,
    FileDataError,
    LlmFailedAnswer,
    PathNotExisting,
)
from vars import PATH_TEST_DOCS_TESTSUITE

# ------------------- Utils -------------------

PATH_DIR_TESTS = PATH_TEST_DOCS_TESTSUITE / "extraction"

# ------------------- From natural language -------------------


@pytest.mark.parametrize(
    ["ied", "text", "expected", "force_answer"],
    [
        # empty
        (bied(inds=[bed(name="n1")]), "", biv(), None),
        # short ind + test text
        (bied(inds=[bed(name="n1")]), "n1:v1", biv(inds={"n1": "v1"}), None),
        (bied(inds=[bed(name="n1")]), "n2:v2", biv(), None),
        # exact
        (
            bied(inds=[bed(name="n1", exact=True)]),
            "12345",
            biv(inds={"n1": "234"}),
            '"debut": "2", "fin": "4"',
        ),
        # list
        (
            bied(lists={"n1": [bed(name="s1")]}),
            None,
            biv(lists={"n1": [{"s1": "v1"}]}),
            '"n1":[{"s1": "v1"}]',
        ),
        # all
        (
            bied(
                inds=[bed(name="n1"), bed(name="n3", exact=True)],
                lists={"n2": [bed(name="s1")]},
            ),
            "12345",
            biv(
                inds={"n1": "v1", "debut": "2", "fin": "4", "n3": "234"},
                lists={"n2": [{"s1": "v2"}]},
            ),
            '"n1":"v1", "debut": "2", "fin": "4", "n2":[{"s1": "v2"}]',
        ),
    ],
)
def test_from_natural_language_good(
    ied: InfoExtractionDatas,
    text: Optional[str],
    expected: InfoValues,
    force_answer: Optional[str],
):
    llm = LlmTest(force_answer=force_answer)

    def f():
        actual = extract_info_from_natural_language(
            llm=llm, info_to_extract=ied, text=text
        )
        assert actual == expected

    wrapper_test_good(runnable=f)


@pytest.mark.parametrize(
    ["ied", "text", "force_answer", "expected", "expected_log_label_class"],
    [
        # short ind
        (bied(inds=[bed(name="n1")]), "1", "toto", biv(), LlmFailedAnswer),
        # list
        (bied(lists={"n1": [bed(name="s1")]}), "1", "toto", biv(), LlmFailedAnswer),
        # exact
        (bied(inds=[bed(name="n1", exact=True)]), "1", "toto", biv(), LlmFailedAnswer),
    ],
)
def test_from_natural_language_wrong(
    ied: InfoExtractionDatas,
    text: Optional[str],
    force_answer: str,
    expected: InfoValues,
    expected_log_label_class,
):
    llm = LlmTest(force_answer=force_answer)

    def f():
        actual = extract_info_from_natural_language(
            llm=llm, info_to_extract=ied, text=text
        )
        assert actual == expected

    wrapper_test_logs(runnable=f, expected_log_label_class=expected_log_label_class)


# ------------------- From pdf -------------------


@pytest.mark.parametrize(
    ["ied", "pdf_filename", "expected"],
    [
        (
            bied(inds=[bed(name="n1")]),
            "n1_v1",
            biv(inds={"n1": "v1"}),
        )
    ],
)
def test_from_pdf_good(
    ied: InfoExtractionDatas, pdf_filename: str, expected: InfoValues
):
    llm = LlmTest()
    path_pdf = PATH_DIR_TESTS / f"{pdf_filename}.pdf"

    def f():
        actual = extract_info_from_pdf(llm=llm, path_pdf=path_pdf, info_to_extract=ied)
        assert actual == expected

    wrapper_test_good(runnable=f)


@pytest.mark.parametrize(
    ["ied", "pdf_filename", "force_answer", "expected", "expected_log_label_class"],
    [
        (
            bied(inds=[bed(name="n1")]),
            "not_existing.pdf",
            "toto",
            biv(inds={}),
            PathNotExisting,
        ),
        (
            bied(inds=[bed(name="n1")]),
            "txt_as_pdf.pdf",
            "toto",
            biv(inds={}),
            FileDataError,
        ),
    ],
)
def test_from_pdf_wrong(
    ied: InfoExtractionDatas,
    pdf_filename: str,
    force_answer: str,
    expected: InfoValues,
    expected_log_label_class,
):
    llm = LlmTest(force_answer=force_answer)
    path_pdf = PATH_DIR_TESTS / pdf_filename

    def f():
        actual = extract_info_from_pdf(llm=llm, path_pdf=path_pdf, info_to_extract=ied)
        assert actual == expected

    wrapper_test_logs(runnable=f, expected_log_label_class=expected_log_label_class)


def test_from_pdf_raise():

    llm = LlmTest()
    path_pdf = PATH_DIR_TESTS / "toto.txt"

    wrapper_try(
        runnable=lambda: extract_info_from_pdf(
            llm=llm, path_pdf=path_pdf, info_to_extract=bied()
        ),
        expected_log_label_class=ExtensionFileNotSupported,
    )


# ------------------- From txt -------------------


@pytest.mark.parametrize(
    ["ied", "txt_filename", "expected"],
    [
        (
            bied(inds=[bed(name="n1")]),
            "n1_v1",
            biv(inds={"n1": "v1"}),
        )
    ],
)
def test_from_txt_good(
    ied: InfoExtractionDatas, txt_filename: str, expected: InfoValues
):
    llm = LlmTest()
    path_txt = PATH_DIR_TESTS / f"{txt_filename}.txt"

    def f():
        actual = extract_from_txt(llm=llm, path_txt=path_txt, info_to_extract=ied)
        assert actual == expected

    wrapper_test_good(runnable=f)


@pytest.mark.parametrize(
    ["ied", "pdf_filename", "force_answer", "expected", "expected_log_label_class"],
    [
        (
            bied(inds=[bed(name="n1")]),
            "not_existing",
            "toto",
            biv(inds={}),
            PathNotExisting,
        ),
    ],
)
def test_from_txt_wrong(
    ied: InfoExtractionDatas,
    pdf_filename: str,
    force_answer: str,
    expected: InfoValues,
    expected_log_label_class,
):
    llm = LlmTest(force_answer=force_answer)
    path_txt = PATH_DIR_TESTS / f"{pdf_filename}.txt"

    def f():
        actual = extract_from_txt(llm=llm, path_txt=path_txt, info_to_extract=ied)
        assert actual == expected

    wrapper_test_logs(runnable=f, expected_log_label_class=expected_log_label_class)


def test_from_txt_raise():

    llm = LlmTest()
    path_txt = PATH_DIR_TESTS / "n1_v1.pdf"

    wrapper_try(
        runnable=lambda: extract_from_txt(
            llm=llm, path_txt=path_txt, info_to_extract=bied()
        ),
        expected_log_label_class=ExtensionFileNotSupported,
    )


# ------------------- From config file and documents -------------------


@dataclass
class ConfigFilePaths:
    folder_config_file: Path
    config_file: Path
    config_file_expected: Path
    folder_sources: Path


def _get_config_paths(
    folder_config_file: str, config_file_name: str, folder_sources_name: str
) -> ConfigFilePaths:
    path_folder_confong_file = PATH_DIR_TESTS / folder_config_file
    path_config_file = path_folder_confong_file / f"{config_file_name}.xlsx"
    path_config_file_expected = (
        path_folder_confong_file / f"{config_file_name}_expected.xlsx"
    )
    path_folder_sources = PATH_DIR_TESTS / folder_sources_name

    return ConfigFilePaths(
        folder_config_file=path_folder_confong_file,
        config_file=path_config_file,
        config_file_expected=path_config_file_expected,
        folder_sources=path_folder_sources,
    )


@pytest.mark.parametrize(
    ["config_file_name", "folder_sources_name", "reset_logs"],
    [
        ("simple_pdf", "./", False),
        ("simple_txt", "./", False),
        ("simple_txt", ".", False),
        ("simple_txt", "", False),
        ("file_sub_folder", "./", False),
        ("file_sub_folder2", "sub_folder/", False),
        ("useless_root_folder", "./", False),
        ("no_extraction", "./", True),
        ("multiple_sources", "./", False),
        ("list", "./", False),
        ("info_not_found", "./", True),
        ("gap", "./", False),
        ("gap_and_not_found", "./", True),
        ("list_and_ind", "./", False),
        ("hard", "./", True),
    ],
)
def test_from_config_file_and_files_tree_good(
    config_file_name: str, folder_sources_name: str, reset_logs: bool
):

    paths = _get_config_paths(
        folder_config_file="config_file",
        config_file_name=config_file_name,
        folder_sources_name=folder_sources_name,
    )

    expected = ExcelBook(paths.config_file_expected)

    def f():
        path_config_file_filled = extract_infos_from_config_file_and_files_tree(
            path_config_file=paths.config_file,
            path_folder_sources=paths.folder_sources,
            path_folder_output=paths.folder_config_file,
        )
        actual = ExcelBook(path_config_file_filled)
        assert actual.equals(expected)
        if reset_logs:
            logger.reset_logs()

    without_internet = os.environ.get("TEST_WITHOUT_INTERNET")
    if not without_internet:
        os.environ["TEST_WITHOUT_INTERNET"] = "true"

    wrapper_test_good(f)

    if not without_internet:
        os.environ.pop("TEST_WITHOUT_INTERNET")


@pytest.mark.parametrize(
    ["folder_sources_name", "expected_log_label_class"],
    (
        [
            ("ind", []),
            ("list", ExtractionNotFoundInfo),
            ("exact", []),
        ]
        if os.environ.get("TEST_WITHOUT_INTERNET") is None
        else []
    ),
)
def test_from_config_file_and_files_tree_good_claude(
    folder_sources_name: str, expected_log_label_class
):

    paths = _get_config_paths(
        folder_config_file=folder_sources_name,
        config_file_name="fichier_configuration",
        folder_sources_name=folder_sources_name,
    )

    expected = ExcelBook(paths.config_file_expected)

    def f():
        path_config_file_filled = extract_infos_from_config_file_and_files_tree(
            path_config_file=paths.config_file,
            path_folder_sources=paths.folder_sources,
            path_folder_output=paths.folder_config_file,
        )
        actual = ExcelBook(path_config_file_filled)
        assert actual.equals(expected)

    wrapper_test_logs(runnable=f, expected_log_label_class=expected_log_label_class)


@pytest.mark.parametrize(
    [
        "config_file_name",
        "folder_sources_name",
        "path_folder_output",
        "expected_log_label_class",
    ],
    [
        ("not_existing.txt", "./", None, PathNotExisting),
        ("simple_txt.txt", "not_existing", None, PathNotExisting),
        ("simple_txt.txt", "./", "not_existing", PathNotExisting),
    ],
)
def test_from_config_file_and_files_tree_raise(
    config_file_name: str,
    folder_sources_name: str,
    path_folder_output: Optional[str],
    expected_log_label_class,
):
    paths = _get_config_paths(
        folder_config_file="config_file",
        config_file_name=config_file_name,
        folder_sources_name=folder_sources_name,
    )

    def f():
        extract_infos_from_config_file_and_files_tree(
            path_config_file=paths.config_file,
            path_folder_sources=paths.folder_sources,
            path_folder_output=path_folder_output,
        )

    wrapper_try(runnable=f, expected_log_label_class=expected_log_label_class)
