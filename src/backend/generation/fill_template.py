from pathlib import Path

from backend.config_file.config_file import read_info_values
from backend.excel.excel_book import ExcelBook
from backend.generation.fill_docx import fill_template_docx
from backend.generation.fill_excel import fill_template_excel
from backend.info_struct import InfoValues
from logger import logger
from logs_label import ExtensionFileNotSupported, PathNotExisting

# ------------------- Public Method -------------------


def fill_template(
    infos_path_file: Path, template_path: Path, path_folder_output: Path
) -> Path:

    # error detection
    if not infos_path_file.exists():
        raise PathNotExisting(infos_path_file)

    if not template_path.exists():
        raise PathNotExisting(template_path)

    if template_path.suffix[1:] not in ["xlsx", "docx"]:
        raise ExtensionFileNotSupported(template_path)

    # extracted infos from filled config file
    infos = read_info_values(infos_path_file)

    logger.info(f"Infos : {infos}")

    # copy and filled the template
    path_output = path_folder_output / (
        template_path.stem + "_généré" + template_path.suffix
    )

    if template_path.suffix.endswith("xlsx"):
        logger.info("The template is an excel")
        nb_changes = fill_template_excel(
            path_excel=template_path, infos=infos, path_output=path_output
        )
    elif template_path.suffix.endswith("docx"):
        logger.info("The template is a .docx")
        nb_changes = fill_template_docx(
            template_path=template_path, infos=infos, path_output=path_output
        )
    else:
        raise ExtensionFileNotSupported(template_path)

    logger.info(f"nb_changes : {nb_changes}")
    logger.info(f"Le modèle a bien été rempli et sauvegardé à '{path_output}'.")

    # return the new file
    return path_output


# ------------------- Main Method -------------------

if __name__ == "__main__":
    from vars import PATH_TEST_DOCS

    if True:
        path_test = PATH_TEST_DOCS / "test_generation"
        fill_template(
            infos_path_file=path_test / "config_file.xlsx",
            template_path=path_test
            / "TJ NAP1 - Visio administrative & Convocation modele.docx",
            path_folder_output=path_test,
        )
    else:
        path = PATH_TEST_DOCS / "feuille présence"
        fill_template(
            infos_path_file=path / "fichier_configuration_rempli.xlsx",
            template_path=path / "feuille_présence_modele.xlsx",
        )
