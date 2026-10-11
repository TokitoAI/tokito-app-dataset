"""Build conservative ESP32 photo-to-3D selector candidates.

These links enable a UI review of per-component highlighting. They do not
certify the community model as the photographed PCB or establish camera pose.
"""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "annotations/esp32-dense-component-review.json"
COMPONENT_MAP = ROOT / "data/board-sources/esp32-devkit-30pin/ar-source-candidate/input/component-map.json"
ASSET = ROOT / "data/board-sources/esp32-devkit-30pin/ar-source-candidate/esp32-package-candidate.glb"
OUTPUT = ROOT / "data/board-sources/esp32-devkit-30pin/ar-source-candidate/photo-selector-candidates.json"

# Printed photo reference or visually distinct package, never a guessed
# passive value, installed order code, or numeric chip pin.
CANDIDATES = {
    "U1": ("U1", "printed_reference"),
    "U2": ("U2", "printed_reference_and_family_marking"),
    "C5": ("C5", "printed_reference"),
    "RF_MODULE": ("MOD1", "distinct_rf_module_location"),
    "USB": ("J1", "distinct_micro_usb_location"),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    source = json.loads(COMPONENT_MAP.read_text(encoding="utf-8"))
    by_ref = {item["reference"]: item for item in source["components"]}
    rows = []
    for mask in review["masks"]:
        suffix = mask["instance_id"].split(":", 1)[1]
        if suffix not in CANDIDATES:
            continue
        ref, evidence = CANDIDATES[suffix]
        item = by_ref[ref]
        assert item["glb_selector"] and item["needs_3d_body"]
        if evidence.startswith("printed_reference"):
            assert mask["observed_reference_designator"] == ref
        rows.append({
            "image_path": mask["image_path"],
            "image_sha256": mask["image_sha256"],
            "photo_instance_id": mask["instance_id"],
            "polygon_xy_pixels": mask["polygon_xy_pixels"],
            "candidate_reference": ref,
            "candidate_glb_selector": item["glb_selector"],
            "link_evidence": evidence,
            "registration_verified": False,
            "physical_revision_match_verified": False,
            "exact_order_code_verified": False,
        })
    assert len(rows) == len(CANDIDATES) * 3
    result = {
        "schema_version": "1.0",
        "board_family": review["board_family"],
        "physical_specimen_id": review["physical_specimen_id"],
        "source_review_path": REVIEW.relative_to(ROOT).as_posix(),
        "source_review_sha256": sha256(REVIEW),
        "candidate_component_map_path": COMPONENT_MAP.relative_to(ROOT).as_posix(),
        "candidate_component_map_sha256": sha256(COMPONENT_MAP),
        "candidate_glb_path": ASSET.relative_to(ROOT).as_posix(),
        "candidate_glb_sha256": sha256(ASSET),
        "link_status": "review_candidates_only",
        "calibration_eligible": False,
        "production_eligible": False,
        "training_export_eligible": False,
        "coverage": "5_selected_bodies_in_3_front_images;_remaining_69_masks_unmapped",
        "limitations": [
            "Community clone geometry has no verified physical-revision match or measured registration to the photographed specimen.",
            "Reference or distinct-package matching does not validate source BOM values or exact installed part numbers.",
            "No underside, side-angle, camera calibration, pose, or flip correspondence is established here.",
        ],
        "links": rows,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return {"links": len(rows), "distinct_selectors": len({r["candidate_glb_selector"] for r in rows})}


if __name__ == "__main__":
    print(json.dumps(build()))
