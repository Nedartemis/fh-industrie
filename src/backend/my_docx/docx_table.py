from copy import deepcopy
from typing import Callable, Tuple

from docx.table import Table, _Cell

from backend.my_docx.docx_helper import replace_text_paragraphs
from backend.my_docx.docx_table_cell import DocxTableCell
from backend.my_docx.my_docx import Docx
from backend.table.table_base import TableBase


class DocxTable(TableBase[DocxTableCell]):

    def __init__(self, doc: Docx, table: Table):
        self.doc = doc
        self.table = table

    def get_row_dimension(self):
        return len(self.table.rows)

    def get_col_dimension(self):
        return max(len(row.cells) for row in self.table.rows)

    def get_cell(self, row, col, copy: bool = True) -> DocxTableCell:
        cell = self.table.rows[row - 1].cells[col - 1]
        return DocxTableCell(
            row=row,
            col=col,
            str=cell.text,
            original_cell=(
                _Cell(deepcopy(cell._tc), parent=self.table) if copy else cell
            ),
        )

    def insert_rows(self, row: int, amount: int) -> None:
        rows = self.table.rows
        row_idx = row - 1

        if row_idx < 0 or row_idx > len(rows):
            raise IndexError("row index out of range")

        # Use a reference row for structure + formatting
        ref_row = rows[row_idx - 1] if row_idx > 0 else rows[0]

        for _ in range(amount):
            new_tr = deepcopy(ref_row._tr)

            if row == 0:
                rows[row_idx]._tr.addprevious(new_tr)
            else:
                rows[row_idx - 1]._tr.addnext(new_tr)

    def replace_text_in_cell(
        self, row, col, replace_text: Callable[[str], Tuple[str, int]]
    ) -> int:
        paragraphs = self.get_cell(row, col, copy=False).original_cell.paragraphs
        return replace_text_paragraphs(
            doc=self.doc, paragraphs=paragraphs, replace_text=replace_text
        )

    def copy_cell(self, src_cell: DocxTableCell, row, col) -> None:

        dst_cell = self.get_cell(row, col, copy=False)

        src_tc = src_cell.original_cell._tc
        dst_tc = dst_cell.original_cell._tc

        # Remove existing content
        dst_tc.clear_content()

        # Copy all children (paragraphs, properties, etc.)
        for child in src_tc:
            dst_tc.append(deepcopy(child))

    def remove_column(self, col: int) -> None:

        col_idx = col - 1

        if col_idx < 0:
            raise IndexError("Column index must be >= 0")

        # Remove the cell from each row
        for row in self.table.rows:
            cells = row._tr.tc_lst
            if col_idx >= len(cells):
                raise IndexError("Column index out of range")
            row._tr.remove(cells[col_idx])

        # Remove gridCol if tblGrid exists
        tbl = self.table._tbl
        if tbl.__dict__.get("tblGrid") is not None:
            grid_cols = tbl.tblGrid.gridCol_lst
            if col_idx < len(grid_cols):
                tbl.tblGrid.remove(grid_cols[col_idx])


if __name__ == "__main__":

    from backend.my_docx.my_docx import Docx
    from vars import PATH_TEST_DOCS_TESTSUITE

    path = PATH_TEST_DOCS_TESTSUITE / f"docx/table/empty_merged_rows.docx"

    doc = Docx(path=path)
    e = DocxTable(doc, doc.tables[0]).get_dimensions()
    print(e)
