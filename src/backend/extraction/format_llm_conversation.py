from typing import Dict, List, Optional, Union

from rapidfuzz import fuzz, process

from backend.info_struct import InfoExtractionDatas, InfoValues
from backend.info_struct.extraction_data import ExtractionData
from logger import logger
from logs_label import LlmWrongFormat

# ------------------------- Helper -------------------------


def _wrapped_prompt_with_json_header(elements: List[str]) -> str:
    return "```json\n{\n\t" + ",\n\t".join(elements) + "\n}```"


# ------------------------- Short and list infos  -------------------------


SHORT_LIST_INFO_INSTRUCTIONS = """
    Extrait toutes les informations que tu trouves sous format json :
    {prompt_infos}

    Si tu ne trouves pas l'info, remplie le champs par "None".
"""


"""example prompt_infos
```json
{
    # short independant info
    "lieu_expertise" : "string",
    # short independant info with description
    "numero_rg" : "string" # description : avec ce format,
    # list info
    "demandeur" : [{"nom" : "string", "avocat" : "string"}, ...]
}```
"""


def _build_prompt_one_short_info(ed: ExtractionData) -> str:

    prompt_description = f" # description : {ed.description}" if ed.description else ""
    return f'"{ed.name}": "string"' + (prompt_description)


def _build_prompt_one_list_info(
    first_name: str, info_list: List[ExtractionData]
) -> List[str]:

    sub_dict_str = (
        "{" + ", ".join(_build_prompt_one_short_info(info) for info in info_list) + "}"
    )
    return f'"{first_name}" : [{sub_dict_str}, ...]'


def build_prompt_short_and_list_infos(infos: InfoExtractionDatas) -> Optional[str]:

    # short (not exact) and independant info
    prompts_short_independant_infos: List[str] = [
        _build_prompt_one_short_info(info)
        for info in infos.independant_infos
        if not info.extract_exactly_info
    ]

    # list infos (always not exact)
    prompts_list_infos: List[str] = [
        _build_prompt_one_list_info(first_name, info_list)
        for first_name, info_list in infos.list_infos.items()
    ]

    # combine
    combined_infos = prompts_short_independant_infos + prompts_list_infos
    if len(combined_infos) == 0:
        return None

    # add the json wrapper
    prompt_infos = _wrapped_prompt_with_json_header(combined_infos)
    logger.info(prompt_infos)

    # add the instructions
    return SHORT_LIST_INFO_INSTRUCTIONS.format(prompt_infos=prompt_infos)


def _convert_str_to_optional_str(s: str) -> Optional[str]:
    return None if s.lower() == "none" else s


