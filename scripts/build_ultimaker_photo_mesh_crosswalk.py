"""Join reviewed Ultimaker photo masks to source-selectable 3D candidates.

The join is by visually reviewed reference designator. It does not assert that
the user's physical PCB matches the source revision or that image pose is known.
"""
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANNOTATION = ROOT / 'annotations/ultimainboard-dense-component-review.json'
COMPONENTS = ROOT / 'data/board-sources/ultimainboard-2.1.4/ar-source-candidate/component-map.json'
GEOMETRY = ROOT / 'data/board-sources/ultimainboard-2.1.4/ar-source-candidate/contact-completion/geometry-coverage.json'
VALIDATION = ROOT / 'data/board-sources/ultimainboard-2.1.4/ar-source-candidate/contact-completion/validation.json'
OUTPUT = ROOT / 'data/ar-alignment/ultimaker-photo-mesh-crosswalk.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    annotation = json.loads(ANNOTATION.read_text(encoding='utf-8'))
    originals = json.loads(COMPONENTS.read_text(encoding='utf-8'))['components']
    geometry = json.loads(GEOMETRY.read_text(encoding='utf-8'))
    validation = json.loads(VALIDATION.read_text(encoding='utf-8'))
    if not validation['independent_node_ownership'] or not validation['independent_mesh_ownership']:
        raise ValueError('GLB independent component selection is not validated')
    if geometry['photo_registration_verified'] or geometry['physical_flip_verified']:
        raise ValueError('This crosswalk expects the unregistered source candidate')
    original_by_ref = {item['reference']: item for item in originals}
    added_by_ref = {item['reference']: item for item in geometry['added_regions']}
    if len(original_by_ref) != len(originals) or len(added_by_ref) != len(geometry['added_regions']):
        raise ValueError('ambiguous source geometry reference')
    if original_by_ref.keys() & added_by_ref.keys():
        raise ValueError('duplicate original and added source selector')
    photo = ROOT / annotation['photo']['path']
    photo_hash = digest(photo)
    if photo_hash != annotation['photo']['sha256']:
        raise ValueError('photo hash does not match annotation')
    linked, excluded = [], []
    for instance in annotation['instances']:
        ref = instance.get('observed_reference_designator')
        status = instance.get('source_mapping_status')
        source = original_by_ref.get(ref) or added_by_ref.get(ref)
        if status != 'source_candidate_by_readable_refdes_only' or not source:
            excluded.append({'photo_instance_id': instance['instance_id'],
                             'observed_reference_designator': ref,
                             'reason': status or 'no_matching_source_selector'})
            continue
        selector = source.get('glb_selector', source.get('selector'))
        if selector != f'ref:{ref}':
            raise ValueError(f'source selector mismatch: {ref}')
        linked.append({
            'photo_instance_id': instance['instance_id'],
            'photo_image_path': str(photo.relative_to(ROOT)),
            'photo_image_sha256': photo_hash,
            'photo_polygon_xy_pixels': instance['polygon_xy_pixels'],
            'photo_class_name': instance['class_name'],
            'observed_reference_designator': ref,
            'source_component_id_candidate': source.get('component_id', f'ultimainboard:2.1.4:{ref}'),
            'glb_selector_candidate': selector,
            'selector_origin': 'original_source_glb' if ref in original_by_ref else 'contact_completion_glb',
            'geometry_kind': source.get('kind', 'original_source_component'),
            'join_basis': 'visually_reviewed_photo_refdes_to_source_reference',
            'installed_part_identity_confirmed': False,
            'photo_to_3d_pose_verified': False,
            'physical_flip_verified': False,
            'ar_highlight_release_eligible': False,
        })
    if len({row['photo_instance_id'] for row in linked}) != len(linked):
        raise ValueError('duplicate photo instance')
    if len({row['glb_selector_candidate'] for row in linked}) != len(linked):
        raise ValueError('multiple photo instances target one mesh selector')
    glb_path = ROOT / 'data/board-sources/ultimainboard-2.1.4/ar-source-candidate/contact-completion/ultimaker-source-contact-selectable-candidate.glb'
    glb = glb_path.read_bytes()
    if hashlib.sha256(glb).hexdigest() != geometry['output_sha256']:
        raise ValueError('GLB hash differs from geometry coverage report')
    if glb[:4] != b'glTF':
        raise ValueError('invalid GLB header')
    json_length, json_type = struct.unpack_from('<II', glb, 12)
    if json_type != 0x4E4F534A:
        raise ValueError('first GLB chunk must be JSON')
    nodes = json.loads(glb[20:20 + json_length])['nodes']
    named = {}
    for index, node in enumerate(nodes):
        if node.get('name'):
            named.setdefault(node['name'], []).append(index)
    owned_meshes = set()
    for row in linked:
        indices = named.get(row['glb_selector_candidate'], [])
        if len(indices) != 1:
            raise ValueError(f"selector not unique in GLB: {row['glb_selector_candidate']}")
        stack, meshes = indices[:], []
        while stack:
            node = nodes[stack.pop()]
            if 'mesh' in node:
                meshes.append(node['mesh'])
            stack.extend(node.get('children', []))
        if not meshes or owned_meshes.intersection(meshes):
            raise ValueError(f"missing or shared component mesh: {row['glb_selector_candidate']}")
        owned_meshes.update(meshes)
        row['glb_mesh_ids'] = sorted(meshes)
    return {
        'schema_version': '1.0', 'board_family': annotation['board_family'],
        'source_files_sha256': {str(path.relative_to(ROOT)): digest(path)
                                for path in (ANNOTATION, COMPONENTS, GEOMETRY, VALIDATION)},
        'source_glb_sha256': geometry['output_sha256'],
        'source_glb_path': str(glb_path.relative_to(ROOT)),
        'photo_instance_count': len(annotation['instances']),
        'candidate_selector_links': len(linked),
        'excluded_count': len(excluded),
        'excluded_reasons': dict(Counter(row['reason'] for row in excluded)),
        'release_eligible': False,
        'limitations': ['Source reference match does not confirm the physical PCB revision or installed part.',
                        'No photo-to-3D metric pose or same-specimen continuous flip has been verified.',
                        'The photographed frame has partial visible-instance coverage.'],
        'links': linked, 'excluded': excluded,
    }


if __name__ == '__main__':
    with OUTPUT.open('w', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(build(), indent=2) + '\n')
    print(str(OUTPUT))
