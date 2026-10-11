"""Audit calibrated multiview coverage and inventory unregistered captures."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "annotations/multiview-capture-review.json"
DEFAULT_OUTPUT = ROOT / "results/multiview-capture-coverage-audit.json"
EVIDENCE_SOURCES = {
    "iqoo_gallery_view_review": ROOT / "data/phone-captures/2026-10-11/gallery/view-review.json",
    "physical_followup_video_manifest": ROOT / "data/video-captures/2026-10-10/physical-view-followup/manifest.json",
    "additional_flip_video_manifest": ROOT / "data/video-captures/2026-10-10/physical-view-followup/additional-flip-clips/manifest.json",
    "nxp_additional_video_manifest": ROOT / "data/video-captures/2026-10-10/physical-view-followup/additional-board-views/nxp-keyframes/manifest.json",
}
BOARD_NAMES = json.loads(
    (ROOT / "data/photo-model/board-yolo11m-finetune-experiment/training-report.json")
    .read_text(encoding="utf-8")
)["class_names"]


def payload_sha256(path: Path) -> str:
    """Return actual payload hash, reading Git LFS object ID in pointer checkouts."""
    raw = path.read_bytes()
    if raw.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        for line in raw.decode("ascii").splitlines():
            if line.startswith("oid sha256:"):
                return line.split(":", 1)[1]
    return hashlib.sha256(raw).hexdigest()


def verify_evidence(path_value: str, expected_hash: str | None) -> dict:
    path = ROOT / path_value
    exists = path.is_file()
    observed = payload_sha256(path) if exists else None
    return {
        "path": path_value,
        "exists": exists,
        "declared_sha256": expected_hash,
        "observed_payload_sha256": observed,
        "hash_verified": bool(expected_hash and observed == expected_hash),
    }


def inventory_unregistered_evidence() -> list[dict]:
    """Record later real captures without inventing specimen or pose registration."""
    inventory = []
    source = EVIDENCE_SOURCES["iqoo_gallery_view_review"]
    gallery = json.loads(source.read_text(encoding="utf-8"))
    gallery_rows = []
    for row in gallery.get("images", []):
        gallery_rows.append({
            **verify_evidence(row["image_path"], row.get("image_sha256")),
            "board_family": row.get("board_family"),
            "visible_face": row.get("visible_face"),
            "physical_specimen_id": row.get("physical_specimen_id"),
            "camera_intrinsics_registered": row.get("camera_intrinsics_registered", False),
            "metric_pose_verified": row.get("metric_pose_verified", False),
        })
    inventory.append({
        "source_manifest": source.relative_to(ROOT).as_posix(),
        "record_count": len(gallery_rows),
        "records": gallery_rows,
        "interpretation": "Board/face review only; specimen IDs and metric poses are absent.",
    })

    for key, collection_name, evidence_kind in (
        ("physical_followup_video_manifest", "recordings", "reviewed_video_pan"),
        ("additional_flip_video_manifest", "recordings", "sampled_flip_video"),
    ):
        source = EVIDENCE_SOURCES[key]
        doc = json.loads(source.read_text(encoding="utf-8"))
        rows = []
        for row in doc.get(collection_name, []):
            rows.append({
                **verify_evidence(row["path"], row.get("sha256")),
                "evidence_kind": evidence_kind,
                "board_family": row.get("board_family"),
                "observed_views": row.get("observed_views", []),
                "underside_seen": row.get("underside_seen", False),
                "four_oblique_sides_seen": row.get("four_oblique_sides_seen", False),
                "continuous_flip_video_present": row.get("continuous_flip_video_present", row.get("continuous_rotate_flip_seen", False)),
                "continuous_flip_verified": row.get("continuous_flip_verified", False),
                "physical_specimen_id": row.get("physical_specimen_id"),
            })
        inventory.append({
            "source_manifest": source.relative_to(ROOT).as_posix(),
            "record_count": len(rows),
            "records": rows,
            "interpretation": "Video evidence is inventoried, but family-only records do not establish specimen identity or metric camera pose.",
        })

    source = EVIDENCE_SOURCES["nxp_additional_video_manifest"]
    doc = json.loads(source.read_text(encoding="utf-8"))
    video = doc["source_video"]
    frame_rows = []
    for frame in doc.get("keyframes", []):
        frame_rows.append({
            **verify_evidence(frame["image_path"], frame.get("image_sha256")),
            "board_family": frame.get("board_family_hint"),
            "view_slot": "top_face_keyframe",
            "physical_specimen_id": frame.get("physical_specimen_id"),
            "metric_pose_verified": False,
        })
    inventory.append({
        "source_manifest": source.relative_to(ROOT).as_posix(),
        "record_count": len(frame_rows),
        "source_video": verify_evidence(video["path"], video.get("sha256")),
        "records": frame_rows,
        "interpretation": "One reviewed NXP top-face keyframe; no calibrated pose or added underside/oblique slot.",
    })
    return inventory


def audit(source: Path) -> dict:
    source = source.resolve()
    manifest = json.loads(source.read_text(encoding="utf-8"))
    required = manifest["required_view_slots"]
    captures = manifest.get("captures", [])
    by_specimen: dict[str, list[dict]] = {}
    for capture in captures:
        if capture.get("capture_role") in {"synthetic", "synthetic_render", "render"}:
            continue
        specimen = capture.get("specimen_id")
        if specimen:
            by_specimen.setdefault(specimen, []).append(capture)

    boards = []
    for specimen, views in sorted(by_specimen.items()):
        recorded = {view["view_slot"] for view in views if view.get("view_slot") in required}
        verified = {
            view["view_slot"] for view in views
            if view.get("view_slot") in required
            and view.get("camera_calibration_id")
            and view.get("board_to_camera_pose") is not None
            and view.get("review_status") == "reviewed"
        }
        boards.append({
            "specimen_id": specimen,
            "board_family": views[0].get("board_family", BOARD_NAMES.get(str(views[0].get("class_id")))),
            "registered_pose_review_records": len(views),
            "recorded_view_slots_without_pose_claim": sorted(recorded - verified),
            "pose_verified_view_slots": sorted(verified),
            "missing_pose_verified_view_slots": [slot for slot in required if slot not in verified],
            "flip_sequence_verified": any(
                seq.get("specimen_id") == specimen
                and seq.get("review_status") == "reviewed"
                and seq.get("continuous_video_sha256")
                for seq in manifest.get("flip_sequences", [])
            ),
        })

    complete = bool(boards) and all(
        not board["missing_pose_verified_view_slots"] and board["flip_sequence_verified"]
        for board in boards
    )
    return {
        "schema_version": "1.1",
        "source_manifest": source.relative_to(ROOT).as_posix() if source.is_relative_to(ROOT) else "<test-fixture>",
        "required_view_slots": required,
        "physical_specimens": len(boards),
        "complete_physical_multiview_specimens": sum(
            not board["missing_pose_verified_view_slots"] and board["flip_sequence_verified"] for board in boards
        ),
        "physical_multiview_complete": complete,
        "release_eligible": complete,
        "boards": boards,
        "unregistered_capture_evidence": inventory_unregistered_evidence() if source.is_relative_to(ROOT) else [],
        "limits": [
            "Only individually reviewed records with camera calibration and board-to-camera pose count toward verified view slots.",
            "Later gallery/video captures are hash-inventoried but not linked to a specimen without explicit source evidence.",
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
        "unregistered_capture_sources": len(result["unregistered_capture_evidence"]),
    }))


if __name__ == "__main__":
    main()
