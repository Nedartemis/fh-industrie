import io
import zipfile
from pathlib import Path
from typing import Union


def extract_zip_file(zip_file: bytes, path_dst: Union[str, Path]) -> None:
    """

    Raises:
        zipfile.BadZipFile
    """

    with zipfile.ZipFile(io.BytesIO(zip_file)) as zf:
        zf.extractall(path=path_dst)


def write(bytes_to_write: bytes, path_dst: Union[str, Path]) -> None:
    with open(path_dst, "wb") as f:
        f.write(bytes_to_write)


def read(path_to_read: Union[str, Path]) -> bytes:
    """

    Raises:
        FileNotFoundError
    """
    with open(path_to_read, "rb") as f:
        file_data = f.read()
    return file_data
