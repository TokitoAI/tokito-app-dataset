"""Audit physical multi-view captures without promoting unreviewed photos.

This report checks the real-camera evidence required for board-to-component AR
registration. Synthetic renders are intentionally excluded from capture counts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "annotations/multiview-capture-review.json"
DEFAULT_OUTPUT = ROOT / "results/multiview-capture-coverage-audit.json"
BOARD_NAMES = json.loads(
    (ROOT / "data/photo-model/board-yolo11m-finetune-experiment/training-report.json")
    .read_text(encoding="utf-8")
)["class_names"]


def audit(source: Path) -> dict:
    source = source.resolve()
    manifest = json.loads(source.read_text(encoding="utf-8"))
    required = manifest["required_view_slots"]
    captures = manifest.get("captures", [])
    by_specimen: dict[str, list[dict]] = {}
    for capture in captures:
        if capture.get("capture_role", "physical_photo") != "physical_photo":
            continue
        specimen = capture.get("specimen_id")
        if specimen:
            by_specimen.setdefault(specimen, []).append(capture)

    boards = []
    for specimen, views in sorted(by_specimen.items()):
        verified = {
            view["view_slot"]
            for view in views
            if view.get("view_slot") in required
            and view.get("camera_calibration_id")
            and view.get("board_to_camera_pose") is not None
            and view.get("review_status") == "reviewed"
        }
        boards.append(
            {
                "specimen_id": specimen,
                "board_family": views[0].get(
                    "board_family", BOARD_NAMES.get(str(views[0].get("class_id")))
                ),
                "physical_capture_records": len(views),
                "verified_view_slots": sorted(verified),
                "missing_view_slots": [slot for slot in required if slot not in verified],
                "flip_sequence_verified": any(
                    seq.get("specimen_id") == specimen
                    and seq.get("review_status") == "reviewed"
                    and seq.get("continuous_video_sha256")
                    for seq in manifest.get("flip_sequences", [])
                ),
            }
        )

    complete = bool(boards) and all(
        not board["missing_view_slots"] and board["flip_sequence_verified"]
        for board in boards
    )
    return {
        "schema_version": "1.0",
        "source_manifest": (
            source.relative_to(ROOT).as_posix()
            if source.is_relative_to(ROOT)
            else "<test-fixture>"
        ),
        "required_view_slots": required,
        "physical_specimens": len(boards),
        "complete_physical_multiview_specimens": sum(
            not b["missing_view_slots"] and b["flip_sequence_verified"] for b in boards
        ),
        "physical_multiview_complete": complete,
        "release_eligible": complete,
        "boards": boards,
        "limits": [
            "Only individually reviewed physical-photo records with calibration and pose count.",
            "Synthetic renders and unreviewed gallery photos do not count as physical coverage.",
            "A reviewed continuous flip video with a content hash is required per specimen.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if not source.is_relative_to(ROOT) or not output.is_relative_to(ROOT):
        raise ValueError("Source and output must stay inside the repository")
    result = audit(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "physical_specimens": result["physical_specimens"],
        "complete_physical_multiview_specimens": result["complete_physical_multiview_specimens"],
        "physical_multiview_complete": result["physical_multiview_complete"],
    }))


if __name__ == "__main__":
    main()
