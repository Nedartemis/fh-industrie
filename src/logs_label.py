from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# ------------------- Base -------------------


class LogLabel(ABC):
    def __getitem__(self, key):
        return self

    def __iter__(self):
        return iter(["label"])

    # @abstractmethod
    # def msg(self) -> str:
    #     pass


# ------------------- Excel -------------------


@dataclass
class ExcelNotExisting(LogLabel, RuntimeError):
    excel_path: Path


@dataclass
class NoRightWorksheet(LogLabel, RuntimeError):
    excel_name: str
    page_name: str


@dataclass
class EmptynessExcelCell(LogLabel):
    page_name: str
    header_names: List[str]
    row: int


@dataclass
class FullnessExcelCell(LogLabel):
    page_name: str
    header_names: List[str]
    row: int
    actuals: List[str]


@dataclass
class ExactnessExcelCell(LogLabel):
    page_name: str
    row: int
    col: int
    expected: str
    actual: str


@dataclass
class EmptyInfoExcel(LogLabel):
    excel_name: str
    page_name: str

    def msg(self):
        return (
            f"No worksheet named '{self.page_name}' in the workbook {self.excel_name}"
        )


# ------------------- File -------------------


@dataclass
class PathNotExisting(LogLabel):
    path: Path


@dataclass
class ExtensionFileNotSupported(LogLabel):
    path: Path


# ------------------- Data consistency -------------------


@dataclass
class OneNameWithMultiplePaths(LogLabel):
    name: str
    paths: List[Path]


@dataclass
class OnePathWithMultipleNames(LogLabel):
    path: Path
    names: List[str]


@dataclass
class NameDuplicated(LogLabel):
    name: str
    rows: Optional[List[int]] = None


@dataclass
class NameListDuplicated(LogLabel):
    first_name: str
    duplicate_names: List[str]


# ------------------- List -------------------


@dataclass
class ListCantBeExact(LogLabel):
    names: List[str]


@dataclass
class ListTooMuchSplitter(LogLabel):
    names: List[str]


@dataclass
class ListCantHaveDifferentSources(LogLabel):
    names: List[str]


@dataclass
class ListCantBeSepareted(LogLabel):
    names: List[str]


@dataclass
class ListEclatedNotConsistent(LogLabel):
    first_name: str


@dataclass
class ListNotEclatedEmptyValues(LogLabel):
    first_name: str


# ------------------- Instruction -------------------


@dataclass
class InstructionIndMustBeEmpty(LogLabel):
    names_and_rows: List[Tuple[str, int]]


# ------------------- Other -------------------


@dataclass
class SourceNotUseful(LogLabel):
    source: str


@dataclass
class SourceNotGiven(LogLabel):
    name_source: str


if __name__ == "__main__":
    pass
