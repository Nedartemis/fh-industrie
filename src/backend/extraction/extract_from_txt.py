from pathlib import Path

from backend.extraction.extract_info_from_natural_language import (
    extract_info_from_natural_language,
)
from backend.info_struct import InfoExtractionDatas, InfoValues
from backend.llm.llm_base import LlmBase
from logger import logger
from logs_label import ExtensionFileNotSupported, FileDataError, PathNotExisting


def extract_from_txt(
    llm: LlmBase,
    path_txt: Path,
    info_to_extract: InfoExtractionDatas,
) -> InfoValues:

    # checks

    # - ext
    if path_txt.suffix != ".txt":
        raise ExtensionFileNotSupported(path=path_txt)

    # - path not existing
    if not path_txt.exists():
        log_label = PathNotExisting(path=path_txt)
        logger.error(log_label.msg(), extra=log_label)
        return InfoValues.empty()

    # read txt
    try:
        with open(path_txt, "r") as file_reader:
            text = file_reader.read()
    except Exception:
        log_label = FileDataError(path=path_txt)
        logger.error(log_label.msg(), extra=log_label)
        return InfoValues.empty()

    # extract
    info_values = extract_info_from_natural_language(
        llm=llm, info_to_extract=info_to_extract, text=text
    )

    return info_values
