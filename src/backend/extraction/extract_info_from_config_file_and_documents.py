import os
from pathlib import Path
from typing import Dict

from backend.config_file.config_file import fill_config_file, read_config_file
from backend.extraction.extract_info_from_pdf import extract_info_from_pdf
from backend.info_struct.info_values import InfoValues
from backend.llm.claude_client import ClaudeClient
from backend.llm.llm_test import LlmTest
from logger import logger
from vars import TEST_WITHOUT_INTERNET


def extract_infos_from_config_file_and_files_tree(
    path_config_file: Path, path_folder_sources: Path
) -> Path:

    if not path_config_file.exists():
        raise RuntimeError(f"Configuration file '{path_config_file}' does not exist")

    logger.info("Path folder sources :", path_folder_sources)
    logger.info("List dir")
    logger.info(os.listdir(path_folder_sources))

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

        new_infos_found = extract_info_from_pdf(
            llm,
            path_pdf=(path_folder_sources / sources[source_name]).resolve(),
            infos=infos,
            log=logger.info,
        )

        # save new infos by merging
        all_infos_found.update(new_infos_found)

    logger.info(
        f"{all_infos_found.count_values()} information have been extracted with success."
    )

    # copy and fill config file
    info_path_file = path_folder_sources / f"{path_config_file.stem}_rempli.xlsx"
    fill_config_file(
        path_config_file, infos=all_infos_found, path_output=info_path_file
    )

    return info_path_file


if __name__ == "__main__":
    from vars import PATH_TEST_DOCS

    path_test = PATH_TEST_DOCS / "simple_extraction"
    extract_infos_from_config_file_and_files_tree(
        path_test / "fichier_configuration.xlsx",
        path_folder_sources=path_test,
    )
