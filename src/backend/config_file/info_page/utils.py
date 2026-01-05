from logging import WARNING

from backend.config_file.info_page import NAME_WORKSHEET, ROW_HEADER, TITLE_ERROR, Datas
from backend.excel.excel_book import ExcelBook
from backend.excel.excel_sheet import ExcelSheet


def check_header(es: ExcelSheet):

    for data in Datas:

        es.check_content_cell(
            page_name=TITLE_ERROR,
            row=ROW_HEADER,
            col=data.col,
            expected_content=data.header_name,
            log_level=WARNING,
        )


def get_excel_sheet(eb: ExcelBook) -> ExcelSheet:
    return eb.get_excel_sheet(NAME_WORKSHEET)
