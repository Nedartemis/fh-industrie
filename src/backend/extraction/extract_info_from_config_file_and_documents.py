import os
from pathlib import Path
from typing import Dict, Optional

from backend.config_file.config_file import fill_config_file, read_config_file
from backend.extraction.extract_from_txt import extract_from_txt
from backend.extraction.extract_info_from_pdf import extract_info_from_pdf
from backend.info_struct import InfoExtractionDatas, InfoValues
from backend.llm.claude_client import ClaudeClient
from backend.llm.llm_test import LlmTest
from logger import logger
from logs_label import (
    ExtensionFileNotSupported,
    ExtractionAddWrongInfo,
    ExtractionLackCompletlyInfo,
    ExtractionNotFoundInfo,
    PathNotExisting,
)
from vars import TEST_WITHOUT_INTERNET

# ------------------- Public method -------------------


def extract_infos_from_config_file_and_files_tree(
    path_config_file: Path,
    path_folder_sources: Path,
    path_folder_output: Optional[Path] = None,
) -> Path:

    if not path_config_file.exists():
        raise PathNotExisting(path=path_config_file)

    if not path_folder_sources.exists():
        raise PathNotExisting(path=path_folder_sources)

    if path_folder_output is not None and not path_folder_output.exists():
        raise PathNotExisting(path=path_folder_output)

    logger.info(f"Path folder sources : {path_folder_sources}")
    logger.info(f"List dir : {os.listdir(path_folder_sources)}")

    # read config file
    logger.info("Reading config file...")
    sources, extraction_datas = read_config_file(path_config_file, path_folder_sources)

    # extract info with llm
    logger.info("Extracting infos...")

    logger.info(
        f"{len(sources)} files are going to be analysed.\n"
        + f"{sum(e.count_extract_data() for e in extraction_datas.values())} information must be extracted.",
    )

    all_infos_found: InfoValues = InfoValues(independant_infos={}, list_infos={})
    llm = LlmTest() if TEST_WITHOUT_INTERNET else ClaudeClient()

    for source_name, infos in extraction_datas.items():

        path = (path_folder_sources / sources[source_name]).resolve()

        # pdf
        if path.suffix == ".pdf":
            new_infos_found = extract_info_from_pdf(
                llm,
                path_pdf=path,
                info_to_extract=infos,
            )
        elif path.suffix == ".txt":
            new_infos_found = extract_from_txt(
                llm=llm, path_txt=path, info_to_extract=infos
            )
        else:
            logger.error(
                f"Not support extension '{path.suffix}' of file : {path}",
                extra=ExtensionFileNotSupported(),
            )
            continue

        # checks and filter
        new_infos_filtered = _check_and_filter_result_extraction(
            info_to_extract=infos, info_values=new_infos_found
        )

        # save new infos by merging
        all_infos_found.update(new_infos_filtered)

    logger.info(
        f"{all_infos_found.count_values()} information have been extracted with success."
    )

    # copy and fill config file
    if path_folder_output is None:
        path_folder_output = path_folder_sources

    info_path_file = path_folder_output / f"{path_config_file.stem}_rempli.xlsx"
    fill_config_file(
        path_config_file, infos=all_infos_found, path_output=info_path_file
    )

    return info_path_file


# ------------------- Private method -------------------


def _check_and_filter_result_extraction(
    info_to_extract: InfoExtractionDatas, info_values: InfoValues
) -> InfoValues:
    # error detection and filter
    names_to_extract = info_to_extract.get_names()
    names_all_extracted = info_values.get_names(keep_none_values=True)

    # - found wrong names and filter
    wrong_names = [name for name in names_all_extracted if name not in names_to_extract]
    if wrong_names:
        logger.warning(
            f"{wrong_names} were extracted but were not asked.",
            extra=ExtractionAddWrongInfo(info_names=wrong_names),
        )
        info_values.filter_names(names_to_remove=wrong_names)

    # - those not in the extraction result at all
    missing_names = [
        name for name in names_to_extract if name not in names_all_extracted
    ]
    if missing_names:
        logger.warning(
            f"{missing_names} were completly missing from the extraction.",
            extra=ExtractionLackCompletlyInfo(info_names=wrong_names),
        )

    # - those in the extraction result but without values
    names_extracted_none = info_values.get_name_nones()
    if names_extracted_none:
        logger.warning(
            f"{names_extracted_none} were not extracted. They got a 'None' value.",
            extra=ExtractionNotFoundInfo(info_names=names_extracted_none),
        )

    return info_values


# ------------------- Main -------------------


if __name__ == "__main__":
    from vars import PATH_TEST_DOCS

    path_test = PATH_TEST_DOCS / "simple_extraction"
    extract_infos_from_config_file_and_files_tree(
        path_test / "fichier_configuration.xlsx",
        path_folder_sources=path_test,
    )
