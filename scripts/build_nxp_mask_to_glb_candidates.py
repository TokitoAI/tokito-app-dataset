"""Build conservative, inspectable NXP photo-mask to source-GLB candidates.

This joins observed refdes only. It does not establish the photographed layout
revision, camera pose, installed order code, or production AR registration.
"""
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path('data/board-sources/nxp-frdm-mcxn236/ar-reference')
MASKS = Path('annotations/nxp-dense-component-review.json')
MAP = BASE / 'component-map.json'
GLB = BASE / 'frdm-mcxn236-rev-c-source-candidate.glb'
REVISION = BASE / 'revision-compatibility-review.json'
OUT = Path('data/ar-alignment/nxp-mask-to-glb-candidates.json')


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def glb_nodes(path):
    with (ROOT / path).open('rb') as stream:
        header = stream.read(20)
        magic, version, _, chunk_length, chunk_type = struct.unpack('<4sIIII', header)
        if (magic, version, chunk_type) != (b'glTF', 2, 0x4E4F534A):
            raise ValueError('unexpected GLB header')
        gltf = json.loads(stream.read(chunk_length))
    return gltf['nodes']


def build():
    source = json.loads((ROOT / MASKS).read_text(encoding='utf-8'))
    mapping = json.loads((ROOT / MAP).read_text(encoding='utf-8'))
    revision = json.loads((ROOT / REVISION).read_text(encoding='utf-8'))
    nodes = glb_nodes(GLB)
    names = Counter(node.get('name') for node in nodes)
    components = {item['reference']: item for item in mapping['components']}
    changed = set(revision['c_changes']['resistors_changed_to_zero_ohm'])
    changed |= set(revision['c_changes']['resistors_changed_to_dnp'])
    changed |= set(revision['c_changes']['deleted_references'])
    changed |= {entry.split(':')[0] for entry in revision['c_changes']['changed_header_contacts']}
    rows = []
    seen = set()
    for mask in source['masks']:
        image = Path(mask['image_path'])
        if sha(image) != mask['image_sha256']:
            raise ValueError(f'image hash mismatch: {image}')
        key = (str(image), mask['instance_id'])
        if key in seen:
            raise ValueError(f'duplicate photo instance: {key}')
        seen.add(key)
        ref = mask.get('observed_reference_designator')
        row = {
            'image_path': str(image).replace('\\', '/'),
            'image_sha256': mask['image_sha256'],
            'image_dimensions_wh': [mask['image_width'], mask['image_height']],
            'instance_id': mask['instance_id'],
            'class_name': mask['class_name'],
            'visible_body_polygon_xy_pixels': mask['polygon_xy_pixels'],
            'observed_reference_designator': ref,
            'photo_review_status': mask['review_status'],
            'source_candidate_component_id': None,
            'source_glb_selector': None,
            'link_status': 'unresolved_photo_local_instance',
            'candidate_only': True,
        }
        if mask.get('identity_correction_evidence'):
            row['identity_correction_evidence'] = mask['identity_correction_evidence']
        if ref:
            component = components.get(ref)
            if component is None:
                raise ValueError(f'observed refdes absent from source map: {ref}')
            selector = component['glb_selector']
            if component['side'] != 'top' or not selector or names[selector] != 1:
                raise ValueError(f'no unique top-side GLB selector: {ref}, {selector}')
            if mask.get('source_component_id') and mask['source_component_id'] != component['component_id']:
                raise ValueError(f'source component mismatch: {ref}')
            row['source_candidate_component_id'] = component['component_id']
            row['source_glb_selector'] = selector
            row['link_status'] = 'observed_refdes_to_rev_c_source_candidate'
            row['revision_sensitive_reference'] = ref in changed
            row['source_body_quality'] = component.get('model_quality')
        rows.append(row)
    counts = Counter(row['link_status'] for row in rows)
    result = {
        'schema_version': '1.0',
        'board_family': 'NXP FRDM-MCXN236',
        'source_design_revision': mapping['board_revision'],
        'photographed_layout_revision_verified': revision['layout_revision_match_verified'],
        'physical_camera_pose_verified': False,
        'same_specimen_flip_verified': False,
        'production_ar_eligible': False,
        'training_export_eligible': False,
        'scope': 'Observed, visually reviewed photo body masks joined by refdes to unique Rev C GLB selectors; no geometric overlay or installed identity claim.',
        'input_sha256': {str(path).replace('\\', '/'): sha(path) for path in (MASKS, MAP, GLB, REVISION)},
        'counts': dict(sorted(counts.items())),
        'instances': rows,
    }
    (ROOT / OUT).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    result = build()
    print(json.dumps(result['counts'], sort_keys=True))
