#!/usr/bin/env python3
"""Build the reviewed board -> partial part -> reviewed photo pin labeling view.

Source pin records are design candidates. Reviewed pin annotations can be added
for any board family, but none exists in this snapshot.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/photo-model/label-hierarchy.json'
CLASS_NAMES = ['esp32_board', 'esp8266_board', 'ultimainboard',
               'nxp_frdm_mcxn236_board', 'raspberry_pi_3b_board']


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def sha256(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def box(values):
    assert len(values) == 4 and all(isinstance(v, (int, float)) for v in values)
    x0, y0, x1, y1 = values
    assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
    return values


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
                  'annotations/component-seeds-sprint.json']
    links_path = 'annotations/component-source-links.json'
    photo_pins_path = 'annotations/pin-annotations.json'
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

    for source in [seed_paths[0], seed_paths[1], seed_paths[3], seed_paths[4]]:
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
    photo_pins = read(photo_pins_path)
    assert photo_pins['schema_version'] == '1.0'
    pin_count = 0
    pin_ids = set()
    for entry in photo_pins['pins']:
        image = by_file[entry['image_file']]
        assert entry['image_sha256'] == image['image_sha256']
        assert entry['board_family'] == image['board']['family']
        part = next(part for part in image['parts'] if part['id'] == entry['part_id'])
        pin_id = entry['id']
        assert pin_id and pin_id not in pin_ids
        pin_ids.add(pin_id)
        pixels = entry['photo_bbox_xyxy_pixels']
        assert len(pixels) == 4 and all(isinstance(v, int) for v in pixels)
        x0, y0, x1, y1 = pixels
        assert 0 <= x0 < x1 <= image['image_width']
        assert 0 <= y0 < y1 <= image['image_height']
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
        'source_linked_part_seeds': linked_count,
        'source_pin_records_under_linked_parts': pin_record_count,
        'unlinked_reference_source_pin_records': sum(row['source_pin_record_count'] for row in other_pin_families.values()),
        'photo_pins_located': pin_count,
        'photo_pins_located_by_family': dict(sorted({family: sum(
            part['photo_pin_label_count'] for row in by_file.values()
            if row['board']['family'] == family for part in row['parts'])
            for family in CLASS_NAMES}.items())),
    }
    assert stats['partial_part_images'] == 15 and stats['part_seed_boxes'] == 204
    result = {
        'schema_version': '1.0',
        'label_order': ['board_family', 'part', 'pin'],
        'meaning': 'Board labels are reviewed; part boxes are partial review seeds; source pin records are not photo pin labels.',
        'sources': {name: {'sha256': sha256(name)} for name in [board_path, review_path, manifest_path, source_bundles_path, other_pins_path, *seed_paths, links_path, components_path, photo_pins_path]},
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
