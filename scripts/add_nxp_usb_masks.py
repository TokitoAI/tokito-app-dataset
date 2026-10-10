"""Add two reviewed USB receptacle masks to the NXP phone reference.

The silhouettes come from the 2026-10-10 iQOO photograph. Refdes and source
CAD links remain candidates because the photographed PCB revision is unverified.
"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
IMAGE_REL = Path("data/phone-captures/2026-10-10/IMG_20261010_092203.jpg")
IMAGE_SHA = "00bdc20da4286033a2c2f1c1d146ee3ece21be8ca322f4d33b7fdc8738038170"
IMAGE_WIDTH, IMAGE_HEIGHT = 3072, 4096
MASKS = [
    {
        "refdes": "J11",
        "class_name": "usb_connector",
        "source_component_id": "nxp-frdm-mcxn236:C:J11",
        "polygon": [[1281, 406], [1294, 397], [1507, 390], [1532, 402], [1544, 421], [1542, 642], [1551, 659], [1538, 674], [1302, 681], [1284, 668], [1278, 648], [1278, 432]],
        "crop": [1180, 300, 1990, 720],
        "evidence": "USB4085-GF-A Type-C receptacle silhouette reviewed in original-pixel crop; left port maps to J11 by Rev C placement relative to mounting holes. Board revision and installed order code are not independently confirmed.",
    },
    {
        "refdes": "J10",
        "class_name": "usb_connector",
        "source_component_id": "nxp-frdm-mcxn236:C:J10",
        "polygon": [[1701, 383], [1718, 373], [1938, 367], [1957, 380], [1965, 401], [1962, 630], [1970, 650], [1957, 670], [1720, 678], [1703, 664], [1698, 642], [1698, 405]],
        "crop": [1180, 300, 1990, 720],
        "evidence": "USB4085-GF-A Type-C receptacle silhouette reviewed in original-pixel crop; right port maps to J10 by Rev C placement relative to mounting holes. Board revision and installed order code are not independently confirmed.",
    },
]


def main():
    image_path = ROOT / IMAGE_REL
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
    if digest != IMAGE_SHA:
        raise SystemExit("NXP source photograph hash changed")
    with Image.open(image_path) as image:
        if ImageOps.exif_transpose(image).size != (IMAGE_WIDTH, IMAGE_HEIGHT):
            raise SystemExit("NXP source photograph dimensions changed")

    mask_path = ROOT / "annotations/ar-instance-masks.json"
    scan_path = ROOT / "data/phone-captures/2026-10-10/reviewed-scan-references.json"
    masks = json.loads(mask_path.read_text(encoding="utf-8"))
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    template = next(t for t in scan["templates"] if t["image_path"] == IMAGE_REL.as_posix())
    known_mask_ids = {m["instance_id"] for m in masks["masks"]}
    known_label_ids = {l["id"] for t in scan["templates"] for l in t["labels"]}

    for item in MASKS:
        instance_id = f"IMG_20261010_092203.jpg:{item['refdes']}"
        if instance_id in known_mask_ids or instance_id in known_label_ids:
            raise SystemExit(f"Annotation already exists: {instance_id}")
        points = item["polygon"]
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        bbox = [min(xs) / IMAGE_WIDTH, min(ys) / IMAGE_HEIGHT, max(xs) / IMAGE_WIDTH, max(ys) / IMAGE_HEIGHT]
        crop = item["crop"]
        mask = {
            "image_path": IMAGE_REL.as_posix(),
            "image_sha256": IMAGE_SHA,
            "image_width": IMAGE_WIDTH,
            "image_height": IMAGE_HEIGHT,
            "instance_id": instance_id,
            "class_name": item["class_name"],
            "observed_reference_designator": item["refdes"],
            "observed_marking_family": None,
            "polygon_xy_pixels": points,
            "boundary_scope": "visible connector package and shield body; excludes PCB, silkscreen, and cast shadow",
            "review_status": "visually_reviewed_body_polygon",
            "review_evidence": f"Original EXIF-upright photo and original-pixel crop x={crop[0]}..{crop[2]},y={crop[1]}..{crop[3]} reviewed. {item['evidence']}",
            "boundary_uncertainty_pixels": 8,
            "source_component_id": item["source_component_id"],
            "source_mapping_status": "source_candidate_photographed_revision_unverified",
            "installed_order_code_confirmed": False,
        }
        label = {
            "id": instance_id,
            "label": f"{item['refdes']} — GCT USB4085-GF-A USB Type-C receptacle [Rev C source candidate]",
            "kind": "part",
            "bbox_xyxy_normalized": bbox,
            "identity_status": "visually_reviewed_connector_type_source_candidate_revision_unverified",
            "source": {
                "observed_refdes": item["refdes"],
                "observed_marking": None,
                "evidence": item["evidence"],
                "source_component_id": item["source_component_id"],
                "source_revision": "C",
                "installed_order_code_confirmed": False,
            },
        }
        masks["masks"].append(mask)
        template["labels"].append(label)

    mask_path.write_text(json.dumps(masks, indent=2) + "\n", encoding="utf-8")
    scan_path.write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"added": [f"IMG_20261010_092203.jpg:{m['refdes']}" for m in MASKS], "coverage": "partial_visible_component_bodies", "release_eligible": False}, indent=2))


if __name__ == "__main__":
    main()
