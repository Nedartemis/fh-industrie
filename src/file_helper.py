import os
import shutil
from pathlib import Path
from typing import List


def rmtree(
    root: Path,
    rm_root: bool = True,
    ext_file_to_avoid_removing_at_the_root: List[str] = list(),
) -> None:
    if rm_root:
        shutil.rmtree(root)
        return

    for sub_dir in os.listdir(path=root):
        path = root / sub_dir
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            if path.suffix.lower()[1:] in ext_file_to_avoid_removing_at_the_root:
                continue
            os.remove(path)
        else:
            raise RuntimeError(
                f"The file '{path}' cannot be removed because its type is not handled."
            )


if __name__ == "__main__":

    from vars import PATH_TMP

    rmtree(PATH_TMP, rm_root=False)
