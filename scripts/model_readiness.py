"""Audit board -> part -> pin photo-label readiness without training on partial labels.

Run from the repository root: python scripts/model_readiness.py [--json]
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HIERARCHY = ROOT / "data/photo-model/label-hierarchy.json"
MANIFEST = ROOT / "data/photo-model/photo-manifest.json"
SPLIT_REPORT = ROOT / "data/photo-model/yolo-boards/split-report.json"


def audit() -> dict:
    hierarchy = json.loads(HIERARCHY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    split_report = json.loads(SPLIT_REPORT.read_text(encoding="utf-8"))
    images = hierarchy["images"]
    by_name = {image["image_file"]: image for image in images}
    manifest_by_name = {item["file"]: item for item in manifest}
    if len(by_name) != len(images) or set(by_name) != set(manifest_by_name):
        raise ValueError("Hierarchy and photo manifest filenames differ or contain duplicates")

    families: dict[str, dict] = {}
    all_classes: Counter = Counter()
    groups: dict[str, list[dict]] = defaultdict(list)
    source_pin_records = 0
    photo_pin_boxes = 0
    for image in images:
        name = image["image_file"]
        item = manifest_by_name[name]
        if image["image_sha256"] != item["sha256"]:
            raise ValueError(f"Image hash differs for {name}")
        family = image["board"]["family"]
        if family not in families:
            families[family] = {
                "images": 0,
                "splits": Counter(),
                "partial_part_images": 0,
                "unreviewed_part_images": 0,
                "part_boxes": 0,
                "part_boxes_by_split": Counter(),
                "part_classes": Counter(),
                "part_box_review_statuses": Counter(),
                "photo_pin_boxes": 0,
                "source_only_pin_records_under_linked_parts": 0,
            }
        record = families[family]
        record["images"] += 1
        record["splits"][image["split"]] += 1
        if image["part_coverage"] == "partial_major_component_seeds":
            record["partial_part_images"] += 1
        else:
            record["unreviewed_part_images"] += 1
        record["part_boxes"] += len(image["parts"])
        record["part_boxes_by_split"][image["split"]] += len(image["parts"])
        groups[item["candidate_capture_group"]].append(image)
        for part in image["parts"]:
            klass = part["class_name"]
            all_classes[klass] += 1
            record["part_classes"][klass] += 1
            record["part_box_review_statuses"][part["box_review_status"]] += 1
            for pin in part["pins"]:
                if pin.get("photo_bbox_xyxy_pixels") is None:
                    source_pin_records += 1
                    record["source_only_pin_records_under_linked_parts"] += 1
                else:
                    photo_pin_boxes += 1
                    record["photo_pin_boxes"] += 1

    split_leaks = []
    for group, members in sorted(groups.items()):
        active_splits = {image["split"] for image in members if image["split"] in ("train", "val")}
        if len(active_splits) > 1:
            split_leaks.append(group)
    if split_leaks:
        raise ValueError(f"Crop/original capture groups cross train/val: {split_leaks}")

    for record in families.values():
        record["splits"] = dict(sorted(record["splits"].items()))
        record["part_classes"] = dict(sorted(record["part_classes"].items()))
        record["part_boxes_by_split"] = dict(sorted(record["part_boxes_by_split"].items()))
        record["part_box_review_statuses"] = dict(sorted(record["part_box_review_statuses"].items()))

    return {
        "source": str(HIERARCHY.relative_to(ROOT)).replace("\\", "/"),
        "total_images": len(images),
        "board_training_split": split_report["counts"],
        "capture_groups": len(groups),
        "crop_group_train_val_leaks": split_leaks,
        "families": dict(sorted(families.items())),
        "part_class_distribution": dict(sorted(all_classes.items())),
        "total_part_boxes": sum(all_classes.values()),
        "validation_part_boxes": sum(record["part_boxes_by_split"].get("val", 0) for record in families.values()),
        "source_only_pin_records_under_linked_parts": source_pin_records,
        "photo_pin_boxes": photo_pin_boxes,
        "readiness": {
            "board_family_diagnostic_training": True,
            "part_detector_complete_supervision": False,
            "photo_pin_annotation_seed_available": photo_pin_boxes > 0,
            "photo_pin_detector_training": False,
            "independent_specimen_test": False,
        },
        "limits": [
            "All part-labelled images have partial major-component coverage; unlabeled visible parts cannot be treated as negatives.",
            "Source schematic pin records are electrical metadata, not photo pin boxes.",
            "Capture-group separation prevents direct crop/original leakage, but all images come from one photo session and one physical specimen per family.",
            "The current validation split has no ESP32 image and cannot estimate ESP32 performance.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    report = audit()
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print(f"Photos: {report['total_images']} | capture groups: {report['capture_groups']}")
    print(f"Board split: {report['board_training_split']}")
    print("family | photos | partial part photos | part boxes | photo pin boxes | source-only pin records")
    for family, data in report["families"].items():
        print(f"{family} | {data['images']} | {data['partial_part_images']} | {data['part_boxes']} | {data['photo_pin_boxes']} | {data['source_only_pin_records_under_linked_parts']}")
    print("Part classes:", json.dumps(report["part_class_distribution"], sort_keys=True))
    print("Partial part boxes on validation photos:", report["validation_part_boxes"])
    print("Training readiness:", json.dumps(report["readiness"], sort_keys=True))
    print("Crop/original train-val leakage groups:", len(report["crop_group_train_val_leaks"]))
    for limit in report["limits"]:
        print("LIMIT:", limit)


if __name__ == "__main__":
    main()
