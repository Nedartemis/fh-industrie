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
