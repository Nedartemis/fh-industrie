from dataclasses import dataclass


@dataclass
class CellBase:
    row: int
    col: int
    str: str
