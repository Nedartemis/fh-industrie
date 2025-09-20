from pathlib import Path
from typing import Dict

from docx import Document

from backend.excel_manager import ExcelManager
from backend.manage_config_file import read_config_file_files_infos_values
from frontend.logger import LogLevel
from frontend.logger import log as front_log
from vars import PATH_TMP

# ------------------- Public Method -------------------


def fill_template(infos_path_file: Path, template_path: Path) -> str:

    # error detection
    if not infos_path_file.exists():
        raise RuntimeError("Info file does not exist")

    if not template_path.exists():
        raise RuntimeError("Template file does not exist")

    if template_path.suffix[1:] not in ["xlsx", "docx"]:
        raise RuntimeError(
            f"L'extension '{template_path.suffix}' du modèle n'est pas supporté."
        )

    # extract infos from filled file
    infos = read_config_file_files_infos_values(ExcelManager(infos_path_file))

    # copy and filled the template
    path_output = PATH_TMP / (template_path.stem + "_rempli" + template_path.suffix)

    if template_path.suffix.endswith("xlsx"):
        _fill_template_excel(template_path, infos, path_output)
    elif template_path.suffix.endswith("docx"):
        _fill_template_docx(template_path, infos, path_output)
    else:
        raise RuntimeError(
            f"L'extension '{template_path.suffix}' du modèle n'est pas supporté."
        )

    front_log(LogLevel.INFO, "Le modèle a bien été rempli et sauvegardé.")

    # return the new file
    return path_output


# ------------------- Private Method -------------------


def _fill_template_excel(
    template_path: Path, infos: Dict[str, str], path_output: Path
) -> None:
    front_log(LogLevel.INFO, "Le modèle est un excel")

    em = ExcelManager(template_path)
    em.replace_content(infos)
    em.save(path_output)


def _fill_template_docx(
    template_path: Path, infos: Dict[str, str], path_output: Path
) -> None:

    front_log(LogLevel.INFO, "Le modèle est un .docx")
    doc = Document(template_path)
    for para in doc.paragraphs:
        for key, value in infos.items():
            if key in para.text:
                para.text = para.text.replace("{" + key + "}", value)
                print(para.text)

    doc.save(path_output)
