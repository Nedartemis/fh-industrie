from pathlib import Path
from typing import Callable

import tmp as tmp_module

# path
PATH_TMP = Path(tmp_module.__file__).parent

PATH_ROOT = PATH_TMP.parent.resolve()

PATH_DOCS = PATH_ROOT / "docs"
PATH_DOCS_PASCALE = PATH_DOCS / "pascal"

PATH_TEMPLATE = PATH_ROOT / "templates"
PATH_CACHE = PATH_ROOT / "cache"
PATH_TEST = PATH_ROOT / "test"
PATH_CONFIG_FILE = PATH_TEST / "config_file.xlsx"

# logger
TYPE_LOGGER = Callable[[str], None]
DEFAULT_LOGGER = print
LAZY_LOGGER = lambda _: None
