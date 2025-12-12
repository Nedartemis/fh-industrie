import os
from pathlib import Path
from typing import Callable, List

import tmp as tmp_module

# path
try:
    # in local
    PATH_TMP = Path(tmp_module.__file__).parent
except:
    # when deployed
    PATH_TMP = Path("tmp/").resolve()

PATH_ROOT = PATH_TMP.parent.resolve()

PATH_DOCS = PATH_ROOT / "docs"
PATH_TEMPLATE = PATH_ROOT / "templates"
PATH_CACHE = PATH_ROOT / "cache"
PATH_TEST_DOCS = PATH_ROOT / "test_docs"
PATH_TEST_DOCS_TESTSUITE = PATH_ROOT / "tests" / "testsuite_docs"

# logger
TYPE_LOGGER = Callable[[str], None]
DEFAULT_LOGGER = print
LAZY_LOGGER = lambda _: None

# extraction
SUPPORTED_FILES_EXT_EXTRACTION: List[str] = ["pdf", "txt"]

# RUN PARAMETERS
TEST_WITHOUT_INTERNET: bool = os.environ.get("TEST_WITHOUT_INTERNET") is not None
