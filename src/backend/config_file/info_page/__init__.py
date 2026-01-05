from enum import Enum

# ------------------------- Constants -------------------------

LIST_SPLITTER = ":"


class Datas(Enum):
    INSTRUCTION = (1, "Instruction")
    NAME = (2, "Nom information")
    DESCRIPTION = (3, "Descriptif de l'information")
    LABEL_SOURCE_NAME = (4, "Nom source")
    VALUE = (5, "Information")
    EXTRACT_EXACTLY_INFO = (6, "Texte exact")

    def __init__(self, col, header_name: str):
        super().__init__()
        self.col = col
        self.header_name = header_name


# str
NAME_WORKSHEET = "Infos à extraire"
TITLE_ERROR = "Config file header info"

# cols and rows
FIRST_ROW_INFO = 3
ROW_HEADER = 2

