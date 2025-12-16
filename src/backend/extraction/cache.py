import json
import os
from pathlib import Path
from typing import List, Optional, Union

from logger import logger
from vars import PATH_CACHE

TYPES_ALLOWED = Union[List, dict]


def _to_path_cache(path: Path) -> Path:
    return PATH_CACHE / (path.replace(os.sep, "|") + ".json")


def exist_cache(path: Path):
    return _to_path_cache(path).exists()


def load(path: Path) -> Optional[TYPES_ALLOWED]:

    if not exist_cache(path):
        return None

    path_cache = _to_path_cache(path)

    with open(str(path_cache), mode="r") as f:
        pages = json.load(f)

    logger.info(f"'{path}' loaded from cache.")
    return pages


def save(path: Path, obj: TYPES_ALLOWED) -> None:

    path_cache = _to_path_cache(path)

    with open(str(path_cache), mode="w") as f:
        json.dump(obj, f)

    logger.info(f"'{path}' saved in cache.")


if __name__ == "__main__":

    def tr(s: str):
        return s
        return s.replace("\n", " ").replace("’", "'").replace("  ", " ")

    obj = load(
        "tests/testsuite_docs/extraction/exact/TJ ROUEN_24800954_LEBRETON_Ordonnance.pdf"
    )
    # print(obj)
    for page in obj[5:7]:
        print(page)
        print(tr(page))

    actual = ""

    text = tr("\n".join(tr(s) for s in obj))
    pattern = tr(actual)

    # print(tr(actual) in tr(obj[5]))

    # text = "hello world this is python"
    # pattern = "world"

    
    print(m[0])
    print()
    print(m[1])
    print()
    print(m[2])
    print(text[m[2] : m[2] + len(actual)])
    print()
    print(actual)

    # from difflib import SequenceMatcher

    # def similar(a, b):
    #     return SequenceMatcher(None, a, b).ratio()

    # print(similar("\n".join(obj[5:7]), actual))
