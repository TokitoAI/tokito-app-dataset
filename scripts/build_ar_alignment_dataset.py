"""Join reviewed image instances and metric anchors to independently selectable CAD nodes.

GLB stays outside Git. A local copy is required to rebuild/check the selector audit.
Boxes, visible-body polygons, electrical pins, and CAD geometry remain distinct.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
AR = ROOT / 'data/board-sources/nxp-frdm-mcxn236/ar-reference'
OUTPUT = ROOT / 'data/ar-alignment/manifest.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def content_sha(path):
    data = Path(path).read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        return next(line.split(':', 1)[1] for line in data.decode().splitlines() if line.startswith('oid sha256:'))
    return hashlib.sha256(data).hexdigest()


def audit_nodes(glb, manifest, component_map):
    raw = Path(glb).read_bytes()
    if len(raw) != manifest['glbBytes'] or sha(glb) != manifest['glbSha256'].removeprefix('sha256:'):
        raise ValueError('GLB does not match the released digital-twin manifest')
    if struct.unpack_from('<III', raw) != (0x46546C67, 2, len(raw)):
        raise ValueError('Invalid GLB header')
    length, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4E4F534A or 20 + length > len(raw):
        raise ValueError('Invalid GLB JSON chunk')
    document = json.loads(raw[20:20 + length])
    nodes, meshes = document['nodes'], document['meshes']
    by_name = {}
    for index, node in enumerate(nodes):
        by_name.setdefault(node.get('name'), []).append(index)
    if (manifest['assetId'] != component_map['asset_id'] or
        manifest['componentNodePrefix'] != component_map['component_node_prefix'] or
        manifest['boardIdentity'] != component_map['board_id'] or
        manifest['boardRevision'] != component_map['board_revision'] or
        manifest['units'] != 'METRE' or manifest['axes'] != 'RIGHT_HANDED_Y_UP'):
        raise ValueError('CAD identity table and GLB manifest refer to different assets')
    if len({c['component_id'] for c in component_map['components']}) != len(component_map['components']):
        raise ValueError('CAD component IDs are not unique')
    owners, mesh_owners, targets = {}, {}, {}
    for component in component_map['components']:
        selector = component['glb_selector']
        if not component['needs_3d_body']:
            if selector is not None:
                raise ValueError('A non-populated reference was assigned a component mesh')
            continue
        indices = by_name.get(selector, [])
        if len(indices) != 1:
            raise ValueError(f'Component selector is missing or ambiguous: {selector}')
        root = indices[0]
        extras = nodes[root].get('extras', {}).get('tokito_component', {})
        if extras.get('reference') != component['reference']:
            raise ValueError(f'GLB metadata does not match reference: {selector}')
        stack, seen, mesh_ids = [root], set(), set()
        while stack:
            index = stack.pop()
            if not 0 <= index < len(nodes) or index in seen:
                raise ValueError(f'Invalid or repeated node in component subtree: {selector}')
            seen.add(index)
            if index in owners:
                raise ValueError(f'Component subtrees share a node: {selector}')
            owners[index] = selector
            node = nodes[index]
            stack.extend(node.get('children', []))
            if 'mesh' in node:
                mesh = node['mesh']
                if not 0 <= mesh < len(meshes) or not meshes[mesh].get('primitives'):
                    raise ValueError(f'Empty component geometry: {selector}')
                for primitive in meshes[mesh]['primitives']:
                    position = document['accessors'][primitive['attributes']['POSITION']]
                    bounds = position.get('min', []) + position.get('max', [])
                    if position['count'] < 3 or len(bounds) != 6 or not all(math.isfinite(v) for v in bounds):
                        raise ValueError(f'Component geometry bounds are missing or non-finite: {selector}')
                if mesh in mesh_owners and mesh_owners[mesh] != selector:
                    raise ValueError(f'Components share a mesh: {selector}')
                mesh_owners[mesh] = selector
                mesh_ids.add(mesh)
        if not mesh_ids:
            raise ValueError(f'Component has no mesh: {selector}')
        targets[component['component_id']] = {
            'selector': selector, 'node_index': root, 'mesh_ids': sorted(mesh_ids),
            'component_class': component['component_class'],
            'model_quality': component['model_quality'], 'reference_designator': component['reference'],
            'source_board_position_mm': component['board_position_mm'], 'source_side': component['side'],
        }
    return targets


def anchors(template, components):
    if 'pose_corners_normalized' not in template:
        return []
    pixels = template['pose_corners_normalized']
    metric = template['pose_metric_landmarks_metres']
    ids = template['pose_landmark_ids']
    if len(pixels) != 4 or len(metric) != 4 or len(set(ids)) != 4:
        raise ValueError('Calibration needs four distinct, paired semantic landmarks')
    source = template['metric_landmark_source']
    if content_sha(ROOT / source['path']) != source['sha256']:
        raise ValueError('Metric anchor source hash mismatch')
    result = []
    for identifier, xy, xz in zip(ids, pixels, metric):
        if len(xy) != 2 or len(xz) != 2 or not all(math.isfinite(v) for v in xy + xz):
            raise ValueError('Invalid paired calibration coordinates')
        position = components[identifier]['board_position_mm']
        if any(abs(a * 1000 - b) > 1e-5 for a, b in zip(xz, [position['x'], position['y']])):
            raise ValueError(f'Metric landmark is inconsistent with CAD source: {identifier}')
        result.append({'id': identifier, 'kind': template['pose_landmark_kind'],
                       'image_xy_normalized': xy, 'asset_xyz_metres': [xz[0], 0.0, xz[1]],
                       'image_uncertainty_pixels': template['corner_uncertainty_pixels']})
    return result


def reviewed_polygon(mask, label, template):
    if mask['image_path'] != template['image_path'] or mask['image_sha256'] != template['image_sha256']:
        raise ValueError('Mask belongs to another image')
    source = ROOT / mask['image_path']
    if sha(source) != mask['image_sha256']:
        raise ValueError('Original segmentation image hash mismatch')
    with Image.open(source) as raw:
        if ImageOps.exif_transpose(raw).size != (mask['image_width'], mask['image_height']):
            raise ValueError('Mask dimensions do not match the EXIF-upright image')
    polygon = [[x / mask['image_width'], y / mask['image_height']] for x, y in mask['polygon_xy_pixels']]
    box = label['bbox_xyxy_normalized']
    if len(polygon) < 3 or any(not (box[0] <= x <= box[2] and box[1] <= y <= box[3]) for x, y in polygon):
        raise ValueError('Reviewed visible body polygon is outside its instance box')
    area = sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(polygon, polygon[1:]+polygon[:1]))
    if abs(area) < 1e-10:
        raise ValueError('Visible-body polygon is degenerate')
    if mask['observed_reference_designator'] != label['source'].get('observed_refdes'):
        raise ValueError('Mask and observed component reference disagree')
    return polygon


def build(glb):
    manifest = read(AR / 'digital-twin-manifest.json')
    component_map = read(AR / 'component-map.json')
    provenance = read(AR / 'provenance.json')
    for entry in provenance['files']:
        if sha(AR / entry['path']) != entry['sha256']:
            raise ValueError('Released CAD metadata hash mismatch')
    targets = audit_nodes(glb, manifest, component_map)
    by_ref = {c['reference']: c for c in component_map['components']}
    population_file = ROOT / 'data/board-sources/nxp-frdm-mcxn236/structured-rev-c/components.json'
    population = {c['refdes']: c for c in read(population_file)['components']}
    if set(population) != set(by_ref):
        raise ValueError('Released CAD references differ from the acquired Rev C BOM')
    for identifier, target in targets.items():
        ref = target['reference_designator']
        target['source_dnp'] = population[ref]['dnp_explicit_in_bom']
        target['physical_population_confirmed'] = False
    hierarchy = read(ROOT / 'data/photo-model/label-hierarchy.json')
    scan = read(ROOT / 'data/phone-captures/2026-10-10/reviewed-scan-references.json')
    mask_file = ROOT / 'annotations/ar-instance-masks.json'
    multiview_file = ROOT / 'annotations/multiview-capture-review.json'
    multiview = read(multiview_file)
    captures = {c['image_path']: c for c in multiview['captures']}
    masks = {m['instance_id']: m for m in read(mask_file)['masks']}
    images = []

    def binding(reference):
        component = by_ref.get(reference)
        if component is None or component['component_id'] not in targets:
            return None
        return {'source_component_id': component['component_id'],
                'source_board_revision': component_map['board_revision'],
                'asset_id': manifest['assetId'], 'glb_sha256': manifest['glbSha256'],
                'selector': component['glb_selector'],
                'source_dnp': population[reference]['dnp_explicit_in_bom'],
                'mapping_status': 'source_candidate_photographed_revision_unverified',
                'installed_order_code_confirmed': False}

    for image in hierarchy['images']:
        instances = []
        for part in image['parts']:
            candidate = part.get('source_component_candidate')
            ref = candidate['source_refdes'] if candidate else part.get('observed_reference_designator')
            bound = binding(ref) if image['board']['class_id'] == 3 and candidate else None
            instances.append({'instance_id': part['id'], 'class_name': part['class_name'],
                              'observed_reference_designator': ref,
                              'bbox_xyxy_normalized': part['bbox_xyxy_normalized'],
                              'visible_body_polygon_xy_normalized': None,
                              'cad_binding': bound, 'pins': part['pins']})
        images.append({'image_path': image['image_path'], 'image_sha256': image['image_sha256'],
                       'class_id': image['board']['class_id'], 'component_coverage': image['part_coverage'],
                       'calibration_landmarks': [], 'instances': instances, 'unparented_contacts': []})
    for template in scan['templates']:
        instances, unparented = [], []
        for label in template['labels']:
            if label['kind'] == 'pin':
                unparented.append(label)
                continue
            mask = masks.pop(label['id'], None)
            polygon = None
            if mask:
                polygon = reviewed_polygon(mask, label, template)
            ref = label['source'].get('observed_refdes')
            instances.append({'instance_id': label['id'], 'class_name': mask['class_name'] if mask else None,
                              'observed_reference_designator': ref, 'observed_label': label['label'],
                              'bbox_xyxy_normalized': label['bbox_xyxy_normalized'],
                              'visible_body_polygon_xy_normalized': polygon,
                              'polygon_review_status': mask['review_status'] if mask else None,
                              'cad_binding': binding(ref) if template['class_id'] == 3 else None,
                              'pins': []})
        paired = anchors(template, by_ref) if template['class_id'] == 3 else []
        images.append({'image_path': template['image_path'], 'image_sha256': template['image_sha256'],
                       'class_id': template['class_id'], 'component_coverage': 'partial',
                       'calibration_landmarks': paired, 'instances': instances,
                       'asset_anchor_override_required': bool(paired),
                       'anchor_override_reason': 'Reviewed mounting-hole centers differ from released outline-corner landmarks' if paired else None,
                       'unparented_contacts': unparented})
    if masks:
        raise ValueError('A reviewed mask has no corresponding instance')
    image_by_path = {image['image_path']: image for image in images}
    specimen_views = {}
    for capture in captures.values():
        if capture['image_path'] not in image_by_path or capture['class_id'] != image_by_path[capture['image_path']]['class_id']:
            raise ValueError('Multi-view capture has no matching board annotation')
        if capture['view_slot'] not in multiview['required_view_slots']:
            raise ValueError('Unknown multi-view capture slot')
        specimen_views.setdefault(capture['specimen_id'], set()).add(capture['view_slot'])
    for image in images:
        image['view_metadata'] = captures.get(image['image_path'])
        for instance in image['instances']:
            ref = instance['observed_reference_designator']
            instance['physical_component_instance_id'] = (
                captures[image['image_path']]['specimen_id'] + ':' + ref
                if image['image_path'] in captures and ref else None
            )
    counts = Counter()
    for image in images:
        counts['paired_metric_landmarks'] += len(image['calibration_landmarks'])
        counts['instances'] += len(image['instances'])
        counts['unparented_contacts'] += len(image['unparented_contacts'])
        for instance in image['instances']:
            counts['reviewed_body_polygons'] += instance['visible_body_polygon_xy_normalized'] is not None
            counts['candidate_mesh_bindings'] += instance['cad_binding'] is not None
            counts['photo_located_parented_contacts'] += sum(p.get('photo_bbox_xyxy_pixels') is not None for p in instance['pins'])
    return {'schema_version': '1.0', 'release_eligible': False, 'evaluation_valid': False,
            'coordinate_contract': {'image': 'EXIF-upright originals; normalized x/y',
                                    'asset': 'metres, right-handed Y-up; [board x, height, board y]',
                                    'keypoint_order': 'explicit semantic landmark IDs; never infer from array position'},
            'inputs': {str(path.relative_to(ROOT)).replace('\\', '/'): sha(path) for path in [
                ROOT / 'data/photo-model/label-hierarchy.json',
                ROOT / 'data/phone-captures/2026-10-10/reviewed-scan-references.json', mask_file, multiview_file,
                AR / 'component-map.json', AR / 'digital-twin-manifest.json', AR / 'provenance.json', population_file]},
            'cad_assets': [{'asset_id': manifest['assetId'], 'glb_sha256': manifest['glbSha256'],
                            'glb_bytes': manifest['glbBytes'], 'verified_independent_component_meshes': len(targets),
                            'source_revision': 'C', 'component_targets': targets}],
            'coverage': dict(counts), 'images': images,
            'multiview_coverage': {
                'required_view_slots': multiview['required_view_slots'],
                'specimens_with_all_required_real_views': sum(set(multiview['required_view_slots']) <= views for views in specimen_views.values()),
                'reviewed_real_view_count': len(captures),
                'reviewed_physical_flip_sequence_count': len(multiview['flip_sequences']),
                'camera_calibrated_real_capture_count': sum(c['camera_calibration_id'] is not None for c in captures.values()),
            },
            'training_policy': {'partial_instances_are_not_exhaustive_negatives': True,
                                'bbox_is_not_segmentation': True, 'source_pins_are_not_visible_contacts': True,
                                'split_by_physical_specimen_and_capture_session': True,
                                'production_training_export_allowed': False},
            'remaining': ['Exhaustive visible-component masks and ignored/occluded regions across all five families',
                          'Matched-revision per-component CAD targets for ESP32, ESP8266, Ultimainboard and Raspberry Pi',
                          'Photographed-revision confirmation before exact NXP CAD activation',
                          'Independent specimen/session test sets and camera/AR alignment evaluation',
                          'Real underside/four-side captures and calibrated rotate-and-flip sequences across all five families',
                          'Parent and source orientation review for the 60 new printed-alias contacts']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--glb', type=Path, required=True, help='Cached released frdm_mcxn236_ar_visible.glb')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build(args.glb)
    if args.check:
        if read(OUTPUT) != result:
            raise ValueError('Saved AR alignment dataset differs from reviewed inputs or GLB')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'independently_selectable_source_components': result['cad_assets'][0]['verified_independent_component_meshes'],
                      **result['coverage'], 'release_eligible': False}))


if __name__ == '__main__':
    main()
