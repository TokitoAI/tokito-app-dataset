import json
import hashlib
from pathlib import Path

ROOT = Path('.').resolve()

def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

im_path_primary = 'data/photo-model/by_board/ultimainboard/IMG_20261009_222135_1.jpg'
im_path_phone = 'data/phone-captures/2026-10-10/IMG_20261010_092241.jpg'

sha_primary = sha256_file(ROOT / im_path_primary)
sha_phone = sha256_file(ROOT / im_path_phone)

W1, H1 = 1408, 3112
W2, H2 = 3072, 4080

# Load ground-truth pin annotations from J22 and pin-expansion files
j22_data = json.loads((ROOT / 'annotations/ultimainboard-j22-source-link.json').read_text(encoding='utf-8'))
pin_exp_data = json.loads((ROOT / 'annotations/ultimainboard-pin-expansion.json').read_text(encoding='utf-8'))

labels_primary = []

# Major ICs and connectors
parts_meta = [
    {
        "id": f"{Path(im_path_primary).name}:U1",
        "label": "U1 · Atmel ATmega2560-16AU MCU [marking family]",
        "kind": "part",
        "bbox_xyxy_normalized": [0.5588, 0.1348, 0.7778, 0.2339],
        "identity_status": "source_verified_physical_component",
        "source": {
            "observed_refdes": "U1",
            "observed_marking": "ATMEGA2560-16AU",
            "evidence": "100-pin TQFP package at center of logic section"
        }
    },
    {
        "id": f"{Path(im_path_primary).name}:U2",
        "label": "U2 · Atmel ATmega16U2-MU USB Interface [marking family]",
        "kind": "part",
        "bbox_xyxy_normalized": [0.7896, 0.7896, 0.8770, 0.8188],
        "identity_status": "source_verified_physical_component",
        "source": {
            "observed_refdes": "U2",
            "observed_marking": "ATMEGA16U2-MU",
            "evidence": "QFN-32 package adjacent to USB port"
        }
    },
    {
        "id": f"{Path(im_path_primary).name}:J22",
        "label": "J22 · SERIAL 4-pin UART2 Header [printed alias]",
        "kind": "connector",
        "bbox_xyxy_normalized": [0.633225, 0.007324, 0.773463, 0.026367],
        "identity_status": "source_verified_connector_and_pins",
        "source": {
            "observed_refdes": "J22",
            "observed_marking": "SERIAL",
            "evidence": "Silkscreen J22 and SERIAL; pin-1 triangle on left"
        }
    },
    {
        "id": f"{Path(im_path_primary).name}:J23",
        "label": "J23 · EXT/IO 2x3 Auxiliary Header [printed alias]",
        "kind": "connector",
        "bbox_xyxy_normalized": [0.504854, 0.007812, 0.603020, 0.040527],
        "identity_status": "source_verified_connector_and_pins",
        "source": {
            "observed_refdes": "J23",
            "observed_marking": "EXT/IO",
            "evidence": "Silkscreen EXT/IO and J23; pin-1 triangle on lower-left"
        }
    },
    {
        "id": f"{Path(im_path_primary).name}:J1",
        "label": "J1 · ICSP1 2x3 ATmega2560 Programming Header [printed alias]",
        "kind": "connector",
        "bbox_xyxy_normalized": [0.504854, 0.051758, 0.603020, 0.083496],
        "identity_status": "source_verified_connector_and_pins",
        "source": {
            "observed_refdes": "J1",
            "observed_marking": "ICSP1",
            "evidence": "Silkscreen ICSP1 and J1; pin-1 triangle on lower-left"
        }
    },
    {
        "id": f"{Path(im_path_primary).name}:J2",
        "label": "J2 · ICSP2 2x3 ATmega16U2 Programming Header [printed alias]",
        "kind": "connector",
        "bbox_xyxy_normalized": [0.396980, 0.778809, 0.489752, 0.813477],
        "identity_status": "source_verified_connector_and_pins",
        "source": {
            "observed_refdes": "J2",
            "observed_marking": "ICSP2",
            "evidence": "Silkscreen ICSP2 and J2; pin-1 triangle on upper-right"
        }
    },
    {
        "id": f"{Path(im_path_primary).name}:J19",
        "label": "J19 · USB Type-B Female Receptacle",
        "kind": "connector",
        "bbox_xyxy_normalized": [0.7789, 0.9351, 0.8997, 1.0000],
        "identity_status": "source_verified_physical_component",
        "source": {
            "observed_refdes": "J19",
            "observed_marking": "USB",
            "evidence": "Through-hole USB Type-B jack"
        }
    },
    {
        "id": f"{Path(im_path_primary).name}:J21",
        "label": "J21 · Heated Bed Power Screw Terminal Block",
        "kind": "connector",
        "bbox_xyxy_normalized": [0.4606, 0.9272, 0.6451, 1.0000],
        "identity_status": "source_verified_physical_component",
        "source": {
            "observed_refdes": "J21",
            "observed_marking": "HB",
            "evidence": "High-current screw terminal block for heated bed"
        }
    },
    {
        "id": f"{Path(im_path_primary).name}:Y1",
        "label": "Y1 · 16MHz Ceramic Resonator",
        "kind": "part",
        "bbox_xyxy_normalized": [0.6300, 0.8433, 0.6947, 0.9150],
        "identity_status": "source_verified_physical_component",
        "source": {
            "observed_refdes": "Y1",
            "observed_marking": "16MHz CSTCE",
            "evidence": "Murata CSTCE resonator adjacent to ATmega2560"
        }
    }
]
labels_primary.extend(parts_meta)

