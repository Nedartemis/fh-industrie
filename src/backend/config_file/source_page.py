from collections import Counter
from pathlib import Path
from typing import Dict

from backend.excel.excel_book import ExcelBook, ExcelSheet
from logger import logger
from logs_label import (
    EmptyInfoExcel,
    OneNameWithMultiplePaths,
    OnePathWithMultipleNames,
)

# {
#   "source_name" : "source_path"
# }
TYPE_SOURCES = Dict[str, Path]

# str
NAME_WORKSHEET = "Sources"
HEADER_NAME = "Nom source"
HEADER_PATH = "Chemin d'accès fichier"

# cols and rows
COL_NAME = 2
COL_PATH = 3
ROW_HEADER = 2
FIRST_ROW_DATA = 3


def check_header(es: ExcelSheet, col: int, expected_header: str):
    es.check_content_cell(
        page_name=NAME_WORKSHEET,
        row=ROW_HEADER,
        col=col,
        expected_content=expected_header,
    )


def read_source_page(em: ExcelBook) -> TYPE_SOURCES:
    es = em.get_excel_sheet(name=NAME_WORKSHEET)

    # checks
    check_header(es, col=COL_NAME, expected_header=HEADER_NAME)
    check_header(es, col=COL_PATH, expected_header=HEADER_PATH)

    # reading

    sources: TYPE_SOURCES = {}

    for current_row in range(FIRST_ROW_DATA, es.get_row_dimension() + 1):

        # reading
        name_source = es.get_text_cell(row=current_row, col=COL_NAME)
        path_source = es.get_text_cell(row=current_row, col=COL_PATH)

        # checks
        if name_source is None:
            es.check_emptiness_row(
                page_name=NAME_WORKSHEET,
                row=current_row,
                header_name_cols=[(HEADER_PATH, COL_PATH)],
            )
            continue

        if es.check_fullness_row(
            page_name=NAME_WORKSHEET,
            row=current_row,
            header_name_cols=[(HEADER_PATH, COL_PATH)],
        ):
            continue

        # check
        if name_source in sources:
            paths = [sources[name_source], path_source]
            logger.error(
                msg=f"Name {name_source} is associated with multiple paths : {paths}",
                extra=OneNameWithMultiplePaths(name=name_source, paths=paths),
            )

        # store
        sources[name_source] = path_source

    # checks

    # - duplicates
    duplicates = [
        path
        for path, nb_occurences in Counter(sources.values()).items()
        if nb_occurences > 1
    ]
    for path_duplicated in duplicates:
        names = [name for name, path in sources.items() if path == path_duplicated]
        logger.warning(
            f"Path {str(path_duplicated)} is associated with multiple names : {names}",
            extra=OnePathWithMultipleNames(path=path_duplicated, names=names),
        )

    # - emptiness
    if len(sources) == 0:
        ll = EmptyInfoExcel(excel_name=em.get_excel_name(), page_name=NAME_WORKSHEET)
        logger.error(ll.msg(), extra=ll)

    return sources
