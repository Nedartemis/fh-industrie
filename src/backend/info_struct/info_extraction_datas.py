from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

from backend.info_struct.extraction_data import ExtractionData


@dataclass
class InfoExtractionDatas:
    independant_infos: List[ExtractionData]
    list_infos: Dict[str, List[ExtractionData]]

    def count_extract_data(self):
        return len(self.independant_infos) + sum(
            len(l) for l in self.list_infos.values()
        )

    def get_names_independant_info(self) -> List[str]:
        return [info.name for info in self.independant_infos]

    def get_names_list_info(self) -> List[Tuple[str, str]]:
        return [
            (first_name, info.name)
            for first_name, list_info in self.list_infos
            for info in list_info
        ]

    def get_names(self) -> List[Union[str, Tuple[str, str]]]:
        return self.get_names_independant_info() + self.get_names_list_info()
