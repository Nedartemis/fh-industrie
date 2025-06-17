from pathlib import Path

import docs as docs_module
import tmp as tmp_module

PATH_TMP = Path(tmp_module.__file__).parent
PATH_DOCS = Path(docs_module.__file__).parent
PATH_DOCS_PASCALE = PATH_DOCS / "pascal"
PATH_CONFIG_FILE = PATH_TMP / "fichier_configuration.xlsx"
