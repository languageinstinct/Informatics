"""Receive and persist incoming zip files for processing."""

from pathlib import Path

from pipeline.utils.file_utils import ensure_dir


def receive_zip(file_bytes: bytes, destination: str) -> str:
    """Save incoming zip bytes to destination and return the saved file path."""
    dest = Path(destination)
    ensure_dir(dest.parent)
    dest.write_bytes(file_bytes)
    return str(dest)


def save_zip_locally(source_zip_path: str, workdir: str) -> str:
    """Copy an existing ZIP into the pipeline workdir to isolate processing."""
    dest = Path(workdir) / Path(source_zip_path).name
    ensure_dir(dest.parent)
    dest.write_bytes(Path(source_zip_path).read_bytes())
    return str(dest)
