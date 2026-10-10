"""Verify ingested video/keyframe provenance without claiming label accuracy."""
import hashlib
import json
from pathlib import Path

from PIL import Image


def validate(root, manifest_path):
    root = Path(root).resolve()
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    def checked_path(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Asset escapes repository")
        return path

    def digest(path):
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    source = manifest["source_video"]
    video = checked_path(source["path"])
    assert video.stat().st_size == source["bytes"], "Video size mismatch"
    assert digest(video) == source["sha256"], "Video digest mismatch"
    assert manifest["all_frames_share_split_group"] is True
    previous_index = -1
    previous_pts = -1.0
    for frame in manifest["keyframes"]:
        path = checked_path(frame["image_path"])
        assert digest(path) == frame["image_sha256"], "Frame digest mismatch"
        with Image.open(path) as image:
            assert image.size == (frame["image_width"], frame["image_height"])
            image.verify()
        assert frame["source_video_sha256"] == source["sha256"]
        assert frame["physical_specimen_id"] == manifest["physical_specimen_id"]
        assert frame["capture_session_id"] == manifest["capture_session_id"]
        index, pts = frame["source_frame_index"], frame["source_pts_seconds"]
        assert previous_index < index < manifest["decoded_frame_count"]
        assert previous_pts < pts < float(manifest["video"]["duration"])
        if any(frame[key] == "not_reviewed" for key in
               ("board_box_review_status", "part_review_status", "pin_review_status")):
            assert frame["training_export_eligible"] is False
        previous_index, previous_pts = index, pts
    review_path = Path(manifest_path).parent / "reviewed-component-masks.json"
    if review_path.exists():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        frame = next(item for item in manifest["keyframes"]
                     if item["image_path"] == review["image_path"])
        assert review["image_sha256"] == frame["image_sha256"]
        assert review["physical_specimen_id"] == manifest["physical_specimen_id"]
        assert review["capture_session_id"] == manifest["capture_session_id"]
        assert review["training_export_eligible"] is False
        assert review["production_eligible"] is False
        width, height = review["image_width"], review["image_height"]
        assert (width, height) == (frame["image_width"], frame["image_height"])
        identities = set()
        for mask in review["masks"]:
            assert mask["instance_id"] not in identities
            identities.add(mask["instance_id"])
            points = mask["polygon_xy_pixels"]
            assert len(points) >= 3
            assert all(0 <= x < width and 0 <= y < height for x, y in points)
            area = abs(sum(x * points[(i + 1) % len(points)][1]
                           - y * points[(i + 1) % len(points)][0]
                           for i, (x, y) in enumerate(points))) / 2
            assert area > 0
        assert review["pin_parent_board_id"] == manifest["physical_specimen_id"]
        for pin in review["pin_annotations"]:
            assert pin["instance_id"] not in identities
            identities.add(pin["instance_id"])
            x, y = pin["center_xy_pixels"]
            radius = pin["visible_radius_pixels"]
            assert radius > 0 and radius <= x < width - radius
            assert radius <= y < height - radius
            assert pin["printed_alias"]
    module_path = Path(manifest_path).parent / "reviewed-module-contacts.json"
    if module_path.exists():
        module = json.loads(module_path.read_text(encoding="utf-8"))
        frame = next(item for item in manifest["keyframes"]
                     if item["image_path"] == module["image_path"])
        assert module["image_sha256"] == frame["image_sha256"]
        assert module["physical_specimen_id"] == manifest["physical_specimen_id"]
        assert module["capture_session_id"] == manifest["capture_session_id"]
        assert module["training_export_eligible"] is False
        assert module["calibration_eligible"] is False
        contacts = module["contacts"]
        assert [pin["source_module_pin_number"] for pin in contacts] == list(range(1, 23))
        assert len({pin["instance_id"] for pin in contacts}) == 22
        for pin in contacts:
            x, y = pin["center_xy_pixels"]
            assert 0 <= x < frame["image_width"] and 0 <= y < frame["image_height"]
            assert pin["parent_component_id"] == "bench-esp8266-01:esp12e_module"
            assert pin["source_pin_name"]
        assert len(module["source"]["pdf_sha256"]) == 64
        assert module["carrier_header_mapping_verified"] is False
    return len(manifest["keyframes"])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    count = validate(Path(__file__).resolve().parents[1], args.manifest)
    print(f"Verified source video and {count} grouped keyframes; labels remain separately reviewed.")
