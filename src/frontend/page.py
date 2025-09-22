from abc import ABC, abstractmethod


class Page(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def build_page(self) -> None:
        pass
