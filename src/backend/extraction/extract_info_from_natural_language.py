import json
import re
from typing import Dict, Optional

from backend.extraction.format_llm_conversation import (
    build_prompt_exact_infos,
    build_prompt_short_and_list_infos,
    from_response_llm_exact_info_extract_exact_text,
    postprocess_llm_answer_short_list_info,
)
from backend.info_struct.info_extraction_datas import InfoExtractionDatas
from backend.info_struct.info_values import InfoValues
from backend.llm.llm_base import LlmBase
from logger import logger
from logs_label import LlmFailedAnswer

# ------------------- Constants -------------------

MAX_TOKENS = 10000
TEMPERATURE = 0
TOP_P = 1

# ------------------- Public Method -------------------


def extract_info_from_natural_language(
    llm: LlmBase,
    info_to_extract: InfoExtractionDatas,
    text: str,
) -> InfoValues:

    if text == "":
        logger.info("Text empty : no extraction")
        return InfoValues(independant_infos={}, list_infos={})

    # short list info

    # - build prompt
    prompt_short_list_info = build_prompt_short_and_list_infos(info_to_extract)

    # - call llm if needed
    extracted_json_short_list = (
        _call_llm(
            llm=llm, prompt_system=prompt_short_list_info, text_where_to_extract=text
        )
        if prompt_short_list_info
        else {}
    )
    if extracted_json_short_list is not None:
        # postprocess
        info_values = postprocess_llm_answer_short_list_info(extracted_json_short_list)
        logger.info(info_values)
    else:
        logger.error(
            "Failed to extract short and list info.",
            extra=LlmFailedAnswer(info_to_extract=info_to_extract, text=text),
        )
        info_values = InfoValues(independant_infos={}, list_infos={})

    # exact info
    extracted_exact_infos: Dict[str, str] = {}
    for info in info_to_extract.independant_infos:
        # - filter
        if not info.extract_exactly_info:
            continue

        # - build prompt
        prompt_system = build_prompt_exact_infos(info)

        # - call llm
        extracted_json_exact = _call_llm(
            llm=llm, prompt_system=prompt_system, text_where_to_extract=text
        )
        if not extracted_json_exact:
            logger.error(
                f"Failed to extract exact info '{info.name}'",
                extra=LlmFailedAnswer(info_to_extract=info_to_extract, text=text),
            )
            continue

        logger.info(f"Exact info extracted json : {extracted_json_exact}")

        # - convert answer
        exact_info_text = from_response_llm_exact_info_extract_exact_text(
            text_where_to_search=text, extracted_json=extracted_json_exact
        )
        if not exact_info_text:
            logger.error(f"Failed to extract exact info '{info.name}'")
            continue

        extracted_exact_infos[info.name] = exact_info_text

    # combine
    info_values.independant_infos.update(extracted_exact_infos)

    return info_values


# ------------------- Private Method -------------------


def _response_to_json(text_response: str) -> Optional[dict]:

    logger.info(f"text_response : {text_response}")
    res = re.search(pattern="```json(.*)```", string=text_response, flags=re.DOTALL)
    if not res:
        res = re.search(pattern="({.*})```", string=text_response, flags=re.DOTALL)

    extracted_str = res.group(1)
    logger.info(f"extracted_str : {extracted_str}")

    # convert to json, raises JSONDecodeError
    try:
        obj = json.loads(extracted_str)
    except json.JSONDecodeError:
        return None

    if not isinstance(obj, dict):
        return None

    return obj


def _call_llm(
    llm: LlmBase, prompt_system: str, text_where_to_extract: str
) -> Optional[dict]:

    messages = llm.build_messages(msg=text_where_to_extract)

    text_response = llm.create_message(
        system=prompt_system,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )

    return _response_to_json(text_response)
