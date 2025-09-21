from pathlib import Path
from typing import Dict

from docx import Document

from backend.excel_manager import ExcelManager
from backend.manage_config_file import read_config_file_files_infos_values
from vars import DEFAULT_LOGGER, PATH_TMP, TYPE_LOGGER

# ------------------- Public Method -------------------


def fill_template(
    infos_path_file: Path, template_path: Path, log: TYPE_LOGGER = DEFAULT_LOGGER
) -> str:

    # error detection
    if not infos_path_file.exists():
        raise RuntimeError("Info file does not exist")

    # extract infos from filled file
    infos = read_config_file_files_infos_values(ExcelManager(infos_path_file))
    log(f"Infos : {infos}")

    # error detection
    if not template_path.exists():
        raise RuntimeError("Template file does not exist")

    if template_path.suffix[1:] not in ["xlsx", "docx"]:
        raise RuntimeError(
            f"L'extension '{template_path.suffix}' du modèle n'est pas supporté."
        )

    # copy and filled the template
    path_output = PATH_TMP / (template_path.stem + "_rempli" + template_path.suffix)

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

    doc = Document(template_path)
    for para in doc.paragraphs:
        for key, value in infos.items():
            if key in para.text:
                para.text = para.text.replace("{" + key + "}", value)
                print(para.text)

    doc.save(path_output)


# ------------------- Main Method -------------------

if __name__ == "__main__":
    from vars import PATH_TEMPLATE, PATH_TEST

    fill_template(
        infos_path_file=PATH_TEST / "fichier_configuration_rempli.xlsx",
        template_path=PATH_TEMPLATE / "feuille_présence_modele.xlsx",
        log=DEFAULT_LOGGER,
    )