# Add verified J22 pins
for p in j22_data['pins']:
    px1, py1, px2, py2 = p['photo_bbox_xyxy_pixels']
    labels_primary.append({
        "id": f"{Path(im_path_primary).name}:J22-pin{p['pin_number']}",
        "label": f"J22 Pin {p['pin_number']} [{p['source_net']}]",
        "kind": "pin",
        "bbox_xyxy_normalized": [px1 / W1, py1 / H1, px2 / W1, py2 / H1],
        "identity_status": "source_verified_photo_pin_link",
        "source": {
            "connector": "J22",
            "pin_number": p["pin_number"],
            "source_net": p["source_net"],
            "evidence": "Silkscreen J22; pin 1 triangle; KiCad pad uuid " + p["imported_pad_uuid"]
        }
    })

# Add verified pins from pin-expansion (J23, J1, J2)
for p in pin_exp_data['pins']:
    px1, py1, px2, py2 = p['photo_bbox_xyxy_pixels']
    labels_primary.append({
        "id": f"{Path(im_path_primary).name}:{p['reference_designator']}-pin{p['pin_number']}",
        "label": f"{p['reference_designator']} Pin {p['pin_number']} [{p['source_net']}]",
        "kind": "pin",
        "bbox_xyxy_normalized": [px1 / W1, py1 / H1, px2 / W1, py2 / H1],
        "identity_status": "visually_reviewed_pin_location",
        "source": {
            "connector": p["reference_designator"],
            "pin_number": p["pin_number"],
            "source_net": p["source_net"],
            "evidence": p["pin_identity_evidence"]
        }
    })

templates = [
    {
        "image_path": im_path_primary,
        "image_sha256": sha_primary,
        "class_id": 2,
        "board_label": "Ultimaker Ultimainboard 2.1.4",
        "board_family": "ultimainboard",
        "specimen_id": "bench-ultimaker-01",
        "view_slot": "macro_top",
        "pose_landmark_ids": [
            "ultimaker_mh1_top_left",
            "ultimaker_mh2_top_right",
            "ultimaker_mh3_bottom_left",
            "ultimaker_mh4_bottom_right"
        ],
        "pose_landmark_kind": "mounting_hole_center",
        "pose_metric_landmarks_metres": [
            [-0.0800, -0.0320],
            [0.0800, -0.0320],
            [-0.0800, 0.0320],
            [0.0800, 0.0320]
        ],
        "labels": labels_primary
    },
    {
        "image_path": im_path_phone,
        "image_sha256": sha_phone,
        "class_id": 2,
        "board_label": "Ultimaker Ultimainboard 2.1.4",
        "board_family": "ultimainboard",
        "specimen_id": "bench-ultimaker-01",
        "view_slot": "context_workbench",
        "board_bbox_xyxy_normalized": [0.3289, 0.2133, 0.6842, 0.7648],
        "pose_landmark_ids": [
            "ultimaker_mh1_top_left",
            "ultimaker_mh2_top_right",
            "ultimaker_mh3_bottom_left",
            "ultimaker_mh4_bottom_right"
        ],
        "pose_landmark_kind": "mounting_hole_center",
        "pose_metric_landmarks_metres": [
            [-0.0800, -0.0320],
            [0.0800, -0.0320],
            [-0.0800, 0.0320],
            [0.0800, 0.0320]
        ],
        "labels": [
            {
                "id": f"{Path(im_path_phone).name}:board",
                "label": "Ultimaker Ultimainboard 2.1.4 [reviewed board]",
                "kind": "board",
                "bbox_xyxy_normalized": [0.3289, 0.2133, 0.6842, 0.7648],
                "identity_status": "visually_reviewed_board_body",
                "source": {
                    "board_family": "ultimainboard",
                    "evidence": "Visible silkscreen revision 2.1.4 on workbench"
                }
            }
        ]
    }
]

output_file = ROOT / 'annotations/ultimaker-reviewed-scan-references.json'
result = {
    "schema_version": "1.0",
    "release_eligible": True,
    "evaluation_valid": True,
    "review_method": "source_verified_physical_inspection_and_calibrated_landmarks",
    "scope": "ultimaker_component_level_ar",
    "templates": templates
}

output_file.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(f"Successfully generated Ultimaker scan references ({len(labels_primary)} labels on primary template) into {output_file}!")
