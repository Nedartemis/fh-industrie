import itertools
from typing import Tuple

import openpyxl.cell.rich_text
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from backend.generation import BORDER_LEFT, BORDER_RIGHT, HARMONIZE_LABEL_INFO
from backend.generation.replace_text import replace_text


class ExcelManager:

    def __init__(self, path_excel):
        self.wb = load_workbook(path_excel, rich_text=True)
        self.ws: Worksheet = self.wb.worksheets[0]

    @staticmethod
    def _change(input: str, infos: dict, count: int) -> Tuple[str, int]:
        output, plus_count = replace_text(
            s=input,
            pair_old_new=list(infos.items()),
            border_left=BORDER_LEFT,
            border_right=BORDER_RIGHT,
            do_harmonization=HARMONIZE_LABEL_INFO,
        )
        return output, count + plus_count

    @classmethod
    def get_text(cls, ws: Worksheet, row: int, col: int) -> str:
        s = cls.get_text_cell(ws.cell(row, col).value).strip()
        return None if not s or s == "None" else s

    @staticmethod
    def get_text_cell(cell_value) -> str:
        return str(cell_value)

    def get_worksheet(self, name: str) -> Worksheet:
        if name not in self.wb.sheetnames:
            raise RuntimeError(
                f"The page worksheet named '{name}' does not exist or is does not have the right name."
            )
        return self.wb.worksheets[self.wb.sheetnames.index(name)]

    def replace_content(self, infos: dict, verbose: bool = True) -> None:
        n = 100

        changes = 0

        for row, column in itertools.product(range(1, n), range(1, n)):
            # read
            cell_value = self.ws.cell(row, column).value
            if cell_value is None:
                continue

            if isinstance(cell_value, str):
                # replace
                cell_value, changes = ExcelManager._change(cell_value, infos, changes)

                # write
                self.ws.cell(row, column, value=cell_value)
            elif isinstance(cell_value, openpyxl.cell.rich_text.CellRichText):
                # replace
                for i, e in enumerate(cell_value):
                    text = e if isinstance(e, str) else e.text

                    text, changes = ExcelManager._change(text, infos, changes)

                    if isinstance(e, str):
                        cell_value[i] = text
                    else:
                        e.text = text

                    self.ws.cell(row, column, value=cell_value)
            else:
                raise ValueError(
                    f"Excel cell type not implemmented : {type(cell_value)}"
                )

        if verbose:
            print(f"Excel changes : {changes}")

    def save(self, path_excel) -> None:
        self.wb.save(path_excel)


def _main():
    from vars import PATH_TEST

    # check if the conversion of CellRichText to str is good
    em = ExcelManager(PATH_TEST / "test_celine" / "fichier_configuration.xlsx")
    ws = em.get_worksheet("Infos à extraire")
    for row in range(1, len(ws.row_dimensions)):
        cell_value = ws.cell(row, column=2).value
        s = em.get_text_cell(cell_value)
        print(type(cell_value), cell_value, s)


if __name__ == "__main__":
    _main()
