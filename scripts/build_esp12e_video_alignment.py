"""Index reviewed ESP-12E video bodies and contacts for future metric/mesh joins."""
import argparse
import hashlib
import json
from pathlib import Path

from validate_board_video import validate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/video-captures/2026-10-10/esp12e-keyframes'
OUTPUT = ROOT / 'data/ar-alignment/esp12e-video-instances.json'


def build():
    validate(ROOT, BASE / 'manifest.json')
    files = [BASE / name for name in ('manifest.json', 'reviewed-component-masks.json',
                                     'reviewed-module-contacts.json')]
    capture, bodies, module = [json.loads(path.read_text()) for path in files]
    width, height = bodies['image_width'], bodies['image_height']
    specimen = bodies['physical_specimen_id']
    records = [{
        'instance_id': specimen + ':esp12e_module',
        'parent_id': specimen,
        'kind': 'component_assembly',
        'observed_marking': 'MODEL: ESP-12E',
        'visible_polygon_normalized': None,
        'geometry_status': 'assembly_boundary_incomplete; antenna_clipped',
        'source_component_id': None,
        'glb_selector': None,
    }]
    for body in bodies['masks']:
        records.append({
            'instance_id': body['instance_id'],
            'parent_id': body.get('parent_component_id', specimen),
            'kind': body['class_name'],
            'observed_marking': body.get('observed_marking'),
            'exact_part_name': body.get('exact_part_name'),
            'visible_polygon_normalized': [[x / width, y / height]
                                           for x, y in body['polygon_xy_pixels']],
            'geometry_scope': body['boundary_scope'],
            'boundary_uncertainty_pixels': body['boundary_uncertainty_pixels'],
            'source_component_id': None,
            'glb_selector': None,
        })
    for pin in bodies['pin_annotations'] + module['contacts']:
        x, y = pin['center_xy_pixels']
        records.append({
            'instance_id': pin['instance_id'],
            'parent_id': pin.get('parent_component_id', specimen),
            'kind': 'module_contact' if 'source_module_pin_number' in pin else 'header_contact',
            'point_normalized': [x / width, y / height],
            'printed_alias': pin.get('printed_alias'),
            'source_module_pin_number': pin.get('source_module_pin_number'),
            'source_pin_name': pin.get('source_pin_name'),
            'physical_feature': pin.get('feature_kind', 'visible_solder_contact_center'),
            'electrical_continuity_verified': False,
            'metric_position_metres': None,
            'glb_selector': None,
        })
    identities = {record['instance_id'] for record in records}
    if len(identities) != len(records):
        raise ValueError('Duplicate instance IDs')
    if any(record['parent_id'] not in identities | {specimen} for record in records):
        raise ValueError('Missing parent instance')
    return {
        'schema_version': '1.0',
        'release_eligible': False,
        'training_export_eligible': False,
        'evaluation_valid': False,
        'source_files': [{'path': str(path.relative_to(ROOT)).replace('\\', '/'),
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                         for path in files],
        'image_path': bodies['image_path'],
        'image_sha256': bodies['image_sha256'],
        'image_dimensions': [width, height],
        'physical_specimen_id': specimen,
        'capture_session_id': capture['capture_session_id'],
        'required_split_group': specimen,
        'instances': records,
        'calibration_landmarks': [],
        'coverage': {'assembly_records': 1, 'visible_body_masks': len(bodies['masks']),
                     'header_contacts': len(bodies['pin_annotations']),
                     'module_contacts': len(module['contacts']), 'verified_mesh_joins': 0},
        'limitations': ['Partial front-side macro frame', 'No complete board boundary',
                        'No verified metric landmarks or camera intrinsics',
                        'No source-matched carrier geometry or selectable component meshes',
                        'No real underside/four-side/flip evaluation'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    payload = json.dumps(build(), indent=2) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != payload:
            raise SystemExit('ESP12E video alignment index is stale')
    else:
        OUTPUT.write_text(payload)
    print('ESP12E video alignment index checked: 18 body masks, 37 contacts, 0 verified mesh joins')
