"""Validate reviewed component-mask files before they enter a YOLO pipeline.

This checks annotation integrity only. Partial review masks remain unsuitable
for standard YOLO training because unlabelled visible objects become background.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image


DEFAULT_FILES = (
    "annotations/ar-instance-masks.json",
    "annotations/esp32-dense-component-review.json",
    "annotations/esp8266-component-mask-review.json",
    "annotations/esp8266-dense-component-review.json",
    "annotations/esp8266-video-component-review.json",
    "annotations/nxp-dense-component-review.json",
    "annotations/ultimainboard-specimen-component-masks.json",
    "annotations/ultimainboard-dense-component-review.json",
)


def validate_file(annotation_path, repo_root):
    annotation_path = Path(annotation_path)
    data = json.loads(annotation_path.read_text(encoding="utf-8"))
    errors = []
    masks = data.get("masks", data.get("instances", []))
    if not isinstance(masks, list):
        return {"file": str(annotation_path), "masks": 0, "errors": ["masks/instances must be a list"], "trainable": False}

    seen = set()
    image_cache = {}
    for index, mask in enumerate(masks):
        label = mask.get("instance_id", f"row {index}")
        image_value = mask.get("image_path") or data.get("image_path") or data.get("photo", {}).get("path")
        if not image_value:
            errors.append(f"{label}: image path is missing")
            continue
        image_path = Path(image_value)
        if not image_path.is_absolute():
            image_path = repo_root / image_path
        if not image_path.is_file():
            errors.append(f"{label}: image does not exist: {image_path}")
            continue

        cache_key = image_path.resolve()
        if cache_key not in image_cache:
            image_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
            try:
                with Image.open(image_path) as image:
                    width, height = image.size
            except OSError:
                errors.append(f"{label}: source image cannot be decoded")
                continue
            image_cache[cache_key] = (image_hash, width, height)
        image_hash, width, height = image_cache[cache_key]
        expected_hash = mask.get("image_sha256") or data.get("image_sha256") or data.get("photo", {}).get("sha256")
        if not expected_hash:
            errors.append(f"{label}: image SHA-256 is missing")
        elif image_hash != expected_hash:
            errors.append(f"{label}: image SHA-256 mismatch")

        if mask.get("image_width", width) != width or mask.get("image_height", height) != height:
            errors.append(f"{label}: declared image dimensions do not match the source")

        key = (str(image_path.resolve()), label)
        if key in seen:
            errors.append(f"{label}: duplicate instance ID for the same image")
        seen.add(key)

        polygon = mask.get("polygon_xy_pixels")
        if not isinstance(polygon, list) or len(polygon) < 3:
            errors.append(f"{label}: polygon must contain at least three points")
            continue
        for point in polygon:
            if (not isinstance(point, list) or len(point) != 2
                    or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in point)
                    or point[0] < 0 or point[0] >= width or point[1] < 0 or point[1] >= height):
                errors.append(f"{label}: polygon point is invalid or outside the image")
                break
        if not mask.get("class_name"):
            errors.append(f"{label}: YOLO class name is missing")

    declared_complete = data.get("coverage") == "complete_visible_instances"
    eligible_flag = data.get("training_export_eligible", data.get("release_eligible", False))
    return {
        "file": str(annotation_path),
        "masks": len(masks),
        "errors": errors,
        "trainable": bool(declared_complete and eligible_flag and not errors),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="Annotation JSON files; defaults to the current reviewed mask sets.")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    files = args.files or DEFAULT_FILES
    results = [validate_file(repo_root / path if not Path(path).is_absolute() else path, repo_root)
               for path in files]
    unique_instances = set()
    for path in files:
        path = repo_root / path if not Path(path).is_absolute() else Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        for mask in data.get("masks", data.get("instances", [])):
            image = mask.get("image_path") or data.get("image_path") or data.get("photo", {}).get("path")
            unique_instances.add((image, mask.get("instance_id")))
    print(json.dumps({"results": results,
                      "annotation_record_count": sum(item["masks"] for item in results),
                      "unique_mask_count": len(unique_instances),
                      "integrity_valid": all(not item["errors"] for item in results),
                      "training_ready": all(item["trainable"] for item in results)}, indent=2))
    if any(item["errors"] for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
