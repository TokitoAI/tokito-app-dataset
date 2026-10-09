"""Verify every file recorded in the offline materialization manifest."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/samples/ultimainboard-2.1.4/offline-manifest.json"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = []
    for row in manifest["files"]:
        path = ROOT / row["path"]
        if not path.is_file():
            problems.append(f"missing: {row['path']}")
            continue
        if path.stat().st_size != row["bytes"]:
            problems.append(f"size mismatch: {row['path']}")
            continue
        if digest(path) != row["sha256"]:
            problems.append(f"SHA-256 mismatch: {row['path']}")
    if problems:
        print("Offline manifest verification failed:", *problems, sep="\n  ")
        return 1
    print(f"Verified {len(manifest['files'])} materialized files against {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
