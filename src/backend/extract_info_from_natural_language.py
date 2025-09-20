import json
import re
from typing import Dict, List

from backend.claude_client import ClaudeClient


def extract_info_from_natural_language(
    claude_client: ClaudeClient, names_infos: List[str], text: str
) -> Dict[str, str]:

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
    print(f"text_infos : {text_infos}")
    res = re.search(pattern="```json(.*)```", string=text_infos, flags=re.DOTALL)
    extracted_str = res.group(1)
    print(f"extracted_str : {extracted_str}")

    # filter those not found
    extracted_infos = {
        key: value
        for key, value in json.loads(extracted_str).items()
        if value != "None"
    }

    return extracted_infos
