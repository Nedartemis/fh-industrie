from typing import Dict, List, Optional, Union

from backend.config_file.info_page import InfoExtractionDatas, InfoValues
from backend.info_struct.extraction_data import ExtractionData
from logger import logger

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
    lieu_expertise : "string" ,
    # short independant info with description
    numero_rg : "string" # description : avec ce format...,
    # list info
    "demandeur" : [{"nom" : "string", "avocat" : "string"}, ...]
}```
"""


def _build_prompt_one_short_info(ed: ExtractionData) -> str:

    prompt_description = f" # description : {ed.desciption}" if ed.desciption else ""
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
        if not info.exact
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


def convert_str_to_optional_node(s: str) -> Optional[str]:
    return None if s == "None" else s


def postprocess_llm_answer_short_list_info(
    extracted_json: Dict[str, Union[str, List[Dict[str, str]]]],
) -> InfoValues:
    """Purposes :
    1. Separate independant and list infos
    2. Check type and filter elements of wrong type
    3. Convert "None" values to None
    4. Combine independant and list infos
    """

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
        name
        for name, value in independant_infos.items()
        if not (isinstance(name, str) and isinstance(value, str))
    ]
    if wrongs:
        logger.error(
            f"The independant info named {wrongs} do(es) not have the good type."
        )
    independant_infos = {
        name: value for name, value in independant_infos.items() if not name in wrongs
    }

    wrongs = [
        first_name
        for first_name, lst in list_infos.items()
        if not (isinstance(first_name, str) and isinstance(lst, list))
        for d in lst
        if not isinstance(d, dict)
        for sub_name, value in d.items()
        if not (isinstance(sub_name, str) and isinstance(value, str))
    ]
    if wrongs:
        logger.error(f"The list info named {wrongs} do(es) not have the good type.")
    list_infos = {
        first_name: lst
        for first_name, lst in list_infos.items()
        if not first_name in wrongs
    }

    # 3. Convert "None" values to None

    # - independant
    independant_infos = {
        name: convert_str_to_optional_node(value)
        for name, value in extracted_json.items()
    }

    # - list
    list_infos = {
        first_name: [
            {
                sub_name: convert_str_to_optional_node(value)
                for sub_name, value in d.items()
            }
            for d in lst
        ]
        for first_name, lst in list_infos.items()
    }

    # 4. Combine independant and list infos
    return InfoValues(indepedant_infos=independant_infos, list_infos=list_infos)


# ------------------------- Exact infos -------------------------

EXACT_INFO_INSTRUCTIONS = """
    Extraire le début et la fin de cette information '{info_name}'{description}."
    Le format doit être le suivant :
    ```json {
        "debut" : "string",
        "fin" : "string"
    }```
"""


def build_prompt_exact_infos(ed: ExtractionData) -> str:

    description = (
        f" ayant cette description : {ed.desciption}" if ed.description else ""
    )

    prompt_system = EXACT_INFO_INSTRUCTIONS.format(
        info_name=ed.name, description=description
    )

    return prompt_system


def _get_index(
    text_where_to_search: str, text_to_get_index: str, label: str
) -> Optional[int]:
    try:
        return text_where_to_search.index(text_to_get_index)
    except ValueError:
        logger.error(f"{label} not in the text.")
        return None


def from_response_llm_exact_info_extract_exact_text(
    text_where_to_search: str,
    extracted_json: dict,
) -> Optional[str]:

    # response consistency
    if not "debut" in extracted_json or not "fin" in extracted_json:
        logger.error(f"'debut' or 'fin' not in the extract_json.")
        return None

    # get the indices of the begin and end
    begin = extracted_json["debut"]
    end = extracted_json["fin"]

    idx_begin = _get_index(text_where_to_search, begin, "Begin")
    idx_end = _get_index(text_where_to_search, end, "End") + len(end)

    # extract
    exact_info_text = text_where_to_search[idx_begin:idx_end]

    return exact_info_text
