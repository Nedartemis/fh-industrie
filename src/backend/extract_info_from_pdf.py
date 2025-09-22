import json
import os
import re
from pathlib import Path
from typing import Dict, List

from backend.claude_client import ClaudeClient
from backend.read_pdf import is_scanned, read_all_pdf
from vars import DEFAULT_LOGGER, PATH_CACHE, PATH_TEST, PATH_TMP, TYPE_LOGGER

# ------------------- Public Method -------------------


def extract_info_from_pdf(
    claude_client: ClaudeClient,
    path_pdf: Path,
    names_infos: List[str],
    log: TYPE_LOGGER = DEFAULT_LOGGER,
) -> dict:

    # get pages
    pages = _get_pdf_pages(path_pdf, log)

    # extract info from the text
    new_infos = _extract_info_from_natural_language(
        claude_client=claude_client,
        names_infos=names_infos,
        text="\n\n".join(pages[:]),
        log=log,
    )

    # error detection

    # -- found wrong ones
    for name_info in new_infos:
        if name_info not in names_infos:
            log(f"'{name_info}' a été extrait mais n'avait pas été demandé.")

    # -- those not found
    for name_info in names_infos:
        if name_info not in new_infos.keys():
            log(f"'{name_info}' n'a pas été extrait.")

    # return
    return new_infos


# ------------------- Private Method -------------------


def _get_pdf_pages(pdf_path: Path, log: TYPE_LOGGER):
    label = pdf_path.stem
    path_cache = PATH_CACHE / (label + ".json")

    if path_cache.exists():
        # read from cache
        with open(str(path_cache), mode="r") as f:
            pages = json.load(f)
        log(f"'{pdf_path.name}' chargé depuis le cache.")
    else:
        # read pdf
        pages = read_all_pdf(pdf_path)
        log(
            f"'{pdf_path.name}' a été lu et est un pdf {'scanné' if is_scanned(pdf_path) else 'natif'}."
        )

        # save into cache
        with open(str(path_cache), mode="w") as f:
            json.dump(pages, f)

    return pages


def _extract_info_from_natural_language(
    claude_client: ClaudeClient, names_infos: List[str], text: str, log: TYPE_LOGGER
) -> Dict[str, str]:

    if not text:
        return {}

    # build prompt
    format_infos = (
        "```json\n{ \n"
        + "\n\t".join([f'"{info_name}": "..."' for info_name in names_infos])
        + "\n}```"
    )
    prompt_system = f"""
        Extrait toutes les informations que tu trouves sous format json :
        {format_infos}

        Si tu ne trouves pas l'info, remplie le champs par "None".
    """

    messages = [{"role": "user", "content": text}]

    # call LLM
    response = claude_client.create_message(
        system=prompt_system,
        messages=messages,
        max_tokens=1000,
        temperature=1,
    )

    # extract the infos
    text_infos = response["content"][0]["text"]
    # log(f"text_infos : {text_infos}")
    res = re.search(pattern="```json(.*)```", string=text_infos, flags=re.DOTALL)
    extracted_str = res.group(1)
    log(f"extracted_str : {extracted_str}")

    # convert to json
    extracted_json = json.loads(extracted_str)

    # filter those not found
    extracted_json = {
        key: value for key, value in extracted_json.items() if value != "None"
    }

    return extracted_json


# ------------------- Main -------------------

if __name__ == "__main__":
    extract_info_from_pdf(
        claude_client=ClaudeClient(),
        path_pdf=PATH_TEST
        / "0- ARBORESCENCE DOSSIERS JUD/EXPERT/01 - Notes aux parties/Note n°1 - Visio Adm/TJ DIEPPE - MASSERE - Ordonnance du 05 06 2024.pdf",
        names_infos=["lieu_expertise", "numero_rg", "date_reunion", "date_ordonnance"],
    )
