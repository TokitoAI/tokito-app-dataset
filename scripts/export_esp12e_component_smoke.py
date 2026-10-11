"""Export the one complete-reviewed ESP-12E frame for segmentation smoke tests.

This creates standard YOLO segmentation files for a single known specimen. It
is an integration fixture, not a train/validation/test dataset and not a route
to model-quality claims.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "annotations/esp8266-frame-component-complete-review.json"
OUT = ROOT / "data/photo-model/component-smoke-esp12e"
IMAGE_REL = "data/phone-captures/2026-10-10/IMG_20261010_092221.jpg"
MODEL_CLASSES = [
    "ic_package", "chip_passive", "connector", "rf_module",
    "switch", "crystal", "discrete_semiconductor", "inductor",
]
SOURCE_TO_MODEL_CLASS = {
    "integrated_circuit": "ic_package",
    "capacitor": "chip_passive",
    "resistor": "chip_passive",
    "usb_connector": "connector",
    "rf_shield": "rf_module",
    "switch": "switch",
    "three_terminal_package": "discrete_semiconductor",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export():
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    image = ROOT / IMAGE_REL
    if review.get("coverage") != "complete_visible_instances" or review.get("training_export_eligible") is not True:
        raise ValueError("Source review is not explicitly complete and training eligible")
    if review.get("evaluation_valid") is not False:
        raise ValueError("Smoke export must not be relabeled as a valid evaluation")
    if review.get("image_path") != IMAGE_REL or sha(image) != review.get("image_sha256"):
        raise ValueError("Image path/hash does not match the reviewed source")
    with Image.open(image) as im:
        width, height = im.size
    if (width, height) != (review.get("image_width"), review.get("image_height")):
        raise ValueError("Source image dimensions differ from the reviewed annotation")

    masks = review.get("masks", [])
    eligible = [m for m in masks if m.get("training_export_eligible", True) is True]
    excluded = [m.get("instance_id") for m in masks if m not in eligible]
    unknown_classes = sorted({m["class_name"] for m in eligible} - set(SOURCE_TO_MODEL_CLASS))
    if unknown_classes:
        raise ValueError("No checkpoint taxonomy mapping for: " + ", ".join(unknown_classes))
    class_names = MODEL_CLASSES
    class_ids = {name: index for index, name in enumerate(class_names)}
    label_lines = []
    for row in eligible:
        polygon = row.get("polygon_xy_pixels")
        if not isinstance(polygon, list) or len(polygon) < 3:
            raise ValueError("Invalid polygon for " + str(row.get("instance_id")))
        normalized = []
        for point in polygon:
            if len(point) != 2 or not (0 <= point[0] < width and 0 <= point[1] < height):
                raise ValueError("Out-of-image polygon point for " + str(row.get("instance_id")))
            normalized.extend((point[0] / width, point[1] / height))
        model_class = SOURCE_TO_MODEL_CLASS[row["class_name"]]
        label_lines.append(str(class_ids[model_class]) + " " + " ".join(f"{v:.8f}" for v in normalized))

    image_dir = OUT / "images"
    label_dir = OUT / "labels"
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    image_out = image_dir / Path(IMAGE_REL).name
    label_out = label_dir / (Path(IMAGE_REL).stem + ".txt")
    image_out.write_bytes(image.read_bytes())
    with label_out.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(label_lines) + "\n")
    data_yaml = OUT / "data.yaml"
    with data_yaml.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(
        "# One-image ESP-12E integration smoke fixture; never use for accuracy claims.\n"
        "path: .\ntrain: images\nval: images\ntest: images\n"
        "names:\n" + "".join(f"  {i}: {name}\n" for i, name in enumerate(class_names)),
        )
    manifest = {
        "schema_version": "1.0",
        "purpose": "single-image YOLO segmentation integration smoke fixture",
        "evaluation_valid": False,
        "production_eligible": False,
        "trainable_model_dataset": False,
        "warning": "train, val and test point to the same single specimen/image for parser/runtime smoke testing only; do not train or report metrics.",
        "board_family": review["board_family"],
        "physical_specimen_id": review["physical_specimen_id"],
        "capture_session_id": review["capture_session_id"],
        "source_annotation": REVIEW.relative_to(ROOT).as_posix(),
        "source_annotation_sha256": sha(REVIEW),
        "image_path": IMAGE_REL,
        "image_sha256": sha(image),
        "export_image_sha256": sha(image_out),
        "export_label_path": label_out.relative_to(ROOT).as_posix(),
        "export_label_sha256": sha(label_out),
        "data_yaml_path": data_yaml.relative_to(ROOT).as_posix(),
        "image_size": [width, height],
        "class_names": class_names,
        "source_to_model_class": SOURCE_TO_MODEL_CLASS,
        "included_instances": len(eligible),
        "excluded_instances": excluded,
        "coverage": review["coverage"],
        "scope": "complete visible component bodies on one ESP-12E top-side image; pins, hidden parts and underside excluded",
    }
    with (OUT / "manifest.json").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(manifest, indent=2) + "\n")
    return manifest


def validate():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    data_yaml = OUT / "data.yaml"
    image = OUT / "images" / Path(IMAGE_REL).name
    label = OUT / "labels" / (Path(IMAGE_REL).stem + ".txt")
    assert manifest["evaluation_valid"] is False and manifest["trainable_model_dataset"] is False
    report = json.loads((ROOT / "models/component-segmentation-v2/REPORT.json").read_text(encoding="utf-8"))
    assert manifest["class_names"] == report["classes"], "Fixture class IDs must match the selected checkpoint"
    assert sha(image) == manifest["image_sha256"] == manifest["export_image_sha256"]
    assert sha(label) == manifest["export_label_sha256"]
    lines = label.read_text(encoding="utf-8").splitlines()
    assert len(lines) == manifest["included_instances"]
    for line in lines:
        values = line.split()
        assert len(values) >= 7 and len(values[1:]) % 2 == 0
        assert 0 <= int(values[0]) < len(manifest["class_names"])
        assert all(0 <= float(v) <= 1 for v in values[1:])
    assert data_yaml.is_file()
    assert "path: .\n" in data_yaml.read_text(encoding="utf-8"), "Dataset YAML must remain portable after cloning"
    return {"valid": True, "images": 1, "labels": len(lines), "classes": len(manifest["class_names"]), "class_ids_match_checkpoint": True, "evaluation_valid": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate an existing export without rewriting it")
    args = parser.parse_args()
    result = validate() if args.check else (export() and validate())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
