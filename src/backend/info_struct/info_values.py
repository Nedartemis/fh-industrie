from dataclasses import dataclass
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple, TypeVar, Union

from backend.config_file.info_page.info_list_helper import SPLITTER
from utils.collection_ope import dict_to_list
from utils.stream import Stream

TYPE_NAME = Union[str, Tuple[str, str]]
TYPE_INFO_LIST_VALUES = Dict[str, List[Dict[str, Optional[str]]]]

T = TypeVar("T")

TupleInd = NamedTuple("independant_info", [("name", str), ("value", Optional[str])])
TupleLst = NamedTuple(
    "list_info",
    [("first_name", str), ("idx", int), ("sub_name", str), ("value", Optional[str])],
)
TupleAll = NamedTuple("all_info", [("name", str), ("value", Optional[str])])


def _predicate_keep_none_value(
    keep: bool,
) -> Callable[[Union[TupleInd, TupleLst]], bool]:
    if keep:
        return lambda t: True
    return lambda t: t.value is not None


@dataclass
class InfoValues:
    # {
    #   "name1": "value1",
    #   "name2": "value2"
    # }
    independant_infos: Dict[str, Optional[str]]
    # {
    #   "fist_name1": [
    #       {
    #           "subname1": "value1",
    #           "subname2": "value2"
    #       },
    #       {
    #           "subname1": "value3",
    #           "subname2": "value4"
    #       }
    #   ],
    #   "first_name2": ...
    # }
    list_infos: TYPE_INFO_LIST_VALUES

    @staticmethod
    def empty() -> "InfoValues":
        return InfoValues(independant_infos={}, list_infos={})

    # ------------------- Generic methods -------------------

    def _stream_ind(self) -> Stream[TupleInd]:
        lst = [
            TupleInd(name=name, value=value)
            for name, value in self.independant_infos.items()
        ]
        return Stream(lst)

    def _stream_lst(self) -> Stream[TupleLst]:
        lst = [
            TupleLst(first_name=first_name, idx=idx, sub_name=sub_name, value=value)
            for first_name, l in self.list_infos.items()
            for idx, d in enumerate(l)
            for sub_name, value in d.items()
        ]
        return Stream(lst)

    def _stream_all(self) -> Stream[TupleAll]:
        l1 = self._stream_ind().map(lambda t: TupleAll(name=t.name, value=t.value)).lst
        l2 = (
            self._stream_lst()
            .map(
                lambda t: TupleAll(
                    name=f"{t.first_name}{SPLITTER}{t.sub_name}", value=t.value
                )
            )
            .lst
        )
        return Stream(l1 + l2)

    def _store_ind(self, s: Stream[TupleInd]) -> None:
        self.independant_infos = {t.name: t.value for t in s.lst}

    def _store_lst(self, s: Stream[TupleLst]) -> None:
        l1 = s.groupby(key=lambda t: t.first_name).lst

        d = {}
        for first_name, l2 in l1:
            s2 = Stream(l2).groupby(key=lambda t: t.idx)
            l3 = Stream.to_list(s2)
            l4 = [{t.sub_name: t.value for t in lst} for lst in l3]
            d[first_name] = l4

        self.list_infos = d

    # ------------------- Getter -------------------

    def get_names_independant_info(self, keep_none_values: bool) -> List[str]:
        return (
            self._stream_ind()
            .filter(_predicate_keep_none_value(keep_none_values))
            .map(mapper=lambda t: t.name)
            .lst
        )

    def get_names_list_info(self, keep_none_values: bool) -> List[Tuple[str, str]]:
        return (
            self._stream_lst()
            .filter(_predicate_keep_none_value(keep_none_values))
            .map(mapper=lambda t: (t.first_name, t.sub_name))
            .unique()
            .lst
        )

    def get_names(self, keep_none_values: bool) -> List[TYPE_NAME]:
        return self.get_names_independant_info(
            keep_none_values
        ) + self.get_names_list_info(keep_none_values)

    def get_name_nones(self) -> List[TYPE_NAME]:
        return (
            (
                self._stream_ind()
                .filter(lambda t: t.value is None)
                .map(lambda t: t.name)
                + self._stream_lst()
                .filter(lambda t: t.value is None)
                .map(lambda t: (t.first_name, t.sub_name))
            )
            .unique()
            .lst
        )

    def count_values(self) -> int:
        return self._stream_all().filter(_predicate_keep_none_value(False)).count()

    # ------------------- Modifier -------------------

    def filter_names(self, names_to_remove: TYPE_NAME) -> None:
        s = self._stream_ind().filter(lambda t: t.name not in names_to_remove)
        self._store_ind(s)

        s = self._stream_lst().filter(lambda t: t.first_name not in names_to_remove)
        self._store_lst(s)

    def update(self, other: "InfoValues") -> None:
        self.independant_infos.update(other.independant_infos)
        self.list_infos.update(other.list_infos)
