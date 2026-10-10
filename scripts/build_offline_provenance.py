"""Build offline manifests for the board dataset without inferring missing evidence."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "docs/samples/ultimainboard-2.1.4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def is_lfs_pointer(data: bytes) -> bool:
    return data.startswith(b"version https://git-lfs.github.com/spec/v1\n")


def lfs_metadata(data: bytes):
    fields = dict(line.split(" ", 1) for line in data.decode().splitlines())
    algorithm, digest = fields["oid"].split(":", 1)
    assert algorithm == "sha256"
    return digest, int(fields["size"])


def parse_sexpr(text: str):
    stack, root = [], None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == "(":
            value = []
            if stack:
                stack[-1].append(value)
            else:
                root = value
            stack.append(value)
        elif token == ")":
            stack.pop()
        else:
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    return root


def child(value, name):
    return next((x for x in value if isinstance(x, list) and x and x[0] == name), None)


def materialization_manifest():
    files = []
    counters = Counter()
    manifest_path = SAMPLE / "offline-manifest.json"
    tracked = subprocess.run(
        ["git", "ls-files", "--cached", "-z"], cwd=ROOT, check=True, capture_output=True
    ).stdout.split(b"\0")
    paths = sorted(ROOT / item.decode("utf-8") for item in tracked if item)
    for path in paths:
        if not path.is_file() or path == manifest_path:
            continue
        relative = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        if is_lfs_pointer(data):
            digest, size = lfs_metadata(data)
            files.append({"path": relative, "kind": "git_lfs_pointer_not_materialized", "sha256": digest, "bytes": size})
            counters["pointer"] += 1
        else:
            files.append({"path": relative, "kind": "materialized", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
            counters["materialized"] += 1
    value = {
        "schema_version": 1,
        "hash_algorithm": "SHA-256 over full file bytes; LFS pointers report their declared object SHA-256 and size",
        "files": files,
        "counts": dict(counters),
        "fully_materialized": counters["pointer"] == 0,
        "excluded_from_hash_inventory": [str(manifest_path.relative_to(ROOT)).replace("\\", "/")],
        "offline_bundle_requirement": "A bundle is complete only when fully_materialized is true and each materialized file hashes to this manifest.",
    }
    write(SAMPLE / "offline-manifest.json", value)
    return value


def model_mapping():
    board = ROOT / "data/board-sources/ultimainboard-2.1.4"
    pcb = board / "generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb"
    blocks = [parse_sexpr(x) for x in re.findall(r"^\t\(footprint .*?^\t\)", pcb.read_text(encoding="utf-8"), re.M | re.S)]
    rows = []
    for footprint in blocks:
        reference = next(x[2] for x in footprint if isinstance(x, list) and x[:2] == ["property", "Reference"])
        at = child(footprint, "at")
        base = {
            "reference_designator": reference,
            "footprint_uuid": child(footprint, "uuid")[1],
            "footprint": footprint[1],
            "placement_transform": {
                "coordinate_system": "imported KiCad board local coordinate system",
                "translation_mm": [float(at[1]), float(at[2]), 0.0],
                "rotation_degrees_z": float(at[3]) if len(at) > 3 else 0.0,
            },
        }
        models = [x for x in footprint if isinstance(x, list) and x and x[0] == "model"]
        if not models:
            rows.append({**base, "model_mapping_status": "unknown_no_imported_model_reference", "model": None})
        for model in models:
            offset, scale, rotate = child(model, "offset"), child(model, "scale"), child(model, "rotate")
            def xyz(record, default):
                xyz_record = child(record, "xyz") if record else None
                return [float(x) for x in xyz_record[1:]] if xyz_record else default
            rows.append({
                **base,
                "model_mapping_status": "imported_model_reference_with_unverified_native_equivalence",
                "model": {
                    "uri": model[1],
                    "units": "mm before KiCad placement; native Altium source association is unverified",
                    "local_offset_mm": xyz(offset, [0.0, 0.0, 0.0]),
                    "local_scale": xyz(scale, [1.0, 1.0, 1.0]),
                    "local_rotation_degrees_xyz": xyz(rotate, [0.0, 0.0, 0.0]),
                },
            })
    value = {
        "schema_version": 1,
        "source_pcb": str(pcb.relative_to(ROOT)).replace("\\", "/"),
        "source_pcb_sha256": sha256(pcb),
        "scope": "All model references emitted in the imported KiCad PCB. The transform is footprint placement composed with the listed model-local transform. It does not prove an extracted native STEP stream corresponds to a particular reference designator.",
        "rows": rows,
        "counts": dict(Counter(row["model_mapping_status"] for row in rows)),
    }
    write(SAMPLE / "model-component-mapping.json", value)


def registration():
    photo = ROOT / "data/photo-model/by_board/ultimainboard/IMG_20261009_222135_1.jpg"
    j22 = read(SAMPLE / "j22-photo-source-link.json")
    landmarks = [{
        "id": "j22_pin_1",
        "kind": "connector_contact_and_pin_1_triangle",
        "photo_center_px": [924.0, 50.0],
        "board_coordinate": {"frame": "J22 footprint local", "value_mm": [0.0, 0.0]},
        "review_status": "reviewed_local_correspondence",
        "evidence": "J22 silkscreen plus pin-1 triangle and imported pad 1 UUID " + j22["pins"][0]["imported_pad_uuid"],
    }]
    candidates = [
        ("board_top_left_mounting_hole", [80, 66]), ("board_top_right_mounting_hole", [1340, 68]),
        ("board_bottom_left_mounting_hole", [70, 3035]), ("board_bottom_right_mounting_hole", [1330, 3025]),
    ]
    for identifier, point in candidates:
        landmarks.append({"id": identifier, "kind": "mounting_hole_candidate", "photo_center_px": point, "board_coordinate": None, "review_status": "unverified_candidate", "reason": "Photo position is visible, but no independently reviewed board-coordinate correspondence has been established."})
    value = {
        "schema_version": 1,
        "photo": {"path": str(photo.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(photo), "coordinate_units": "pixels, origin upper left"},
        "board": {"coordinate_units": "mm in imported KiCad board coordinates", "registration_status": "not_established"},
        "landmarks": landmarks,
        "transform": None,
        "transform_status": "withheld",
        "reason": "One reviewed local J22 correspondence cannot estimate or validate a 2D projective transform, camera pose, scale, or lens distortion. Candidate holes need independent CAD-coordinate review and a reprojection-error check.",
        "acceptance_requirements": {"minimum_reviewed_non_collinear_landmarks": 4, "required": ["board-coordinate IDs", "photo pixels at original resolution", "camera/lens assumption", "fit method", "per-landmark reprojection error in pixels", "visual overlay review"]},
    }
    write(SAMPLE / "ar-registration.json", value)


def board_index():
    items = [
        ("ESP32 DevKit 30-pin", "esp32-devkit-30pin", "physical revision unverified", "community clone reference; physical board match unconfirmed", "native KiCad clone PCB, board-only STEP/GLB, separate assembly STEP/GLB", "reviewed photo-to-CAD registration and exact physical revision"),
        ("NodeMCU DevKit V1.0", "esp8266-nodemcu-reference", "source revision V1.0; photographed USB-UART variant unverified", "source reference differs from some photographed boards", "Altium PCB, four Gerber archives, 17 extracted STEP models", "exact physical variant, native import/export, photo registration"),
        ("FRDM-MCXN236", "nxp-frdm-mcxn236", "official source Rev C; physical revision unverified", "photographed model is MCXN236", "Allegro BRD, KiCad import, board-only STEP/GLB, Gerber/drill", "physical revision and registration; import padstack review"),
        ("FRDM-MCXN947", "nxp-frdm-mcxn947", "source Rev C", "different-board reference only; must not be assigned to MCXN236 photos", "reference sources only", "not applicable until separately photographed"),
        ("Raspberry Pi 3B", "raspberry-pi-3b-v1.2", "v1.2 family only", "board family inferred; exact physical revision unverified", "reduced schematics; community cluster assembly model only", "exact PCB CAD, standalone board model, licence and photo registration"),
        ("Ultimainboard", "ultimainboard-2.1.4", "2.1.4 photographed silkscreen verified", "design revision matches marking; full physical geometry registration pending", "Altium PCB, imported KiCad PCB, 61 STEP streams, assembly STEP/GLB, board-only STEP/GLB", "four or more reviewed board/photo landmarks and transform validation"),
    ]
    value = {"schema_version": 1, "boards": [dict(zip(["name", "path", "revision", "verification_status", "available_cad_models", "missing_inputs"], item)) for item in items]}
    write(ROOT / "docs/ALL_BOARD_INDEX.json", value)


if __name__ == "__main__":
    materialization_manifest()
    model_mapping()
    registration()
    board_index()
