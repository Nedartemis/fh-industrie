from dataclasses import dataclass
from typing import Any, Optional, Union

from openpyxl.cell.rich_text import CellRichText
from openpyxl.styles.borders import Border
from openpyxl.styles.fills import PatternFill
from openpyxl.styles.fonts import Font


@dataclass
class Cell:
    row: int
    col: int
    value: Optional[Union[CellRichText, str]]
    str: Optional[str]
    font: Font
    fill: PatternFill
    border: Border
    alignment: Any
    number_format: Any
    protection: Any
    has_style: bool
