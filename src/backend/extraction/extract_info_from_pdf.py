import os
from pathlib import Path
from typing import Dict, List, Optional

import backend.extraction.cache as cache
from backend.extraction.extract_info_from_natural_language import (
    extract_info_from_natural_language,
)
from backend.info_struct import InfoExtractionDatas, InfoValues
from backend.llm.llm_base import LlmBase
from backend.read_pdf.read_pdf import is_scanned, read_all_pdf
from logger import logger
from logs_label import ExtensionFileNotSupported, FileDataError, PathNotExisting
from vars import DEFAULT_LOGGER, PATH_ROOT, PATH_TEST_DOCS

# ------------------- Public Method -------------------


def extract_info_from_pdf(
    llm: LlmBase,
    path_pdf: Path,
    info_to_extract: InfoExtractionDatas,
) -> InfoValues:

    if path_pdf.suffix != ".pdf":
        raise ExtensionFileNotSupported(path=path_pdf)

    # get pages
    pages = _get_pdf_pages(path_pdf)

    if pages is None:
        return InfoValues.empty()

    # extract info from the text
    info_values = extract_info_from_natural_language(
        llm=llm,
        info_to_extract=info_to_extract,
        text="\n\n".join(pages[:]),
    )

    # return
    return info_values


# ------------------- Private Method -------------------


def _get_pdf_pages(pdf_path: Path) -> Optional[List[str]]:

    rel_path_from_root = os.path.relpath(path=pdf_path.resolve(), start=PATH_ROOT)

    if not pdf_path.exists():
        logger.error(
            f"pdf path not existing, relative path from root : {rel_path_from_root}",
            extra=PathNotExisting(path=pdf_path),
        )
        return None

    pages = cache.load(rel_path_from_root)

    if not pages:
        # read pdf
        try:
            pages = read_all_pdf(pdf_path)
        except FileDataError:
            logger.error(
                f"pdf data error, relative path from root : {rel_path_from_root}",
                extra=FileDataError(pdf_path),
            )
            return None

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
