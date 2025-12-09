from collections import Counter
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T")


def dict_to_list(d: Dict[int, T]) -> List[Optional[T]]:
    m = max(d.keys())
    l = [None] * (m + 1)
    for idx, value in d.items():
        l[idx] = value
    return l


def dict_to_list_throw_none(d: Dict[int, T]) -> List[T]:
    l = dict_to_list(d)
    if any(e is None for e in l):
        raise ValueError("An index has no values")
    return l


def find_duplicates(lst: List[Any]) -> List[Any]:
    return [e for e, nb_occurences in Counter(lst).items() if nb_occurences > 1]
