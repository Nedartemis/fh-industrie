import itertools
from typing import Tuple

import openpyxl.cell.rich_text
from openpyxl import load_workbook


class ExcelManager:

    def __init__(self, path_excel):
        self.wb = load_workbook(path_excel, rich_text=True)
        self.ws = self.wb.worksheets[0]

    @staticmethod
    def _change(input: str, key: str, value: str, count: int) -> Tuple[str, int]:
        output = input.replace("{" + key + "}", value)
        if output != input:
            count += 1
        return output, count

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
                for key, value in infos.items():
                    cell_value, changes = ExcelManager._change(
                        cell_value, key, value, changes
                    )

                # write
                self.ws.cell(row, column, value=cell_value)
            elif isinstance(cell_value, openpyxl.cell.rich_text.CellRichText):
                # replace
                for i, e in enumerate(cell_value):
                    text = e if isinstance(e, str) else e.text

                    for key, value in infos.items():
                        text, changes = ExcelManager._change(text, key, value, changes)

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
