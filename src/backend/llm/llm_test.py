import json
import re
from typing import Any, Dict, List, Optional

from backend.llm.llm_base import TYPE_MESSAGES, LlmBase


def _extract_json(s: str) -> dict:
    res = re.search(pattern="```json(.*)```", string=s, flags=re.DOTALL)
    extracted_str = res.group(1)
    print(extracted_str)
    return json.loads(extracted_str)


class LlmTest(LlmBase):

    def __init__(self):
        super().__init__()

    def build_messages(msg: str) -> TYPE_MESSAGES:
        return [msg]

    def create_message(
        self,
        messages: List[Dict[str, str]],
        model: str = "No need model",
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:

        system_preprocessed = re.sub(pattern=r"#.*,", repl=",", string=system)
        infos_to_extract = _extract_json(system_preprocessed)
        data = {
            name: f"info{n+1}"
            for n, (name, obj) in enumerate(infos_to_extract.items())
            if isinstance(obj, str)
        }
        text = f"```json{json.dumps(data)}```"
        return text


if __name__ == "__main__":
    llm_test = LlmTest()
    prompt_system = """
        ```json
        {
            "lieu_expertise" : "string",
            "numero_rg" : "string" # description : avec ce format...,
            "demandeur" : [{"nom" : "string", "avocat" : "string"}, {"nom" : "string", "avocat" : "string"}]
        }```
        """
    res = llm_test.create_message(messages=[], system=prompt_system)
    print(res)
