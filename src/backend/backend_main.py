import json
from pathlib import Path
from typing import Dict, Optional

from backend.claude_client import ClaudeClient
from backend.extract_info_from_natural_language import (
    extract_info_from_natural_language,
)
from backend.fill_template import fill_template
from backend.manage_config_file import fill_config_file, read_config_file
from backend.read_pdf import is_scanned, read_all_pdf
from frontend.logger import LogLevel
from frontend.logger import log as front_log
from vars import PATH_CONFIG_FILE, PATH_TMP


def _backend_log(message: str) -> None:
    print(f"Backend : {message}")


def _all_log(log_level: LogLevel, message: str) -> None:
    _backend_log(f"{str(log_level)} : {message}")
    front_log(log_level, message)


class Backend:

    template_path: Optional[Path]
    info_path_file: Optional[Path]

    def __init__(self):

        self.claude_client = ClaudeClient()
        self.path_config_file = PATH_CONFIG_FILE
        self.reset()

    def reset(self) -> None:
        _backend_log("Reset")

    @staticmethod
    def _get_pdf_pages(label_source: str, relative_path: str):
        path_cache = PATH_TMP / (label_source + ".json")

        if path_cache.exists():
            # read from cache
            with open(str(path_cache), mode="r") as f:
                pages = json.load(f)
            _all_log(LogLevel.INFO, f"'{label_source}' chargé depuis le cache.")
        else:
            # read pdf
            path = PATH_TMP / relative_path
            pages = read_all_pdf(path)
            _all_log(
                LogLevel.INFO,
                f"'{label_source}' a été lu et est un pdf {'scanné' if is_scanned(path) else 'natif'}.",
            )

            # save into cache
            with open(str(path_cache), mode="w") as f:
                json.dump(pages, f)

        return pages

    def extract_infos_from_tree_and_config_file(self) -> str:
        if not self.path_config_file.exists():
            raise RuntimeError("Configuration file does not exist")

        _backend_log("Reading config file...")
        path_config_file = self.path_config_file
        files_path, files_infos = read_config_file(path_config_file)

        _backend_log("Extracting infos...")

        # log action that are going to be done
        _all_log(
            LogLevel.INFO,
            f"{len(files_path)} fichiers vont être analysés.\n"
            + f"{sum(len(e) for e in files_infos.values())} informations doivent être extraites.",
        )

        all_infos: Dict[str, str] = {}

        for source_name, infos in files_infos.items():
            names_infos = [info_name for info_name, _ in infos]

            # get pages
            pages = self._get_pdf_pages(source_name, files_path[source_name])

            # extract info from the text
            new_infos = extract_info_from_natural_language(
                claude_client=self.claude_client,
                names_infos=names_infos,
                text="\n\n".join(pages[:1]),
            )

            # save new infos
            all_infos.update(new_infos)

            # error detection

            # -- found wrong ones
            for name_info in new_infos:
                if name_info not in names_infos:
                    _backend_log(
                        f"'{name_info}' a été extrait mais n'avait pas été demandé."
                    )

            # -- those not found
            for name_info in names_infos:
                if name_info not in new_infos.keys():
                    _backend_log(f"'{name_info}' n'a pas été extrait.")

        _all_log(
            LogLevel.INFO,
            f"{len(all_infos)} informations ont été extraites avec succès.",
        )

        # copy config file
        self.info_path_file = PATH_TMP / "fichier_configuration_rempli.xlsx"
        fill_config_file(
            path_config_file, infos=all_infos, path_output=self.info_path_file
        )

        # return the file containing the infos
        return str(self.info_path_file)

    def set_template_path(self, path: str):
        self.template_path = Path(path)
        print(self.template_path)

    def fill_template(self) -> str:
        if self.template_path is None:
            raise RuntimeError("Template path is none")

        if self.info_path_file is None:
            raise RuntimeError("Info path file is none")

        return fill_template(self.template_path, self.info_path_file)


def _main():
    backend = Backend()

    backend.extract_infos_from_tree_and_config_file()


if __name__ == "__main__":
    _main()
