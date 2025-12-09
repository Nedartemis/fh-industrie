from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from backend.excel.excel_sheet import ExcelSheet
from logs_label import NoRightWorksheet


class ExcelBook:
    """Wrapper around openpyxl WorkBook"""

    def __init__(self, path_excel):
        self.path_excel = path_excel
        self.wb = load_workbook(path_excel, rich_text=True)
        self.first_ws: Worksheet = self.wb.worksheets[0]
        self.save = self.wb.save

    def get_excel_sheet(self, name: str) -> ExcelSheet:
        if name not in self.wb.sheetnames:
            raise NoRightWorksheet(
                excel_name=self.get_excel_name(),
                page_name=f"The page worksheet named '{name}' does not exist or is does not have the right name.",
            )
        return ExcelSheet(self.wb.worksheets[self.wb.sheetnames.index(name)])

    def get_excel_name(self) -> str:
        return Path(self.path_excel).name
