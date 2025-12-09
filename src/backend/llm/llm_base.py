from abc import abstractmethod
from typing import Any, Dict, List, Optional

TYPE_MESSAGES = List[Dict[str, str]]


class LlmBase:

    def __init__(self):
        pass

    @abstractmethod
    def build_messages(msg: str) -> TYPE_MESSAGES:
        pass

    @abstractmethod
    def create_message(
        self,
        model: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Dict[str, Any]:
        pass
