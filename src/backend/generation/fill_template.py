from pathlib import Path
from typing import Dict

from docx import Document

from backend.excel_manager import ExcelManager
from backend.generation import BORDER_LEFT, BORDER_RIGHT, HARMONIZE_LABEL_INFO
from backend.generation.replace_text import replace_text
from backend.manage_config_file import read_config_file_files_infos_values
from vars import DEFAULT_LOGGER, PATH_TMP, TYPE_LOGGER

# ------------------- Public Method -------------------


def fill_template(
    infos_path_file: Path, template_path: Path, log: TYPE_LOGGER = DEFAULT_LOGGER
) -> Path:

    # error detection
    if not infos_path_file.exists():
        raise RuntimeError("Info file does not exist")

    # extract infos from filled file
    infos = read_config_file_files_infos_values(ExcelManager(infos_path_file))

    # remove accents and other things
    log(f"Infos : {infos}")

    # error detection
    if not template_path.exists():
        raise RuntimeError("Template file does not exist")

    if template_path.suffix[1:] not in ["xlsx", "docx"]:
        raise RuntimeError(
            f"L'extension '{template_path.suffix}' du modèle n'est pas supporté."
        )

    # copy and filled the template
    path_output = PATH_TMP / (template_path.stem + "_généré" + template_path.suffix)

    if template_path.suffix.endswith("xlsx"):
        log("Le modèle est un excel")
        _fill_template_excel(template_path, infos, path_output)
    elif template_path.suffix.endswith("docx"):
        log("Le modèle est un .docx")
        _fill_template_docx(template_path, infos, path_output)
    else:
        raise RuntimeError(
            f"L'extension '{template_path.suffix}' du modèle n'est pas supporté."
        )

    log(f"Le modèle a bien été rempli et sauvegardé à '{path_output}'.")

    # return the new file
    return path_output


# ------------------- Private Method -------------------


def _fill_template_excel(
    template_path: Path, infos: Dict[str, str], path_output: Path
) -> None:

    em = ExcelManager(template_path)
    em.replace_content(infos)
    em.save(path_output)


def _fill_template_docx(
    template_path: Path, infos: Dict[str, str], path_output: Path
) -> None:

    # open doc
    doc = Document(template_path)

    # go through each paragraphs
    for para in doc.paragraphs:
        # go through each infos
        para.text, _ = replace_text(
            s=para.text,
            pair_old_new=list(infos.items()),
            border_left=BORDER_LEFT,
            border_right=BORDER_RIGHT,
            do_harmonization=HARMONIZE_LABEL_INFO,
        )

    doc.save(path_output)


# ------------------- Main Method -------------------

if __name__ == "__main__":
    from vars import PATH_TEST

    path_test = PATH_TEST / "test_generation"
    fill_template(
        infos_path_file=path_test / "config_file.xlsx",
        template_path=path_test
        / "TJ NAP1 - Visio administrative & Convocation modele.docx",
        log=DEFAULT_LOGGER,
    )
