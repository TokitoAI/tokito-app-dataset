"""Preserve a phone gallery batch and emit fail-closed image provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "work/gallery-intake-2026-10-11"
DEFAULT_OUTPUT = ROOT / "data/phone-captures/2026-10-11/gallery"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def import_gallery(source: Path, output: Path) -> dict:
    source, output = source.resolve(), output.resolve()
    if not source.is_dir():
        raise FileNotFoundError(source)
    if not output.is_relative_to(ROOT):
        raise ValueError("Gallery output must remain inside the repository")
    photos = sorted(source.glob("IMG_*.jpg"))
    if not photos:
        raise ValueError(f"No IMG_*.jpg originals found in {source}")

    output.mkdir(parents=True, exist_ok=True)
    records = []
    for photo in photos:
        with Image.open(photo) as image:
            image.verify()
        with Image.open(photo) as image:
            width, height = image.size
            exif = image.getexif()
            captured_at = exif.get(36867) or exif.get(306)
            orientation = exif.get(274, 1)
        digest = sha256(photo)
        destination = output / photo.name
        if destination.exists():
            if sha256(destination) != digest:
                raise ValueError(f"Refusing to overwrite changed gallery photo: {destination}")
        else:
            shutil.copy2(photo, destination)
        group = re.sub(r"_1(?=\.jpg$)", "", photo.name, flags=re.IGNORECASE)
        records.append(
            {
                "path": destination.relative_to(ROOT).as_posix(),
                "source_device": "iQOO I2501 camera gallery (ADB retrieval)",
                "source_filename": photo.name,
                "sha256": digest,
                "bytes": photo.stat().st_size,
                "width": width,
                "height": height,
                "exif_datetime_original": captured_at,
                "exif_orientation": orientation,
                "candidate_capture_group": group,
                "board_family": None,
                "view_slot": None,
                "review_status": "unreviewed",
                "training_export_eligible": False,
                "evaluation_eligible": False,
            }
        )
    manifest = {
        "schema_version": "1.0",
        "intake_id": "iqoo-gallery-2026-10-11",
        "retrieval": "Original IMG_*.jpg files copied byte-for-byte from the local ADB gallery intake; contact sheets excluded.",
        "capture_session_id": "iqoo-gallery-session-2026-10-11",
        "review_status": "unreviewed",
        "training_export_eligible": False,
        "evaluation_eligible": False,
        "photo_count": len(records),
        "total_bytes": sum(record["bytes"] for record in records),
        "images": records,
        "limits": [
            "No board identity, component boundary, view slot, or metric camera pose is inferred at intake.",
            "Near-duplicate images share candidate capture groups and must not cross dataset folds.",
            "Hash verification establishes byte provenance only, not annotation correctness.",
        ],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"photo_count": len(records), "total_bytes": manifest["total_bytes"],
            "manifest": manifest_path.relative_to(ROOT).as_posix()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(import_gallery(args.source, args.output)))


if __name__ == "__main__":
    main()