def postprocess_llm_answer_short_list_info(
    extracted_json: Dict[str, Union[str, List[Dict[str, str]]]],
) -> InfoValues:
    """Purposes :
    0. Check its a dict with str as keys
    1. Separate independant and list infos
    2. Check type and filter elements of wrong type
    3. Convert "None" values to None
    4. Combine independant and list infos
    """

    # 0.

    # dict
    if not isinstance(extracted_json, dict):
        logger.error(
            f"The answer of short and list is not a dict : {extracted_json}",
            extra=LlmWrongFormat(extracted_json=extracted_json),
        )
        return InfoValues(independant_infos={}, list_infos={})

    # str keys
    wrongs = [k for k in extracted_json.keys() if not isinstance(k, str)]
    if wrongs:
        logger.error(
            f"Some keys of the answer of short and list are not str, they are: {set(type(k) for k in wrongs)}",
            extra=LlmWrongFormat(extracted_json=extracted_json),
        )
    extracted_json = {k: v for k, v in extracted_json.items() if k not in wrongs}

    # values
    wrongs = [
        v
        for v in extracted_json.values()
        if not isinstance(v, str) and not isinstance(v, list)
    ]
    if wrongs:
        logger.error(
            f"Some values of the answer of short and list are not str nor list, they are: {set(type(k) for k in wrongs)}",
            extra=LlmWrongFormat(extracted_json=extracted_json),
        )
    extracted_json = {k: v for k, v in extracted_json.items() if v not in wrongs}

    # 1. Separate independant and list infos
    independant_infos: Dict[str, str] = {
        name: value for name, value in extracted_json.items() if isinstance(value, str)
    }
    list_infos: Dict[str, List[Dict[str, str]]] = {
        first_name: lst
        for first_name, lst in extracted_json.items()
        if isinstance(lst, list)
    }

    # 2. Check type and filter elements of wrong type
    wrongs = [
        first_name
        for first_name, lst in list_infos.items()
        for d in lst
        if not isinstance(d, dict)
    ] + [
        first_name
        for first_name, lst in list_infos.items()
        for d in lst
        if isinstance(d, dict)
        for sub_name, value in d.items()
        if not isinstance(sub_name, str) or not isinstance(value, str)
    ]
    if wrongs:
        logger.error(
            f"The list info named {wrongs} do(es) not have the good type.",
            extra=LlmWrongFormat(list_infos),
        )
    list_infos = {
        first_name: lst
        for first_name, lst in list_infos.items()
        if not first_name in wrongs
    }

    # 3. Convert "None" values to None

    # - independant
    independant_infos = {
        name: _convert_str_to_optional_str(value)
        for name, value in independant_infos.items()
    }

    # - list
    list_infos = {
        first_name: [
            {
                sub_name: _convert_str_to_optional_str(value)
                for sub_name, value in d.items()
            }
            for d in lst
        ]
        for first_name, lst in list_infos.items()
    }
    logger.info(independant_infos)
    logger.info(list_infos)

    # 4. Combine independant and list infos
    return InfoValues(independant_infos=independant_infos, list_infos=list_infos)


# ------------------------- Exact infos -------------------------

EXACT_INFO_INSTRUCTIONS_TITLE = """
    Extraire le début et la fin de cette information '{info_name}'{description}."
"""

EXACT_INFO_INSTRUCTIONS_FORMAT = """
    Le format doit être le suivant :
    ```json
    {
        "debut" : "string",
        "fin" : "string"
    }```
"""


def build_prompt_exact_infos(ed: ExtractionData) -> str:

    description = (
        f" ayant cette description : {ed.description}" if ed.description else ""
    )

    prompt_system_title = EXACT_INFO_INSTRUCTIONS_TITLE.format(
        info_name=ed.name, description=description
    )

    return prompt_system_title + EXACT_INFO_INSTRUCTIONS_FORMAT


def from_response_llm_exact_info_extract_exact_text(
    text_where_to_search: str,
    extracted_json: Dict[str, str],
) -> Optional[str]:

    # response consistency
    if not isinstance(extracted_json, dict):
        logger.error(
            f"Answer of exact query is not a dict.",
            extra=LlmWrongFormat(extracted_json),
        )
        return None

    if not "debut" in extracted_json or not "fin" in extracted_json:
        logger.error(
            f"'debut' or 'fin' not in the extract_json.",
            extra=LlmWrongFormat(extracted_json),
        )
        return None

    if not isinstance(extracted_json["debut"], str) or not isinstance(
        extracted_json["fin"], str
    ):
        logger.error(
            f"'debut' or 'fin' value is not str.", extra=LlmWrongFormat(extracted_json)
        )
        return None

    # get the indices of the begin and end
    begin = extracted_json["debut"]
    end = extracted_json["fin"]

    idx_begin = find_index(text_where_to_search, pattern=begin)
    idx_end = find_index(text_where_to_search, pattern=end)

    if idx_begin is None or idx_end is None:
        logger.error(
            f"'debut' or 'fin' value not in the original text.",
            extra=LlmWrongFormat(extracted_json),
        )
        return None

    # extract
    exact_info_text = text_where_to_search[idx_begin : idx_end + len(end)]

    return exact_info_text


def find_index(text: str, pattern: str) -> Optional[int]:
    matches = process.extract(
        pattern,
        [text[i : i + len(pattern)] for i in range(len(text) - len(pattern) + 1)],
        scorer=fuzz.ratio,
        score_cutoff=80,
    )
    if len(matches) == 0:
        return None

    best_match = max(matches, key=lambda x: x[1])
    idx = best_match[2]
    return idx
