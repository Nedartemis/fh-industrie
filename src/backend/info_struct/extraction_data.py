from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractionData:
    name: str
    label_source_name: str
    row: int
    instruction: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    extract_exactly_info: bool = False
