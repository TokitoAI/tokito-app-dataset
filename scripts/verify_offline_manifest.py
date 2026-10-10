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


def pointer_metadata(path: Path):
    data = path.read_bytes()
    if not data.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        return None
    lines = data.decode("ascii").splitlines()
    values = dict(line.split(" ", 1) for line in lines[1:] if " " in line)
    oid = values.get("oid", "")
    if not oid.startswith("sha256:") or "size" not in values:
        raise ValueError(f"Malformed Git LFS pointer: {path.relative_to(ROOT)}")
    return oid.removeprefix("sha256:"), int(values["size"])


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = []
    for row in manifest["files"]:
        path = ROOT / row["path"]
        if not path.is_file():
            problems.append(f"missing: {row['path']}")
            continue
        pointer = pointer_metadata(path)
        if row["kind"] == "git_lfs_pointer_not_materialized":
            if pointer != (row["sha256"], row["bytes"]):
                problems.append(f"LFS pointer metadata mismatch: {row['path']}")
            continue
        if pointer is not None:
            problems.append(f"unexpected LFS pointer: {row['path']}")
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
