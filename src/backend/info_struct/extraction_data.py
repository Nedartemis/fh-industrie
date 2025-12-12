from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractionData:
    name: str
    row: int
    label_source_name: Optional[str] = None
    instruction: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    extract_exactly_info: bool = False
