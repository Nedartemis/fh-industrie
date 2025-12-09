from dataclasses import dataclass
from enum import Enum
from logging import WARNING
from typing import Dict, List, Optional

from backend.excel.excel_book import ExcelBook
from backend.excel.excel_sheet import ExcelSheet
from backend.info_struct.extraction_data import ExtractionData

# ------------------------- Constants -------------------------


class Datas(Enum):
    INSTRUCTION = (1, "Instruction")
    NAME = (2, "Nom information")
    DESCRIPTION = (3, "Descriptif de l'information")
    LABEL_SOURCE_NAME = (4, "Nom source")
    VALUE = (5, "Information")
    EXTRACT_EXACTLY_INFO = (6, "Texte exact")

    def __init__(self, col, header_name: str):
        super().__init__()
        self.col = col
        self.header_name = header_name


# str
NAME_WORKSHEET = "Infos à extraire"
TITLE_ERROR = "Config file header info"

# cols and rows
FIRST_ROW_INFO = 3
ROW_HEADER = 2

# ------------------------- Consistency -------------------------


def check_header(es: ExcelSheet):

    for data in Datas:

        es.check_content_cell(
            page_name=TITLE_ERROR,
            row=ROW_HEADER,
            col=data.col,
            expected_content=data.header_name,
            log_level=WARNING,
        )


# ------------------------- Utils -------------------------


def get_excel_sheet(eb: ExcelBook) -> ExcelSheet:
    return eb.get_excel_sheet(NAME_WORKSHEET)


# ------------------------- Structure -------------------------
