from pathlib import Path
from typing import Dict, Tuple

import backend.config_file.info_page.read as info_page
from backend.config_file.info_page.read import read_info_page_and_preprocess
from backend.config_file.info_page.write import write_values
from backend.config_file.source_page import TYPE_SOURCES, read_source_page
from backend.excel.excel_book import ExcelBook
from backend.info_struct.info_extraction_datas import InfoExtractionDatas
from backend.info_struct.info_values import InfoValues
from logger import f, logger
from vars import SUPPORTED_FILES_EXT_EXTRACTION

# ------------------- Public Method -------------------


# > read


def read_config_file(
    path_config_file: Path, path_folder_sources: Path
) -> Tuple[TYPE_SOURCES, Dict[str, InfoExtractionDatas]]:

    # open the excel
    em = ExcelBook(path_config_file)

    # read the source page : read the label and the path of each file
    sources = read_source_page(em)

    # read the info page
    extraction_datas = read_info_page_and_preprocess(em)

    # error detection and filter
    files_path, files_infos = _error_detection_config_file_extraction_and_filter(
        sources, extraction_datas, path_folder_sources
    )

    log_sources(sources)
    log_infos(infos=extraction_datas)

    return files_path, files_infos


def read_info_values(path_config_file: Path) -> InfoValues:

    # open the excel
    em = ExcelBook(path_config_file)

    # read
    return info_page.read_info_values(em)


# > write


def fill_config_file(
    path_config_file: Path, infos: InfoValues, path_output: Path
) -> None:

    # open
    eb = ExcelBook(path_config_file)

    # write
    write_values(eb, infos)

    # save
    eb.save(path_output)
    eb.wb.close()


# print
def log_sources(sources: TYPE_SOURCES):

    logger.info(
        "Sources : " + str({label: str(path) for label, path in sources.items()})
    )


def log_infos(infos: Dict[str, InfoExtractionDatas]):
    logger.info(
        "Independant infos : "
        + str({key: ied.get_names_independant_info() for key, ied in infos.items()})
    )
    logger.info(
        "List infos : "
        + str({key: ied.get_names_list_info() for key, ied in infos.items()})
    )


# ------------------- Private Method -------------------


def _error_detection_config_file_extraction_and_filter(
    sources: TYPE_SOURCES,
    extraction_datas: Dict[str, InfoExtractionDatas],
    path_folder_sources: Path,
) -> Tuple[TYPE_SOURCES, Dict[str, InfoExtractionDatas]]:

    # check and filter sources
    sources_filtered = {}
    for name_source, path in sources.items():
        if path.suffix[1:] not in SUPPORTED_FILES_EXT_EXTRACTION:
            logger.error(
                f"The extraction does not support files of extension '{path.suffix[1:]}' '{f(filename=path.name)}'.\n"
                + f"Supported extensions are {', '.join(SUPPORTED_FILES_EXT_EXTRACTION)}",
            )
        elif not (path_folder_sources / path).resolve().exists():
            logger.error(
                f"The file '{path}' does not exist. {f(fullpath=path_folder_sources / path)}",
            )
        elif not name_source in extraction_datas.keys():
            logger.warning(
                f"There is no information to extract from '{name_source}'.",
            )
        else:
            sources_filtered[name_source] = path

    # check and filter extraction datas

    extraction_datas_filtered = {}
    for name_source, infos in extraction_datas.items():
        if name_source not in sources:
            logger.error(
                f"The label '{name_source}' is not present in the sources worksheet of the config file.",
            )
            continue
        extraction_datas_filtered[name_source] = infos

    return sources_filtered, extraction_datas_filtered


# ------------------- Main -------------------

if __name__ == "__main__":
    from vars import PATH_TEST_DOCS

    path = PATH_TEST_DOCS / "simple_extraction"
    if True:
        # test simple
        sources, infos = read_config_file(
            path_config_file=path / "fichier_configuration.xlsx",
            path_folder_sources=path,
        )

    else:
        # test list
        infos = {
            "demandeur": [
                {
                    "nom": "M. Claude MASSERE",
                    "avocat": "SCP MORIVAL AMISSE MABIRE",
                    "avocat_lieu": "Barreau de DIEPPE",
                },
                {
                    "nom": "Mme Françoise, Brigitte, Jeanne, Julia LAMAILLE épouse MASSERE",
                    "avocat": "SCP MORIVAL AMISSE MABIRE",
                    "avocat_lieu": "Barreau de DIEPPE",
                },
            ],
            "defendeur": [
                {
                    "nom": "La S.A.R.L. BRUGOT XAVIER",
                    "avocat": "SCP LENGLET, MALBESIN & Associés",
                    "avocat_lieu": "Barreau de ROUEN",
                },
                {
                    "nom": "La S.A. AXA France IARD",
                    "avocat": "SCP LENGLET, MALBESIN & Associés",
                    "avocat_lieu": "Barreau de ROUEN",
                },
                {
                    "nom": "M. Olivier BOUDET",
                    "avocat": "SELARL PATRICE LEMIEGRE PHILIPPE FOURDRIN SUNA GUNEY & Associés",
                    "avocat_lieu": "Barreau de ROUEN",
                },
                {
                    "nom": "La Société MUTUELLE DES ARCHITECTES FRANCAIS",
                    "avocat": "None",
                    "avocat_lieu": "None",
                },
            ],
        }

        fill_config_file(
            path_config_file=path / "fichier_configuration.xlsx",
            infos=infos,
            path_output=path / "fichier_configuration_rempli.xlsx",
        )
