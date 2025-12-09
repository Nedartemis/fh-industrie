import os
from pathlib import Path
from typing import Dict

import backend.extraction.cache as cache
from backend.extraction.extract_info_from_natural_language import (
    extract_info_from_natural_language,
)
from backend.info_struct.info_extraction_datas import InfoExtractionDatas
from backend.info_struct.info_values import InfoValues
from backend.llm.llm_base import LlmBase
from backend.read_pdf.read_pdf import is_scanned, read_all_pdf
from logger import logger
from vars import DEFAULT_LOGGER, PATH_ROOT, PATH_TEST_DOCS

# ------------------- Public Method -------------------


def extract_info_from_pdf(
    llm: LlmBase,
    path_pdf: Path,
    info_to_extract: InfoExtractionDatas,
) -> InfoValues:

    # get pages
    pages = _get_pdf_pages(path_pdf)

    # extract info from the text
    info_values = extract_info_from_natural_language(
        llm=llm,
        info_to_extract=info_to_extract,
        text="\n\n".join(pages[:]),
    )

    # error detection and filter
    names_to_extract = info_to_extract.get_names()
    names_all_extracted = info_values.get_names(keep_none_values=True)

    # - found wrong names and filter
    wrong_names = [name for name in names_all_extracted if name not in names_to_extract]
    if wrong_names:
        logger.warning(f"{wrong_names} were extracted but were not asked.")
        info_values.filter_names(names_to_remove=wrong_names)

    # - those not in the extraction result at all
    missing_names = [
        name for name in names_to_extract if name not in names_all_extracted
    ]
    if missing_names:
        logger.warning(f"{missing_names} were completly missing from the extraction.")

    # - those in the extraction result but without values
    names_extracted_none = info_values.get_name_nones()
    if names_extracted_none:
        logger.warning(
            f"{names_extracted_none} were not extracted. They got a 'None' value."
        )

    # return
    return info_values


# ------------------- Private Method -------------------


def _get_pdf_pages(pdf_path: Path):
    rel_path_from_root = os.path.relpath(path=pdf_path.resolve(), start=PATH_ROOT)

    pages = cache.load(rel_path_from_root)

    if not pages:
        # read pdf
        pages = read_all_pdf(pdf_path)
        logger.info(
            f"'{rel_path_from_root}' a été lu et est un pdf {'scanné' if is_scanned(pdf_path) else 'natif'}."
        )

        cache.save(rel_path_from_root, pages)

    return pages


# ------------------- Main -------------------

if __name__ == "__main__":

    _get_pdf_pages(
        PATH_TEST_DOCS / "test_reading_pdf" / "native.pdf",
        log=DEFAULT_LOGGER,
    )

    # extract_info_from_pdf(
    #     claude_client=ClaudeClient(),
    #     path_pdf=PATH_TEST
    #     / "0- ARBORESCENCE DOSSIERS JUD/EXPERT/01 - Notes aux parties/Note n°1 - Visio Adm/TJ DIEPPE - MASSERE - Ordonnance du 05 06 2024.pdf",
    #     names_infos=["lieu_expertise", "numero_rg", "date_reunion", "date_ordonnance"],
    # )
