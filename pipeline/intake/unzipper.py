"""Handle decompression of intake zip archives."""

import zipfile
from pathlib import Path
from typing import Iterable

from pipeline.utils.file_utils import ensure_dir


def unzip_archive(zip_path: str, target_dir: str) -> Iterable[Path]:
    """
    Extract the provided ZIP to target_dir and yield extracted file paths.

    Non-file entries are skipped.
    """
    target = ensure_dir(target_dir)
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.endswith("/"):
                continue
            destination = target / member
            ensure_dir(destination.parent)
            with zf.open(member) as src, destination.open("wb") as dst:
                dst.write(src.read())
            extracted.append(destination)
    return extracted
