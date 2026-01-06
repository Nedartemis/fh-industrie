import re
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

import unidecode

from backend.generation.constants import BORDER_LEFT, BORDER_RIGHT, HARMONIZE_LABEL_INFO
from logs_label import DuplicatesNameAfterHarmonization
from utils.collection_ope import find_duplicates


@dataclass
class ReplaceRes:
    changed_text: str
    nb_changes: int


def replace_text(
    s: str,
    pair_old_new: Dict[str, Optional[str]],
    border_left: str = BORDER_LEFT,
    border_right: str = BORDER_RIGHT,
    do_harmonization: bool = HARMONIZE_LABEL_INFO,
) -> ReplaceRes:
    # choose the string transformer
    tr = (
        (lambda x: unidecode.unidecode(x).lower().replace(" ", "_"))
        if do_harmonization
        else lambda x: x
    )

    old_duplicates_after_harmonization = find_duplicates(
        [tr(old) for old in pair_old_new]
    )
    if old_duplicates_after_harmonization:
        raise DuplicatesNameAfterHarmonization(names=old_duplicates_after_harmonization)

    pair_old_new_tr = {tr(old): new for old, new in pair_old_new.items()}

    def _replace_text_rec(s: str, nb_changes: int) -> Tuple[str, int]:
        matches = re.finditer(
            pattern=f"{border_left}[^{border_right}]*{border_right}", string=s
        )

        for e in matches:

            # take sub string
            word = s[e.start(0) + len(border_left) : e.end(0) - len(border_right)]

            new = pair_old_new_tr.get(tr(word), None)

            if new is not None:

                # replace string
                s = s[: e.start(0)] + (new if new else "") + s[e.end(0) :]

                # recursive call because regex matches indexes might have change
                return _replace_text_rec(
                    s=s,
                    nb_changes=nb_changes + 1,
                )

        return s, nb_changes

    # first call
    res = _replace_text_rec(s=s, nb_changes=0)
    return ReplaceRes(changed_text=res[0], nb_changes=res[1])


def build_replace_text(
    pair_old_new: Dict[str, Optional[str]],
) -> Callable[[str], Tuple[str, int]]:

    def replace_text_custom(s: str) -> Tuple[str, int]:
        res = replace_text(s, pair_old_new=pair_old_new)
        return res.changed_text, res.nb_changes

    return replace_text_custom


if __name__ == "__main__":
    res = replace_text(
        "le {écho} toto {caca} |",
        pair_old_new=[("ècho", "foo"), ("toto", "tutu"), ("caca", "pipi")],
        border_left="{",
        border_right="}",
        do_harmonization=False,
    )
    print(res)
