from dataclasses import dataclass

from docx.table import _Cell


@dataclass
class DocxTableCell:
    row: int
    col: int
    str: str
    original_cell: _Cell

    def __repr__(self):
        return f"Cell(row={self.row}, col={self.col}, str={self.str})"
