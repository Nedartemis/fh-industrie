from abc import ABC, abstractmethod


class LogLabel(ABC):
    def __getitem__(self, key):
        return self

    def __iter__(self):
        return iter(["label"])

    # @abstractmethod
    # def msg(self) -> str:
    #     pass
