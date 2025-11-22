"""General file handling helpers for the pipeline."""

import json
import shutil
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    """Create the directory if it does not already exist and return the Path."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def save_json(data: Any, path: str | Path) -> Path:
    """Persist a JSON serialisable object to disk."""
    target = Path(path)
    ensure_dir(target.parent)
    with target.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    return target


def save_text(content: str, path: str | Path) -> Path:
    """Write plain text content to disk."""
    target = Path(path)
    ensure_dir(target.parent)
    target.write_text(content, encoding="utf-8")
    return target


def copy_file(source: str | Path, destination: str | Path) -> Path:
    """Copy a file to the destination directory."""
    src_path = Path(source)
    dest_path = Path(destination)
    ensure_dir(dest_path.parent)
    shutil.copy2(src_path, dest_path)
    return dest_path


def package_workdir(base_dir: str | Path, package_id: str) -> Path:
    """
    Create and return a working directory for a package.

    Example: data/workdir/<package_id>
    """
    return ensure_dir(Path(base_dir) / package_id)
