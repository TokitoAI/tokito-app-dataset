"""Build source-backed relative contact spacing; do not fabricate a full pose frame."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/video-captures/2026-10-10/esp12e-keyframes/reviewed-module-contacts.json'
OUTPUT = ROOT / 'data/ar-alignment/esp12e-module-spacing-constraints.json'


def build():
    source = json.loads(SOURCE.read_text())
    pins = {pin['source_module_pin_number']: pin for pin in source['contacts']}
    rows = []
    for group in (list(range(1, 9)), list(range(9, 15)), list(range(15, 23))):
        for first, second in zip(group, group[1:]):
            if pins[first]['feature_kind'] != pins[second]['feature_kind']:
                raise ValueError('Different physical feature types cannot share spacing constraint')
            rows.append({
                'contact_ids': [pins[first]['instance_id'], pins[second]['instance_id']],
                'module_pin_numbers': [first, second],
                'feature_kind': pins[first]['feature_kind'],
                'image_points_xy_pixels': [pins[first]['center_xy_pixels'], pins[second]['center_xy_pixels']],
                'nominal_distance_metres': 0.002,
                'manufacturing_tolerance_metres': None,
                'scope': 'adjacent_same_row_module_contacts',
                'specimen_metric_measurement_verified': False,
            })
    return {
        'schema_version': '1.0',
        'release_eligible': False,
        'calibration_eligible': False,
        'image_path': source['image_path'],
        'image_sha256': source['image_sha256'],
        'physical_specimen_id': source['physical_specimen_id'],
        'source_contacts_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'dimension_source': {**source['source'], 'dimension_pages_one_based': [10, 11],
                             'quantity': 'nominal module contact pitch', 'pitch_metres': 0.002},
        'constraints': rows,
        'absolute_landmarks': [],
        'limitations': ['Relative spacing only; no absolute board frame or rigid 6DoF pose',
                       'No validated cross-row hole-center separation',
                       'Carrier footprint pad centers are not observed castellation centers',
                       'Camera intrinsics, distortion and specimen dimensions remain unverified',
                       'Do not convert perspective image distances into a uniform pixel-to-metre scale'],
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    payload = json.dumps(build(), indent=2) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != payload:
            raise SystemExit('ESP12E spacing constraints are stale')
    else:
        OUTPUT.write_text(payload)
    print('Checked 19 relative 2 mm contact-spacing constraints; full calibration remains unverified')
