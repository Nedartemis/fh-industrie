from typing import Callable, List, Optional, Tuple

import openpyxl.cell.rich_text
from openpyxl.worksheet.worksheet import Worksheet

from logger import WARNING, f, logger
from logs_label import EmptynessExcelCell, ExactnessExcelCell, FullnessExcelCell


class ExcelSheet:
    """Wrapper around openpyxl Worksheet"""

    def __init__(self, ws: Worksheet):
        self.ws = ws

    def get_text_cell(self, row: int, col: int) -> Optional[str]:
        s = str(self.ws.cell(row, col).value).strip()
        return None if s is None or s == "" or s == "None" else s

    def get_dimensions(self) -> Tuple[int, int]:
        return (self.get_row_dimension(), self.get_col_dimension())

    def get_row_dimension(self) -> int:
        return self.ws.max_row

    def get_col_dimension(self) -> int:
        return self.ws.max_column

    def replace_text_in_cell(
        self,
        row: int,
        col: int,
        replace_text: Callable[[str], Tuple[str, int]],
    ) -> int:
        nb_changes = 0

        # read
        cell_value = self.ws.cell(row, col).value
        if cell_value is None:
            return nb_changes

        if isinstance(cell_value, str):
            # replace
            cell_value, nb_new_changes = replace_text(cell_value)
            nb_changes += nb_new_changes

            # write
            self.ws.cell(row, col, value=cell_value)
        elif isinstance(cell_value, openpyxl.cell.rich_text.CellRichText):
            # replace
            for i, e in enumerate(cell_value):
                text = e if isinstance(e, str) else e.text

                text, nb_new_changes = replace_text(text)
                nb_changes += nb_new_changes

                if isinstance(e, str):
                    cell_value[i] = text
                else:
                    cell_value[i] = openpyxl.cell.rich_text.TextBlock(e.font, text)

                self.ws.cell(row, col, value=cell_value)
        else:
            raise ValueError(f"Excel cell type not implemmented : {type(cell_value)}")

        return nb_changes

    def check_content_cell(
        self,
        page_name: str,
        row: int,
        col: int,
        expected_content: str,
        log_level: str = WARNING,
    ) -> bool:
        """
        Returns:
            bool: True if an error has been detected
        """

        content = self.get_text_cell(row=row, col=col)
        if content is None or content.lower() != expected_content.lower():
            logger.log(
                level=log_level,
                msg=f"{page_name} : Text cell{f(row=row, col=col)} should be '{expected_content}' but is '{content}'",
                extra=ExactnessExcelCell(
                    page_name=page_name,
                    row=row,
                    col=col,
                    expected=expected_content,
                    actual=content,
                ),
            )
            return True
        return False

    def check_emptiness_row(
        self,
        page_name: str,
        row: int,
        header_name_cols: Tuple[str, int],
        log_level: str = WARNING,
    ) -> bool:
        """
        Returns:
            bool: True if an error has been detected
        """

        not_empty_cols = [
            (header_name, content)
            for header_name, col in header_name_cols
            if (content := self.get_text_cell(row=row, col=col))
        ]

        if not_empty_cols:
            not_empty_cols_names = [header_name for header_name, _ in not_empty_cols]
            contents = [content for _, content in not_empty_cols]
            logger.log(
                level=log_level,
                msg=f"{page_name} : Column(s) [{', '.join(not_empty_cols_names)}] is/are not empty on the row {row}.\n"
                + f"Here is the content : {contents}.\n"
                + "The excel may have a mistake.",
                extra=FullnessExcelCell(
                    page_name=page_name,
                    header_names=not_empty_cols,
                    row=row,
                    actuals=contents,
                ),
            )

        return not_empty_cols

    def check_fullness_row(
        self,
        page_name: str,
        row: int,
        header_name_cols: List[Tuple[str, int]],
        log_level: str = WARNING,
    ) -> bool:
        """
        Returns:
            bool: True if an error has been detected
        """

        empty_cols = [
            header_name
            for header_name, col in header_name_cols
            if self.get_text_cell(row=row, col=col) is None
        ]

        if empty_cols:
            logger.log(
                level=log_level,
                msg=f"{page_name} : Column(s) {', '.join(empty_cols)} is/are empty on the row {row}.\n"
                + f"The excel may have a mistake.",
                extra=EmptynessExcelCell(
                    page_name=page_name, header_names=empty_cols, row=row
                ),
            )
        return empty_cols


if __name__ == "__main__":
    from backend.excel.excel_book import ExcelBook
    from vars import PATH_TEST_DOCS

    path = PATH_TEST_DOCS / "simple_extraction" / "fichier_configuration.xlsx"

    es = ExcelBook(path).get_excel_sheet("Sources")
    print(es.get_dimensions())
