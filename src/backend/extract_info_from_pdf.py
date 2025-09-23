import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from backend.claude_client import ClaudeClient
from backend.manage_config_file import InfoToExtractData
from backend.read_pdf import is_scanned, read_all_pdf
from vars import DEFAULT_LOGGER, PATH_CACHE, PATH_ROOT, PATH_TEST, PATH_TMP, TYPE_LOGGER

MAX_TOKENS = 10000
TEMPERATURE = 1

# ------------------- Public Method -------------------


def extract_info_from_pdf(
    claude_client: ClaudeClient,
    path_pdf: Path,
    infos: List[InfoToExtractData],
    log: TYPE_LOGGER = DEFAULT_LOGGER,
) -> dict:

    # get pages
    pages = _get_pdf_pages(path_pdf, log)

    # extract info from the text
    new_infos = _extract_info_from_natural_language(
        claude_client=claude_client,
        infos=infos,
        text="\n\n".join(pages[:]),
        log=log,
    )

    # error detection
    names_infos = [info.name for info in infos if not ":" in info.name]

    # -- found wrong ones
    for name_info in [
        info_name for info_name, e in new_infos.items() if isinstance(e, str)
    ]:
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
    label = os.path.relpath(path=pdf_path.resolve(), start=PATH_ROOT)

    path_cache = PATH_CACHE / (label.replace(os.sep, "|") + ".json")

    if path_cache.exists():
        # read from cache
        with open(str(path_cache), mode="r") as f:
            pages = json.load(f)
        log(f"'{label}' chargé depuis le cache.")
    else:
        # read pdf
        pages = read_all_pdf(pdf_path)
        log(
            f"'{label}' a été lu et est un pdf {'scanné' if is_scanned(pdf_path) else 'natif'}."
        )

        # save into cache
        with open(str(path_cache), mode="w") as f:
            json.dump(pages, f)

    return pages


def _extract_info_from_natural_language(
    claude_client: ClaudeClient,
    infos: List[InfoToExtractData],
    text: str,
    log: TYPE_LOGGER,
) -> Dict[str, Any]:

    if not text:
        return {}

    # little information

    infos_short = [info for info in infos if not info.long]

    # filter independants information
    infos_short_independant = [info for info in infos if not ":" in info.name]

    # filter list information
    info_short_list: Dict[str, List[InfoToExtractData]] = {}
    for info in infos_short:
        if not ":" in info.name:
            continue
        parts = info.name.split(":")
        assert len(parts) == 2
        list_name, info_name = parts
        if not list_name in info_short_list:
            info_short_list[list_name] = []

        new_info = InfoToExtractData(**info.__dict__)
        new_info.name = info_name
        info_short_list[list_name].append(new_info)

    """{
        "demendeurs" : [
            {
                "nom" : "string",
                "avocat" : "string",
                "avocat_lieu" : "string"
            }, ...
        ]
    }"""

    # build prompt
    def prompt_one_info(info: InfoToExtractData) -> str:
        return f'"{info.name}": "string"' + (
            f" # description : {info.desciption}" if info.desciption else ""
        )

    format_infos = (
        "```json\n{\n\t"
        + ",\n\t".join(
            [prompt_one_info(info) for info in infos_short_independant]
            + [
                f'"{list_name}" : [{s}, ...]'
                for list_name, info_list in info_short_list.items()
                if (
                    s := "{"
                    + ", ".join(prompt_one_info(info) for info in info_list)
                    + "}"
                )
            ]
        )
        + "\n}```"
    )
    print(format_infos)

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
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    # extract the infos
    text_infos = response["content"][0]["text"]
    log(f"text_infos : {text_infos}")
    res = re.search(pattern="```json(.*)```", string=text_infos, flags=re.DOTALL)
    extracted_str = res.group(1)
    log(f"extracted_str : {extracted_str}")

    # convert to json
    extracted_json = json.loads(extracted_str)

    # filter those not found
    extracted_json = {
        key: value for key, value in extracted_json.items() if value != "None"
    }

    # long information
    for info in infos:
        if not info.long:
            continue

        description = f" et cette description : {info.desciption}"
        prompt_system = (
            f"Extraire le maximum d'information sans faire de résumé correspondant à ce nom '{info.name}'{description}."
            + " Donne directement les informations extraites, sans amorce ni introduction."
        )

        response = claude_client.create_message(
            system=prompt_system,
            messages=[{"role": "user", "content": text}],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )

        extracted_json[info.name] = response["content"][0]["text"]
        log(f"Long {info.name} : {extracted_json[info.name]}")

    return extracted_json


# ------------------- Main -------------------

if __name__ == "__main__":

    _get_pdf_pages(
        PATH_TEST / "test_reading_pdf" / "native.pdf",
        log=DEFAULT_LOGGER,
    )

    # extract_info_from_pdf(
    #     claude_client=ClaudeClient(),
    #     path_pdf=PATH_TEST
    #     / "0- ARBORESCENCE DOSSIERS JUD/EXPERT/01 - Notes aux parties/Note n°1 - Visio Adm/TJ DIEPPE - MASSERE - Ordonnance du 05 06 2024.pdf",
    #     names_infos=["lieu_expertise", "numero_rg", "date_reunion", "date_ordonnance"],
    # )
