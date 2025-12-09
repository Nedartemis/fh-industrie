import __future__

from typing import Callable, Dict, List, Optional, Set, Tuple, TypeVar


class Stream:

    lst: List

    def __init__(self, lst: List):
        self.lst = lst

    @staticmethod
    def from_set(s: Set) -> "Stream":
        return Stream(list(s))

    @staticmethod
    def of(e) -> "Stream":
        return Stream([e])

    def map(self, mapper) -> "Stream":
        return Stream([mapper(e) for e in self.lst])

    def filter(self, accepted) -> "Stream":
        return Stream([e for e in self.lst if accepted(e)])

    def unique(self) -> "Stream":
        return Stream(list(set(self.lst)))

    def count(self) -> int:
        return len(self.lst)

    def groupby(
        self,
        key,
        value=lambda x: x,
    ) -> "Stream":
        d: Dict = dict()
        for e in self.lst:
            k = key(e)
            if not k in d:
                d[k] = []
            d[k].append(value(e))

        return Stream([(k, v) for k, v in d.items()])

    @staticmethod
    def to_dict(s: "Stream") -> Dict:
        return {k: v for k, v in s.lst}

    @staticmethod
    def to_list_opt(s: "Stream") -> List:
        idx_max = max(idx for idx, _ in s.lst)
        l = [None] * (idx_max + 1)
        for idx, value in s.lst:
            l[idx] = value
        return l

    @classmethod
    def to_list(cls, s: "Stream") -> List:

        l = cls.to_list_opt(s)
        if any(e is None for e in l):
            raise ValueError("An index has no values")
        return l

    def __repr__(self):
        return str(self.lst)
