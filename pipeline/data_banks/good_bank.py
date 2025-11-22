"""Store or forward records that meet quality and validation criteria."""

from __future__ import annotations

from pathlib import Path

from pipeline.utils.file_utils import copy_file, ensure_dir, save_json


def store(package_id: str, working_dir: str, artifacts: dict, version: int = 1) -> dict:
    """
    Persist pipeline artifacts into a versioned Good Data Bank folder.

    Artifacts can include paths for:
      - score_json
      - classification_json
      - validation_json
      - memo_text
      - memo_json
      - pdf_texts_json
    """
    base = ensure_dir(Path("pipeline/data_banks/good_bank") / package_id / f"v{version}")
    copied = {}
    for key, path in artifacts.items():
        if not path:
            continue
        dest = base / Path(path).name
        copy_file(path, dest)
        copied[key] = str(dest)

    manifest = {"package_id": package_id, "version": version, "artifacts": copied}
    manifest_path = save_json(manifest, base / "manifest.json")
    copied["manifest"] = str(manifest_path)
    return copied
