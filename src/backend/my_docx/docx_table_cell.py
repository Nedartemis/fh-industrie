from dataclasses import dataclass

from docx.table import _Cell


@dataclass
class DocxTableCell:
    row: int
    col: int
    str: str
    original_cell: _Cell
