from pathlib import Path
from typing import Callable

import docs as docs_module
import tmp as tmp_module

PATH_TMP = Path(tmp_module.__file__).parent
PATH_ROOT = PATH_TMP.parent.resolve()
PATH_DOCS = Path(docs_module.__file__).parent
PATH_DOCS_PASCALE = PATH_DOCS / "pascal"
PATH_TEMPLATE = PATH_DOCS.parent / "templates"
PATH_CACHE = PATH_DOCS.parent / "cache"
PATH_TEST = PATH_DOCS.parent / "test"
PATH_CONFIG_FILE = PATH_TEST / "config_file.xlsx"

TYPE_LOGGER = Callable[[str], None]
DEFAULT_LOGGER = print
LAZY_LOGGER = lambda _: None
