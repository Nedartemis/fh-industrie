from abc import ABC, abstractmethod
from typing import Callable, Generic, List, Optional, Tuple, TypeVar

from backend.table.cell_base import CellBase
from logger import f, logger

CELL_TYPE = TypeVar("Cell type", bound=CellBase)


class TableBase(Generic[CELL_TYPE], ABC):

    # ------------------- Abstract method -------------------

    @abstractmethod
    def get_row_dimension(self) -> int:
        pass

    @abstractmethod
    def get_col_dimension(self) -> int:
        pass

    @abstractmethod
    def insert_rows(self, row: int, amount: int) -> None:
        pass

    @abstractmethod
    def replace_text_in_cell(
        self,
        row: int,
        col: int,
        replace_text: Callable[[str], Tuple[str, int]],
    ) -> int:
        pass

    @abstractmethod
    def copy_cell(self, src_cell, row: int, col: int) -> None:
        pass

    @abstractmethod
    def get_cell(self, row: int, col: int) -> CELL_TYPE:
        pass

    # ------------------- Default method -------------------

    def get_dimensions(self) -> Tuple[int, int]:
        return (self.get_row_dimension(), self.get_col_dimension())

    def copy_rectangle(
        self,
        from_row: int,
        from_col: int,
        to_row: int,
        to_col: int,
        nb_row: Optional[int] = None,
        nb_col: Optional[int] = None,
    ) -> None:

        max_row, max_col = self.get_dimensions()

        if nb_row is None:
            nb_row = (max_row + 1) - from_row

        if nb_col is None:
            nb_col = (max_col + 1) - from_col

        # copy
        texts: List[List[CELL_TYPE]] = [
            [self.get_cell(row, col) for col in range(from_col, from_col + nb_col)]
            for row in range(from_row, from_row + nb_row)
        ]

        # paste
        for row, lst in enumerate(texts, start=to_row):
            for col, cell in enumerate(lst, start=to_col):

                if row > max_row or col > max_col:
                    logger.warning(
                        f"Try to copy excel cell outside of the border of the excel. Action not done and just ignored. {f(row=row, col=col, max_row=max_row, max_col=max_col)}"
                    )
                    continue

                self.copy_cell(src_cell=cell, row=row, col=col)
