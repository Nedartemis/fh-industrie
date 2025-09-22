from pathlib import Path

import io_helper


def read_data_conditionned(path: Path, condition: bool):
    return (
        io_helper.read(path_to_read=path)
        if condition
        else b"The download should have not happened."
    )
