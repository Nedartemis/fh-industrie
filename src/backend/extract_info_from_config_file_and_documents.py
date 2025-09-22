from pathlib import Path
from typing import Dict

from backend.claude_client import ClaudeClient
from backend.extract_info_from_pdf import extract_info_from_pdf
from backend.manage_config_file import fill_config_file, read_config_file
from vars import PATH_TMP


def extract_infos_from_tree_and_config_file(
    path_config_file: Path, path_folder_sources: Path
) -> Path:
    if not path_config_file.exists():
        raise RuntimeError("Configuration file does not exist")

    print("Reading config file...")

    files_path, files_infos = read_config_file(path_config_file, path_folder_sources)

    print(files_path)
    print(files_infos)

    print("Extracting infos...")

    # log action that are going to be done
    print(
        f"{len(files_path)} fichiers vont être analysés.\n"
        + f"{sum(len(e) for e in files_infos.values())} informations doivent être extraites.",
    )

    all_infos: Dict[str, str] = {}

    for source_name, infos in files_infos.items():

        new_infos = extract_info_from_pdf(
            ClaudeClient(),
            path_folder_sources / files_path[source_name],
            names_infos=[info_name for info_name, _ in infos],
            log=print,
        )

        # save new infos by merging
        all_infos.update(new_infos)

    print(f"{len(all_infos)} informations ont été extraites avec succès.")

    # copy and fill config file
    info_path_file = path_folder_sources / f"{path_config_file.stem}_rempli.xlsx"
    fill_config_file(path_config_file, infos=all_infos, path_output=info_path_file)

    # return the file containing the infos
    return info_path_file


if __name__ == "__main__":
    from vars import PATH_TEST

    path_test = PATH_TEST / "test_celine"
    extract_infos_from_tree_and_config_file(
        path_test / "fichier_configuration_rempli.xlsx",
        path_folder_sources=path_test,
    )
