"""Build a conservative, per-image component annotation backlog.

The report combines existing reviewed polygon masks and their explicit
coverage audits. It never infers completeness from mask counts or promotes
partial frames into a YOLO training export.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "annotations/ar-instance-masks.json",
    "annotations/esp32-dense-component-review.json",
    "annotations/esp8266-component-mask-review.json",
    "annotations/esp8266-dense-component-review.json",
    "annotations/esp8266-video-component-review.json",
    "annotations/nxp-dense-component-review.json",
    "annotations/ultimainboard-specimen-component-masks.json",
    "annotations/ultimainboard-dense-component-review.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_records(path: Path) -> tuple[dict, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("masks", data.get("instances", []))
    if not isinstance(records, list):
        return data, []
    return data, records


def build() -> dict:
    frames: dict[str, dict] = {}
    source_counts: Counter = Counter()
    for rel in SOURCES:
        source_path = ROOT / rel
        data, masks = load_records(source_path)
        family = data.get("board_family")
        metadata = data.get("images", data.get("image_reviews", data.get("image_coverage_reviews", [])))
        metadata_by_path = {row.get("image_path"): row for row in metadata if isinstance(row, dict) and row.get("image_path")}
        default_path = data.get("image_path") or (data.get("photo") or {}).get("path")
        for mask in masks:
            image = mask.get("image_path") or default_path or (data.get("photo") or {}).get("path")
            if not image:
                continue
            frame = frames.setdefault(image, {
                "image_path": image,
                "board_family_candidates": set(),
                "mask_count": 0,
                "classes": Counter(),
                "instance_ids": set(),
                "review_statuses": Counter(),
                "source_files": set(),
                "declared_coverage": set(),
                "training_flags": [],
                "evaluation_flags": [],
                "image_sha256_values": set(),
                "remaining_review": set(),
                "capture_groups": set(),
            })
            if family:
                frame["board_family_candidates"].add(family)
            frame["mask_count"] += 1
            frame["classes"][mask.get("class_name", "unknown")] += 1
            frame["instance_ids"].add(mask.get("instance_id", ""))
            if mask.get("review_status"):
                frame["review_statuses"][mask["review_status"]] += 1
            frame["source_files"].add(rel)
            if data.get("coverage"):
                frame["declared_coverage"].add(data["coverage"])
            frame["training_flags"].append(mask.get("training_export_eligible", data.get("training_export_eligible", data.get("training_eligible", False))))
            frame["evaluation_flags"].append(data.get("evaluation_valid", False))
            digest = mask.get("image_sha256") or data.get("image_sha256") or (data.get("photo") or {}).get("sha256")
            if digest:
                frame["image_sha256_values"].add(digest)
            for key in ("capture_session_id", "physical_specimen_id", "capture_group_id", "same_specimen_split_group"):
                if mask.get(key) or data.get(key):
                    frame["capture_groups"].add(str(mask.get(key) or data.get(key)))
            source_counts[rel] += 1

        # Add explicitly reviewed image rows, including those with zero masks.
        for image, meta in metadata_by_path.items():
            frame = frames.setdefault(image, {
                "image_path": image,
                "board_family_candidates": set(), "mask_count": 0,
                "classes": Counter(), "instance_ids": set(), "review_statuses": Counter(),
                "source_files": set(), "declared_coverage": set(), "training_flags": [],
                "evaluation_flags": [], "image_sha256_values": set(),
                "remaining_review": set(), "capture_groups": set(),
            })
            if family:
                frame["board_family_candidates"].add(family)
            frame["source_files"].add(rel)
            if meta.get("coverage"):
                frame["declared_coverage"].add(meta["coverage"])
            for key in ("remaining_review", "unreviewed_visible_instances"):
                frame["remaining_review"].update(meta.get(key, []))
            for key in ("capture_session_id", "physical_specimen_id", "capture_group_id"):
                if meta.get(key):
                    frame["capture_groups"].add(str(meta[key]))
            if meta.get("image_sha256"):
                frame["image_sha256_values"].add(meta["image_sha256"])

        # File-level gaps apply to every image reviewed in this annotation.
        for frame in frames.values():
            if rel in frame["source_files"]:
                for key in ("remaining_review", "unreviewed_visible_instances"):
                    frame["remaining_review"].update(data.get(key, []))
                if data.get("coverage"):
                    frame["declared_coverage"].add(data["coverage"])

    rows = []
    for image, frame in frames.items():
        image_path = (ROOT / image).resolve()
        exists = image_path.is_file()
        actual_hash = sha256(image_path) if exists else None
        declared_hashes = sorted(frame["image_sha256_values"])
        hash_matches = exists and (not declared_hashes or declared_hashes == [actual_hash])
        coverage = sorted(frame["declared_coverage"])
        complete_claim = "complete_visible_instances" in coverage
        explicit_training = bool(frame["training_flags"]) and all(x is True for x in frame["training_flags"])
        safe_training = bool(complete_claim and explicit_training and hash_matches)
        classes = dict(sorted(frame["classes"].items()))
        reviewed = frame["mask_count"]
        rows.append({
            "image_path": image,
            "board_family_candidates": sorted(frame["board_family_candidates"]),
            "image_exists": exists,
            "image_sha256": actual_hash,
            "declared_sha256_values": declared_hashes,
            "hash_matches": bool(hash_matches),
            "reviewed_mask_count": reviewed,
            "unique_instance_ids": len(frame["instance_ids"]),
            "classes": classes,
            "review_statuses": dict(sorted(frame["review_statuses"].items())),
            "coverage_claims": coverage,
            "remaining_review": sorted(frame["remaining_review"]),
            "capture_groups": sorted(frame["capture_groups"]),
            "annotation_sources": sorted(frame["source_files"]),
            "ordinary_yolo_training_safe": safe_training,
            "next_action": "eligible_for_training_export_review" if safe_training else (
                "repair_hash_or_image_provenance" if not hash_matches else
                "finish_visible_instance_masks_and_review_coverage"
            ),
        })
    rows.sort(key=lambda row: (row["ordinary_yolo_training_safe"], row["reviewed_mask_count"], row["image_path"]))
    summary = Counter(row["next_action"] for row in rows)
    return {
        "schema_version": "1.0",
        "purpose": "Conservative frame-level queue for completing visible component masks; not an annotation or training export.",
        "source_annotation_files": list(SOURCES),
        "unique_frames": len(rows),
        "reviewed_mask_records_before_deduplication": sum(source_counts.values()),
        "frame_action_counts": dict(sorted(summary.items())),
        "ordinary_yolo_trainable_frames": sum(row["ordinary_yolo_training_safe"] for row in rows),
        "rules": [
            "Mask count alone never implies complete frame coverage.",
            "A frame is marked safe only with explicit complete_visible_instances coverage, all explicit training flags true, and verified image provenance.",
            "Partial frames remain queued for complete annotation; do not export them as background-complete YOLO labels.",
        ],
        "frames": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/photo-model/component-review-backlog.json")
    args = parser.parse_args()
    report = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "unique_frames", "reviewed_mask_records_before_deduplication",
        "frame_action_counts", "ordinary_yolo_trainable_frames"
    )} | {"output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
