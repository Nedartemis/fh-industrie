import __future__

from typing import Callable, Dict, List, Optional, Set, Tuple, TypeVar

T = TypeVar("T")
C = TypeVar("C")
M = TypeVar("M")
M2 = TypeVar("M2")
K = TypeVar("K")
V = TypeVar("V")


class Stream[T]:

    lst: List[T]

    def __init__(self, lst: List[T]):
        self.lst = lst

    @staticmethod
    def from_set(s: Set[C]) -> "Stream[C]":
        return Stream(list(s))

    @staticmethod
    def of(e: T) -> "Stream[T]":
        return Stream([e])

    def map(self, mapper: Callable[[T], M]) -> "Stream[M]":
        return Stream([mapper(e) for e in self.lst])

    def filter(self, accepted: Callable[[T], bool]) -> "Stream[T]":
        return Stream([e for e in self.lst if accepted(e)])

    def unique(self) -> "Stream[T]":
        return Stream(list(set(self.lst)))

    def count(self) -> int:
        return len(self.lst)

    def groupby(
        self,
        key: Callable[[T], K],
        value: Callable[[T], M] = lambda x: x,
    ) -> "Stream[Tuple[K, List[M]]]":
        d: Dict[K, List[M]] = dict()
        for e in self.lst:
            k = key(e)
            if not k in d:
                d[k] = []
            d[k].append(value(e))

        return Stream([(k, v) for k, v in d.items()])

    @staticmethod
    def to_dict(s: "Stream[Tuple[K, V]]") -> Dict[K, V]:
        return {k: v for k, v in s.lst}

    @staticmethod
    def to_list_opt(s: "Stream[Tuple[int, V]]") -> List[Optional[V]]:
        idx_max = max(idx for idx, _ in s.lst)
        l = [None] * (idx_max + 1)
        for idx, value in s.lst:
            l[idx] = value
        return l

    @classmethod
    def to_list(cls, s: "Stream[Tuple[int, V]]") -> List[V]:

        l = cls.to_list_opt(s)
        if any(e is None for e in l):
            raise ValueError("An index has no values")
        return l

    def __repr__(self):
        return str(self.lst)
