import re
from typing import List, Tuple

import unidecode


def replace_text(
    s: str,
    pair_old_new: List[Tuple[str, str]],
    border_left: str,
    border_right: str,
    do_harmonization: bool,
) -> Tuple[str, int]:
    # choose the string transformer
    tr = lambda x: (
        unidecode.unidecode(x).lower().replace(" ", "_")
        if do_harmonization
        else lambda x: x
    )

    def _replace_text_rec(s: str, n_changes: int) -> Tuple[str, int]:
        matches = re.finditer(
            pattern=f"{border_left}[^{border_right}]*{border_right}", string=s
        )

        for e in matches:
            for old, new in pair_old_new:
                # take sub string
                word = s[e.start(0) + len(border_left) : e.end(0) - len(border_right)]

                # check equality
                if tr(old) == tr(word):

                    # replace string
                    s = s[: e.start(0)] + (new if new else "") + s[e.end(0) :]

                    # recursive call because regex matches indexes might have change
                    return _replace_text_rec(
                        s=s,
                        n_changes=n_changes + 1,
                    )

        return s, n_changes

    # first call
    return _replace_text_rec(s=s, n_changes=0)


if __name__ == "__main__":
    res = replace_text(
        "le {écho} toto {caca} |",
        pair_old_new=[("ècho", "foo"), ("toto", "tutu"), ("caca", "pipi")],
        border_left="{",
        border_right="}",
        do_harmonization=False,
    )
    print(res)
