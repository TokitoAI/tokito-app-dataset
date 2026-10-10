#!/usr/bin/env python3
"""Build the reviewed board -> partial part -> reviewed photo pin labeling view.

Source pin records are design candidates. Reviewed pin annotations can be added
for any board family with verified parent and orientation evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/photo-model/label-hierarchy.json'
CLASS_NAMES = ['esp32_board', 'esp8266_board', 'ultimainboard',
               'nxp_frdm_mcxn236_board', 'raspberry_pi_3b_board']


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def sha256(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def verify_source_hash(name, expected):
    data = (ROOT / name).read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        assert f'oid sha256:{expected}\n'.encode() in data
    else:
        assert hashlib.sha256(data).hexdigest() == expected


def box(values):
    assert len(values) == 4 and all(isinstance(v, (int, float)) for v in values)
    x0, y0, x1, y1 = values
    assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
    return values


def through_hole_pad_records(name):
    """Read explicit through-hole pad number/net/UUID; exclude duplicate SMD additions."""
    data = (ROOT / name).read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        return None
    source = data.decode('utf-8')
    records = {}
    for match in re.finditer(r'\(pad "([^"]+)" thru_hole\b', source):
        depth, quoted, escaped = 0, False, False
        end = match.start()
        for end in range(match.start(), len(source)):
            char = source[end]
            if escaped:
                escaped = False
            elif quoted and char == '\\':
                escaped = True
            elif char == '"':
                quoted = not quoted
            elif not quoted:
                depth += (char == '(') - (char == ')')
                if depth == 0:
                    break
        block = source[match.start():end+1]
        uuid = re.search(r'\(uuid "([^"]+)"\)', block).group(1)
        net = re.search(r'\(net "([^"]+)"\)', block)
        assert uuid not in records
        records[uuid] = (match.group(1), net.group(1) if net else None)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare saved hierarchy with regenerated source joins')
    args = parser.parse_args()
    board_path = 'data/photo-model/board-annotations.json'
    review_path = 'data/photo-model/board-review.json'
    manifest_path = 'data/photo-model/photo-manifest.json'
    source_bundles_path = 'data/photo-model/source-bundles.json'
    other_pins_path = 'data/board-sources/non-nxp-source-pins.json'
    seed_paths = ['annotations/component-seed-annotations.json',
                  'annotations/large-board-component-seeds.json',
                  'annotations/nxp-component-seeds.json',
                  'annotations/component-seeds-expanded.json',
                  'annotations/component-seeds-sprint.json',
                  'annotations/component-seeds-final.json']
    links_path = 'annotations/component-source-links.json'
    photo_pins_path = 'annotations/pin-annotations.json'
    j22_link_path = 'annotations/ultimainboard-j22-source-link.json'
    pin_expansion_path = 'annotations/ultimainboard-pin-expansion.json'
    pi_j8_path = 'annotations/pi-j8-pin-labels.json'
    esp_contacts_paths = ['annotations/esp-header-pin-labels.json',
                          'annotations/esp-additional-contact-labels.json']
    components_path = 'data/board-sources/nxp-frdm-mcxn236/structured-rev-c/components.json'
    boards = read(board_path)
    review = read(review_path)['images']
    manifest = {row['file']: row for row in read(manifest_path)}
    source_bundles = read(source_bundles_path)
    assert set(source_bundles) == set(CLASS_NAMES)
    other_pin_catalog = read(other_pins_path)
    other_pin_families = {row['board_family']: row for row in other_pin_catalog['families']}
    assert set(other_pin_families) == {'esp8266_board', 'ultimainboard'}
    assert all(row['source_pin_record_count'] == len(row['pins']) for row in other_pin_families.values())
    assert len(boards) == len(review) == len(manifest) == 80
    assert len({row['file'] for row in boards}) == 80
    by_file = {}
    for row in boards:
        name = row['file']
        assert row['sha256'] == review[name]['sha256'] == manifest[name]['sha256']
        assert row['class_id'] == review[name]['class_id']
        assert row['board_class'] == CLASS_NAMES[row['class_id']]
        assert row['bbox_xyxy_normalized'] == review[name]['bbox_xyxy_normalized']
        assert row['box_status'] == 'visually-reviewed-board-box'
        assert (ROOT / 'data/photo-model/photos/raw' / name).is_file()
        by_file[name] = {
            'image_file': name, 'image_path': 'data/photo-model/photos/raw/' + name,
            'image_sha256': row['sha256'], 'image_width': row['width'],
            'image_height': row['height'], 'split': row['split'],
            'board': {
                'class_id': row['class_id'], 'family': row['board_class'],
                'model': row.get('exact_model'),
                'bbox_xyxy_normalized': box(row['bbox_xyxy_normalized']),
                'review_status': 'visually_reviewed_board_box_and_family',
                'source_reference': {
                    'path': source_bundles[row['board_class']]['path'],
                    'relation': source_bundles[row['board_class']]['relation'],
                    'exact_component_mapping': source_bundles[row['board_class']]['exact_component_mapping'],
                    'unlinked_source_pin_catalog_path': other_pins_path if row['board_class'] in other_pin_families else None,
                    'unlinked_source_pin_record_count': other_pin_families[row['board_class']]['source_pin_record_count'] if row['board_class'] in other_pin_families else 0,
                },
            },
            'part_coverage': 'not_reviewed', 'parts': [],
        }
    assert len({row['image_sha256'] for row in by_file.values()}) == 80

    components = {row['refdes']: row for row in read(components_path)['components']}
    links = read(links_path)['links']
    links_by_annotation = {row['annotation_id']: row for row in links}
    assert len(links_by_annotation) == len(links)
    part_ids = set()
    linked_count = 0
    pin_record_count = 0

    def add_part(image_file, source, key, index, original):
        nonlocal linked_count, pin_record_count
        board = by_file[image_file]
        label_id = f'{image_file}:{source}:{original.get("id", index)}'
        assert label_id not in part_ids
        part_ids.add(label_id)
        bounds = box(original.get('xyxy_normalized', original.get('bbox_xyxy_normalized', original.get('bbox_xyxy'))))
        refdes = original.get('reference_designator', original.get('refdes'))
        annotation_id = original.get('id')
        link = links_by_annotation.get(annotation_id) if source == seed_paths[2] else None
        if link:
            assert link['annotation_path'] == source
            assert link['image_path'] == board['image_path']
            assert link['image_sha256'] == board['image_sha256']
            assert board['board']['family'] == 'nxp_frdm_mcxn236_board'
            assert board['board']['model'] == link['source_board_model']
            assert link['observed_reference_designator'] == refdes
            assert link['specimen_revision'] is None
            assert link['exact_installed_part_mapping'] is False
            assert original['manufacturer_part_number'] is None
            component = components[refdes]
            assert link['source_component']['bom_item_id'] == component['bom_item_id']
            assert link['source_component']['sha256'] == sha256(components_path)
            pins = [{
                'pin_number': connection['pin'],
                'symbol_pin_name': connection['symbol_pin_name'],
                'source_net_name': connection['net_name'],
                'source_record_kind': connection['record_kind'],
                'photo_bbox_xyxy_pixels': None,
                'mapping_status': 'source_pin_unregistered_in_photo',
            } for connection in component['connections']]
            assert len({entry['pin_number'] for entry in pins}) == len(pins)
            source_part = {
                'source_board_revision': link['source_revision'],
                'source_refdes': refdes,
                'bom_item_id': component['bom_item_id'],
                'source_manufacturer_part_number_text': component['manufacturer_part_number_text'],
                'component_source_path': components_path,
                'component_source_sha256': sha256(components_path),
                'link_id': link['id'],
                'match_status': link['match_status'],
                'installed_part_identity_status': 'unconfirmed',
            }
            linked_count += 1
            pin_record_count += len(pins)
        else:
            assert source != seed_paths[2] or refdes is None, annotation_id
            pins, source_part = [], None
        kind = original.get('class_name', original.get('class'))
        assert kind
        board['parts'].append({
            'id': label_id, 'annotation_source': source,
            'annotation_id': annotation_id, 'class_name': kind,
            'bbox_xyxy_normalized': bounds,
            'box_review_status': original.get('review_status', original.get('annotation_status', 'partial_visual_seed')),
            'observed_reference_designator': refdes,
            'source_component_candidate': source_part,
            'photo_pin_label_count': 0,
            'pins': pins,
        })

    for source in [seed_paths[0], seed_paths[1], *seed_paths[3:]]:
        data = read(source)
        for image in data['images']:
            name = Path(image.get('filename', image.get('image'))).name
            board = by_file[name]
            assert board['part_coverage'] == 'not_reviewed'
            assert [board['image_width'], board['image_height']] == [image['width'], image['height']]
            if 'sha256' in image:
                assert board['image_sha256'] == image['sha256']
            if 'split' in image:
                assert board['split'] == image['split']
            source_family_to_class = {
                'ultimainboard_2_1_4': 'ultimainboard',
                'raspberry_pi_3b_v1_2': 'raspberry_pi_3b_board',
            }
            assert board['board']['family'] == source_family_to_class.get(image['board_family'], image['board_family'])
            board['part_coverage'] = 'partial_major_component_seeds'
            for number, original in enumerate(image['objects'], 1):
                add_part(name, source, 'objects', number, original)

    source = seed_paths[2]
    nxp = read(source)
    name = Path(nxp['source_image']).name
    board = by_file[name]
    assert nxp['source_image'] == board['image_path']
    assert nxp['source_image_sha256'] == board['image_sha256']
    assert board['board']['model'] == nxp['board_identity']['model']
    assert nxp['board_identity']['revision'] is None
    assert [board['image_width'], board['image_height']] == [nxp['image_width'], nxp['image_height']]
    assert board['part_coverage'] == 'not_reviewed'
    board['part_coverage'] = 'partial_major_component_seeds'
    for number, original in enumerate(nxp['annotations'], 1):
        add_part(name, source, 'annotations', number, original)

    assert linked_count == len(links)
    expansion = read(pin_expansion_path)
    assert expansion['photo']['sha256'] == by_file[Path(expansion['photo']['path']).name]['image_sha256']
    for source in expansion['sources'].values():
        verify_source_hash(source['path'], source['sha256'])
    for update in expansion['reviewed_parent_updates']:
        image = by_file[update['image_file']]
        assert image['board']['family'] == 'ultimainboard'
        part = next(part for part in image['parts'] if part['id'] == update['part_id'])
        assert part['annotation_source'] == update['seed_file']
        assert part['annotation_id'] == update['seed_id']
        assert part['bbox_xyxy_normalized'] == update['bbox_xyxy_normalized']
        part['observed_reference_designator'] = update['reference_designator']
        part['box_review_status'] = update['annotation_status']
        part['parent_review_source'] = pin_expansion_path

    pi_j8 = read(pi_j8_path)
    assert pi_j8['schema_version'] == '1.0'
    assert pi_j8['status'] == 'visually_reviewed_pin_locations_integrated_into_hierarchy'
    pi_photo = pi_j8['photo']
    pi_image = by_file[Path(pi_photo['path']).name]
    assert pi_image['image_sha256'] == pi_photo['sha256']
    assert pi_image['board']['family'] == 'raspberry_pi_3b_board'
    assert [pi_image['image_width'], pi_image['image_height']] == [pi_photo['width'], pi_photo['height']]
    for source in pi_j8['sources'].values():
        if isinstance(source, dict) and 'path' in source and 'sha256' in source:
            verify_source_hash(source['path'], source['sha256'])
    assert len(pi_j8['reviewed_parent_updates']) == 1
    for update in pi_j8['reviewed_parent_updates']:
        assert update['image_file'] == pi_image['image_file']
        part = next(part for part in pi_image['parts'] if part['id'] == update['part_id'])
        assert part['annotation_source'] == update['seed_file']
        assert part['annotation_id'] == update['seed_id']
        assert part['bbox_xyxy_normalized'] == update['bbox_xyxy_normalized']
        assert update['reference_designator'] == 'J8'
        part['observed_reference_designator'] = 'J8'
        part['box_review_status'] = update['annotation_status']
        part['parent_review_source'] = pi_j8_path

    photo_pins = read(photo_pins_path)
    assert photo_pins['schema_version'] == '1.0'
    pin_count = 0
    pin_ids = set()
    for entry in [*photo_pins['pins'], *expansion['pins'], *pi_j8['pins']]:
        image = by_file[entry['image_file']]
        assert entry['image_sha256'] == image['image_sha256']
        assert entry['board_family'] == image['board']['family']
        part = next(part for part in image['parts'] if part['id'] == entry['part_id'])
        assert part['box_review_status'].startswith('visual_reviewed_')
        pin_id = entry['id']
        assert pin_id and pin_id not in pin_ids
        pin_ids.add(pin_id)
        pixels = entry['photo_bbox_xyxy_pixels']
        assert len(pixels) == 4 and all(isinstance(v, int) for v in pixels)
        x0, y0, x1, y1 = pixels
        assert 0 <= x0 < x1 <= image['image_width']
        assert 0 <= y0 < y1 <= image['image_height']
        parent_bounds = part['bbox_xyxy_normalized']
        assert parent_bounds[0]*image['image_width'] <= x0 < x1 <= parent_bounds[2]*image['image_width']
        assert parent_bounds[1]*image['image_height'] <= y0 < y1 <= parent_bounds[3]*image['image_height']
        assert entry['review_status'] == 'visually_reviewed_pin_location'
        assert entry['pin_identity_evidence']
        number = entry['pin_number']
        assert isinstance(number, str) and number.strip()
        matching = [pin for pin in part['pins'] if pin['pin_number'] == number]
        assert len(matching) <= 1
        if matching:
            assert matching[0]['photo_bbox_xyxy_pixels'] is None
            matching[0]['photo_bbox_xyxy_pixels'] = pixels
            matching[0]['mapping_status'] = 'reviewed_photo_pin_with_source_candidate'
            matching[0]['photo_pin_annotation_id'] = pin_id
        else:
            part['pins'].append({
                'pin_number': number,
                'symbol_pin_name': None,
                'source_net_name': None,
                'source_record_kind': None,
                'photo_bbox_xyxy_pixels': pixels,
                'mapping_status': 'reviewed_photo_pin_without_source_link',
                'photo_pin_annotation_id': pin_id,
            })
        part['photo_pin_label_count'] += 1
        pin_count += 1

    alias_count = 0
    for esp_contacts_path in esp_contacts_paths:
        contacts = read(esp_contacts_path)
        assert contacts['schema_version'] == '1.0' and contacts['training_eligible'] is False
        for image_entry in contacts['images']:
            image = by_file[image_entry['image_file']]
            assert image_entry['image_sha256'] == image['image_sha256']
            assert image_entry['board_family'] == image['board']['family']
            assert [image_entry['image_width'], image_entry['image_height']] == [image['image_width'], image['image_height']]
            for number, original in enumerate(image_entry['parts'], 1):
                assert original['review_status'] == 'visually_reviewed_part_location'
                w, h = image['image_width'], image['image_height']
                x0, y0, x1, y1 = original['photo_bbox_xyxy_pixels']
                add_part(image['image_file'], esp_contacts_path, 'parts', number, {
                    'id': original['id'], 'class': original['class'],
                    'bbox_xyxy': [x0/w, y0/h, x1/w, y1/h],
                    'review_status': 'visual_reviewed_contact_row_box',
                })
                part = image['parts'][-1]
                for entry in original['pins']:
                    assert entry['id'] not in pin_ids
                    pin_ids.add(entry['id'])
                    assert entry['parent_part_id'] == original['id']
                    assert entry['label_semantics'] == 'board_silkscreen_alias'
                    assert entry['pin_number'] is None and entry['source_net'] is None and entry['source_refdes'] is None
                    assert entry['review_status'] == 'visually_reviewed_contact_and_printed_alias'
                    assert entry['printed_alias'] and entry['evidence']
                    a, b, c, d = entry['photo_bbox_xyxy_pixels']
                    assert x0 <= a < c <= x1 and y0 <= b < d <= y1
                    box([v/scale for v, scale in zip(entry['silkscreen_bbox_xyxy_pixels'], [w, h, w, h])])
                    part['pins'].append({
                        'pin_number': None, 'printed_alias': entry['printed_alias'],
                        'pin_identifier_kind': 'board_silkscreen_alias',
                        'symbol_pin_name': None, 'source_net_name': None,
                        'source_record_kind': None,
                        'photo_bbox_xyxy_pixels': entry['photo_bbox_xyxy_pixels'],
                        'silkscreen_bbox_xyxy_pixels': entry['silkscreen_bbox_xyxy_pixels'],
                        'mapping_status': 'reviewed_photo_contact_with_printed_alias',
                        'photo_pin_annotation_id': entry['id'],
                        'annotation_source': esp_contacts_path,
                        'identity_evidence': entry['evidence'],
                        'truncated': entry['truncated'],
                    })
                    part['photo_pin_label_count'] += 1
                    alias_count += 1
    j22 = read(j22_link_path)
    assert j22['schema_version'] == '1.0' and j22['status'] == 'source_verified_photo_pin_link'
    assert j22['board_family'] == 'ultimainboard'
    assert j22['photo_part']['seed_file_sha256'] == sha256('annotations/large-board-component-seeds.json')
    for source in [j22['native_sources']['pcb'], j22['native_sources']['schematic'], j22['imported_pcb']]:
        verify_source_hash(source['path'], source['sha256'])
    j22_image = by_file[Path(j22['photo']['path']).name]
    assert j22_image['image_sha256'] == j22['photo']['sha256']
    j22_part = next(part for part in j22_image['parts'] if part['id'] == j22['photo_part']['part_id'])
    assert j22_part['observed_reference_designator'] == j22['imported_pcb']['reference_designator'] == 'J22'
    assert j22_part['bbox_xyxy_normalized'] == j22['photo_part']['bbox_xyxy_normalized']
    j22_catalog = {(pin['refdes'], pin['pin_number']): pin for pin in other_pin_families['ultimainboard']['pins'] if pin['refdes'] == 'J22'}
    assert len(j22_catalog) == len(j22['pins']) == 4
    for source_pin in j22['pins']:
        number = source_pin['pin_number']
        photo_pin = next(pin for pin in j22_part['pins'] if pin['pin_number'] == number)
        catalog_pin = j22_catalog['J22', number]
        assert photo_pin['photo_pin_annotation_id'] == source_pin['photo_pin_id']
        assert photo_pin['photo_bbox_xyxy_pixels'] == source_pin['photo_bbox_xyxy_pixels']
        assert catalog_pin['source_record_index'] == source_pin['schematic_pin_record_index']
        photo_pin['symbol_pin_name'] = catalog_pin['pin_name']
        photo_pin['source_net_name'] = source_pin['source_net']
        photo_pin['source_record_kind'] = 'revision_matched_pcb_pad_and_schematic_pin'
        photo_pin['source_link_path'] = j22_link_path
        photo_pin['mapping_status'] = 'reviewed_photo_pin_with_source_link'
    j22_part['source_component_candidate'] = {
        'source_refdes': 'J22',
        'source_board_revision': '2.1.4',
        'source_link_path': j22_link_path,
        'installed_part_identity_status': 'unconfirmed',
    }
    expansion_catalog = {(pin['refdes'], pin['pin_number']): pin
                         for pin in other_pin_families['ultimainboard']['pins']
                         if pin['refdes'] in {entry['reference_designator'] for entry in expansion['connectors']}}
    pad_records = through_hole_pad_records(expansion['sources']['imported_pcb']['path'])
    expansion_source_records = set()
    for entry in expansion['pins']:
        image = by_file[entry['image_file']]
        part = next(part for part in image['parts'] if part['id'] == entry['part_id'])
        assert part['observed_reference_designator'] == entry['reference_designator']
        pin = next(pin for pin in part['pins'] if pin['pin_number'] == entry['pin_number'])
        catalog = expansion_catalog[entry['reference_designator'], entry['pin_number']]
        assert catalog['source_record_index'] == entry['source_schematic_pin_record_index']
        assert catalog['source_sheet'] == entry['source_schematic_sheet']
        path = entry['source_schematic_pin_records_path']
        records = {row['stream_record_index']: row['fields'] for row in read(path)}
        assert records[catalog['source_record_index']]['RECORD'] == '2'
        assert records[catalog['source_record_index']]['DESIGNATOR'] == entry['pin_number']
        expansion_source_records.add(path)
        connector = next(connector for connector in expansion['connectors'] if connector['part_id'] == part['id'])
        pad = next(pad for pad in connector['verified_through_hole_pads'] if pad['pin_number'] == entry['pin_number'])
        assert pad['uuid'] == entry['imported_pad_uuid'] and pad['net'] == entry['source_net']
        if pad_records is not None:
            assert pad_records[pad['uuid']] == (entry['pin_number'], entry['source_net'])
        pin['symbol_pin_name'] = catalog['pin_name']
        pin['source_net_name'] = entry['source_net']
        pin['source_record_kind'] = 'revision_matched_through_hole_pad_and_schematic_pin'
        pin['source_link_path'] = pin_expansion_path
        pin['mapping_status'] = 'reviewed_photo_pin_with_source_link'
        part['source_component_candidate'] = {
            'source_refdes': entry['reference_designator'],
            'source_board_revision': '2.1.4',
            'source_link_path': pin_expansion_path,
            'installed_part_identity_status': 'unconfirmed',
        }
    assert len(pi_j8['pins']) == pi_j8['connector']['source_pin_count'] == pi_j8['connector']['photo_contact_count'] == 40
    assert {entry['pin_number'] for entry in pi_j8['pins']} == {str(n) for n in range(1, 41)}
    pi_by_number = {int(entry['pin_number']): entry for entry in pi_j8['pins']}
    assert pi_j8['connector']['pin_1_position'] == 'upper_inner_in_original_photo'
    assert pi_j8['connector']['odd_pins'] == 'inner_row_away_from_right_PCB_edge_in_photo'
    for number in range(1, 40, 2):
        inner = pi_by_number[number]['photo_bbox_xyxy_pixels']
        outer = pi_by_number[number + 1]['photo_bbox_xyxy_pixels']
        assert inner[2] < outer[0] and abs(inner[1] - outer[1]) < 20
        if number > 1:
            assert pi_by_number[number - 2]['photo_bbox_xyxy_pixels'][3] < inner[1]
    pi_part = next(part for part in pi_image['parts'] if part['id'] == pi_j8['connector']['part_id'])
    assert pi_part['observed_reference_designator'] == 'J8'
    for entry in pi_j8['pins']:
        assert entry['image_file'] == pi_image['image_file']
        assert entry['reference_designator'] == 'J8'
        assert entry['source_document_path'] == pi_j8['sources']['reduced_schematic']['path']
        assert entry['source_net_semantics'] == 'reduced_schematic_net_name_not_measured_on_photo'
        assert entry['contact_location_confidence'] in ('high', 'moderate')
        pin = next(pin for pin in pi_part['pins'] if pin['pin_number'] == entry['pin_number'])
        assert pin['photo_bbox_xyxy_pixels'] == entry['photo_bbox_xyxy_pixels']
        pin['source_net_name'] = entry['source_net']
        pin['source_record_kind'] = 'revision_matched_reduced_schematic_J8_pin'
        pin['source_link_path'] = pi_j8_path
        pin['mapping_status'] = 'reviewed_photo_pin_with_source_document_link'
        pin['contact_location_confidence'] = entry['contact_location_confidence']
    pi_part['source_component_candidate'] = {
        'source_refdes': 'J8',
        'source_board_revision': '1.2',
        'source_link_path': pi_j8_path,
        'installed_part_identity_status': 'header_reference_designator_visually_reviewed',
    }
    for image in by_file.values():
        if image['board']['family'] == 'ultimainboard':
            image['board']['source_reference']['unlinked_source_pin_record_count'] -= len(j22['pins']) + len(expansion['pins'])
    stats = {
        'board_images': len(by_file),
        'board_family_counts': dict(sorted(Counter(row['board']['family'] for row in by_file.values()).items())),
        'partial_part_images': sum(row['part_coverage'] == 'partial_major_component_seeds' for row in by_file.values()),
        'partial_part_images_by_family': dict(sorted(Counter(
            row['board']['family'] for row in by_file.values()
            if row['part_coverage'] == 'partial_major_component_seeds').items())),
        'part_seed_boxes': len(part_ids),
        'part_seed_boxes_by_family': dict(sorted({family: sum(
            len(row['parts']) for row in by_file.values()
            if row['board']['family'] == family) for family in CLASS_NAMES}.items())),
        'source_linked_part_seeds': linked_count + 1 + len(expansion['connectors']) + 1,
        'nxp_source_linked_part_seeds': linked_count,
        'source_pin_records_under_linked_parts': pin_record_count + len(j22['pins']) + len(expansion['pins']) + len(pi_j8['pins']),
        'reference_source_pin_catalog_records': sum(row['source_pin_record_count'] for row in other_pin_families.values()),
        'unlinked_reference_source_pin_records': sum(row['source_pin_record_count'] for row in other_pin_families.values()) - len(j22['pins']) - len(expansion['pins']),
        'source_linked_photo_pins': len(j22['pins']) + len(expansion['pins']) + len(pi_j8['pins']),
        'photo_pins_located': pin_count + alias_count,
        'photo_pins_numbered': pin_count,
        'photo_contacts_with_printed_alias': alias_count,
        'photo_pins_located_by_family': dict(sorted({family: sum(
            part['photo_pin_label_count'] for row in by_file.values()
            if row['board']['family'] == family for part in row['parts'])
            for family in CLASS_NAMES}.items())),
    }
    assert stats['partial_part_images'] == 19 and stats['part_seed_boxes'] == 240
    result = {
        'schema_version': '1.0',
        'label_order': ['board_family', 'part', 'pin'],
        'meaning': 'Board labels are reviewed; parts have partial coverage. Source-only pin records, reviewed numeric photo pins and directly printed photo contact aliases retain distinct status.',
        'sources': {name: {'sha256': sha256(name)} for name in [board_path, review_path, manifest_path, source_bundles_path, other_pins_path, *seed_paths, links_path, components_path, photo_pins_path, j22_link_path, pin_expansion_path, pi_j8_path, *esp_contacts_paths, *sorted(expansion_source_records)]},
        'statistics': stats,
        'images': [by_file[row['file']] for row in boards],
    }
    if args.check:
        assert read('data/photo-model/label-hierarchy.json') == result
        print('Hierarchy matches current reviewed board, seed part and source pin records:', stats)
    else:
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
        print('Wrote label hierarchy:', stats)


if __name__ == '__main__':
    main()
