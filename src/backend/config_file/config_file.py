from pathlib import Path
from typing import Dict, Tuple

import backend.config_file.info_page.read as info_page
from backend.config_file.info_page import NAME_WORKSHEET as NAME_WORKSHEET_INFO
from backend.config_file.info_page.read import read_info_page_and_preprocess
from backend.config_file.info_page.write import write_values
from backend.config_file.source_page import NAME_WORKSHEET as NAME_WORKSHEET_SOURCE
from backend.config_file.source_page import TYPE_SOURCES, read_source_page
from backend.excel.excel_book import ExcelBook
from backend.info_struct.info_extraction_datas import InfoExtractionDatas
from backend.info_struct.info_values import InfoValues
from logger import f, logger
from logs_label import (
    EmptyInfoExcel,
    ExtensionFileNotSupported,
    PathNotExisting,
    SourceNotGiven,
    SourceNotUseful,
)
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
    eds = read_info_page_and_preprocess(em)

    # error detection and filter
    sources, eds = _error_detection_config_file_extraction_and_filter(
        em.get_excel_name(), sources, eds, path_folder_sources
    )

    log_sources(sources)
    log_infos(infos=eds)

    return sources, eds


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
    excel_name: str,
    sources: TYPE_SOURCES,
    extraction_datas: Dict[str, InfoExtractionDatas],
    path_folder_sources: Path,
) -> Tuple[TYPE_SOURCES, Dict[str, InfoExtractionDatas]]:

    # check and filter sources
    sources_filtered = {}
    for name_source, path_str in sources.items():
        path = Path(path_str)
        if path.suffix[1:] not in SUPPORTED_FILES_EXT_EXTRACTION:
            # extensions
            logger.error(
                f"The extraction does not support files of extension '{path.suffix[1:]}' '{f(filename=path.name)}'.\n"
                + f"Supported extensions are {', '.join(SUPPORTED_FILES_EXT_EXTRACTION)}",
                extra=ExtensionFileNotSupported(path=path),
            )
        elif not (path_folder_sources / path).resolve().exists():
            # file not exising
            logger.error(
                f"The file '{path_str}' does not exist. {f(fullpath=path_folder_sources / path)}",
                extra=PathNotExisting(path=path_str),
            )
        elif not name_source in extraction_datas.keys():
            # source not used
            logger.warning(
                f"There is no information to extract from '{name_source}'.",
                extra=SourceNotUseful(source=name_source),
            )
        else:
            sources_filtered[name_source] = path_str

    # check and filter extraction datas
    extraction_datas_filtered = {}
    for name_source, infos in extraction_datas.items():
        if name_source not in sources:
            logger.error(
                f"The label '{name_source}' is not present in the sources worksheet of the config file.",
                extra=SourceNotGiven(name_source=name_source),
            )
            continue
        extraction_datas_filtered[name_source] = infos

    # remove the extraction datas that are not in the sources_filtered
    extraction_datas_filtered = {
        name_source: infos
        for name_source, infos in extraction_datas_filtered.items()
        if name_source in sources_filtered
    }

    # emptiness
    if not sources_filtered:
        logger.error(
            "Information from sources are empty after all the other checks.",
            extra=EmptyInfoExcel(
                excel_name=excel_name, page_name=NAME_WORKSHEET_SOURCE
            ),
        )

    if not extraction_datas_filtered:
        logger.error(
            "Information from information page are empty after all the other checks.",
            extra=EmptyInfoExcel(excel_name=excel_name, page_name=NAME_WORKSHEET_INFO),
        )

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
