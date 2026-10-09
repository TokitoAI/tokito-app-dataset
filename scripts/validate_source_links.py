"""Check portable photo/source links and their declared evidence without PDF libraries.

With LFS objects present this hashes their bytes; pointer-only CI checks their
declared SHA-256 and size. Visual correctness is a separate review requirement.
"""
from collections import Counter, defaultdict
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def path_in_repo(value):
    path = Path(value)
    assert not path.is_absolute() and ':' not in value and '\\' not in value, value
    target = (ROOT / path).resolve()
    assert target.is_relative_to(ROOT) and target.is_file(), value
    return target


def evidence_hash(path):
    data = path.read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        fields = dict(line.split(' ', 1) for line in data.decode().splitlines())
        kind, digest = fields['oid'].split(':', 1)
        assert kind == 'sha256' and len(digest) == 64
        return digest, int(fields['size'])
    return hashlib.sha256(data).hexdigest(), len(data)


def read_json(value):
    return json.loads(path_in_repo(value).read_text(encoding='utf-8'))


def path_in_bundle(bundle, value):
    path = Path(value)
    assert value and not path.is_absolute() and ':' not in value and '\\' not in value, value
    target = (bundle / path).resolve()
    assert target.is_relative_to(bundle), value
    return path_in_repo(target.relative_to(ROOT).as_posix())


def validate_source_record(bundle, source):
    path = path_in_bundle(bundle, source['path'])
    assert re.fullmatch('[0-9a-f]{64}', source['sha256'])
    assert isinstance(source['bytes'], int) and source['bytes'] >= 0
    assert evidence_hash(path) == (source['sha256'], source['bytes']), source['path']
    return path


def unique_records(rows, key):
    result = {row[key]: row for row in rows}
    assert len(result) == len(rows), f'Duplicate {key}'
    return result


def normalized_field(value):
    return '' if value is None else str(value).strip()


def validate_archive(inventory_path):
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    bundle = inventory_path.parent
    archive = inventory['archive']
    archive_path = path_in_repo((bundle / archive['path']).relative_to(ROOT).as_posix())
    assert evidence_hash(archive_path) == (archive['sha256'], archive['bytes'])
    assert inventory['file_count'] == len(inventory['files'])
    members = {}
    for item in inventory['files']:
        path = path_in_repo((bundle / item['path']).relative_to(ROOT).as_posix())
        assert path.is_relative_to(bundle)
        assert evidence_hash(path) == (item['sha256'], item['bytes'])
        member_name = Path(item['path']).relative_to('original-design-files').as_posix()
        assert member_name not in members
        members[member_name] = item
    # CI can inspect LFS declarations. A full checkout also checks ZIP CRCs and
    # every member's bytes against the extracted-file inventory.
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path) as archive_file:
            assert archive_file.testzip() is None
            assert set(archive_file.namelist()) == set(members)
            for name, item in members.items():
                assert hashlib.sha256(archive_file.read(name)).hexdigest() == item['sha256']
    else:
        assert archive_path.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1\n')
    return len(members)


def validate_index(index_path):
    index = json.loads(index_path.read_text(encoding='utf-8'))
    source = index['source']
    pdf = (index_path.parent / source['pdf_path_relative_to_index']).resolve()
    assert pdf.is_relative_to(ROOT) and pdf.is_file()
    assert evidence_hash(pdf) == (source['pdf_sha256'], source['pdf_bytes'])
    pages = {page['page']: page for page in index['pages']}
    assert len(index['pages']) == len(pages) == source['page_count']
    assert set(pages) == set(range(1, source['page_count'] + 1))
    by_refdes, occurrences = defaultdict(list), {}
    for item in index['occurrences']:
        assert item['id'] not in occurrences, item['id']
        occurrences[item['id']] = item
        page = pages[item['page']]
        x0, top, x1, bottom = item['bbox_pt']
        assert all(math.isfinite(v) for v in (x0, top, x1, bottom))
        assert 0 <= x0 < x1 <= page['width_pt']
        assert 0 <= top < bottom <= page['height_pt']
        assert item['raw_text'] and item['normalized_refdes']
        by_refdes[item['normalized_refdes']].append(item['id'])
    assert dict(by_refdes) == index['by_refdes']
    assert len(occurrences) == index['statistics']['occurrence_count']
    assert len(by_refdes) == index['statistics']['unique_normalized_reference_texts']
    return index, occurrences, pdf


def validate_structured_sources(bundle_entry):
    components_path = path_in_repo(bundle_entry['structured_components'])
    report_path = path_in_repo(bundle_entry['structured_extraction_report'])
    bundle_relative = bundle_entry['path']
    assert ':' not in bundle_relative and '\\' not in bundle_relative
    assert not Path(bundle_relative).is_absolute()
    bundle = (ROOT / bundle_relative).resolve()
    assert bundle.is_relative_to(ROOT) and bundle.is_dir()
    assert components_path.is_relative_to(bundle) and report_path.parent == components_path.parent
    data = json.loads(components_path.read_text(encoding='utf-8'))
    report = json.loads(report_path.read_text(encoding='utf-8'))
    assert data['schema_version'] == report['schema_version'] == '1.0'
    assert report['board'] == 'FRDM-MCXN236' and report['source_revision'] == 'C'
    assert data['sources'] == report['source_files']
    sources = data['sources']
    source_paths = {name: validate_source_record(bundle, record) for name, record in sources.items()}
    inventory = read_json(bundle_entry['design_archive_inventory'])
    inventory_records = {row['path']: {key: row[key] for key in ('path', 'sha256', 'bytes')} for row in inventory['files']}
    assert unique_records(list(sources.values()), 'path') == inventory_records

    joins = data['schematic_join_sources']
    assert joins == report['schematic_join_sources']
    index_path = validate_source_record(bundle, joins['index'])
    assert index_path == path_in_repo(bundle_entry['schematic_reference_index'])
    joined_pdf = validate_source_record(bundle, joins['pdf'])
    index, occurrences, indexed_pdf = validate_index(index_path)
    assert joined_pdf == indexed_pdf

    def artifact(name, source_name):
        path = path_in_bundle(bundle, (components_path.parent / name).relative_to(bundle).as_posix())
        value = json.loads(path.read_text(encoding='utf-8'))
        assert value['schema_version'] == '1.0'
        assert value['source'] == sources[source_name]
        return value

    bom = artifact('bom-items.json', 'SCH-90828_C.BOM.xlsx')
    workbook = artifact('bom-workbook.json', 'SCH-90828_C.BOM.xlsx')
    text_bom = artifact('bom-text.json', 'SCH-90828_C.BOM')
    native = artifact('native-parts.json', 'allegro/pstxprt.dat')
    primitive_data = artifact('primitives.json', 'allegro/pstchip.dat')
    net_data = artifact('netlist.json', 'allegro/pstxnet.dat')
    bom_items = unique_records(bom['items'], 'id')
    components = unique_records(data['components'], 'refdes')
    parts = unique_records(native['parts'], 'refdes')
    primitives = unique_records(primitive_data['primitives'], 'name')
    nets = unique_records(net_data['records'], 'id')
    unique_records(net_data['records'], 'name')
    sheets = unique_records(workbook['sheets'], 'sheet')
    sheet_rows = {name: unique_records(sheet['rows'], 'row') for name, sheet in sheets.items()}
    bom_by_ref, text_by_ref = {}, {}
    for item in bom_items.values():
        raw = item['source_columns']
        sheet = sheets[item['sheet']]
        assert bom['columns'] == sheet['columns']
        assert sheet_rows[item['sheet']][sheet['header_row']]['values'] == bom['columns']
        row = sheet_rows[item['sheet']][item['row']]
        assert list(raw) == bom['columns'] and list(raw.values()) == row['values']
        assert item['range'] == f"A{item['row']}:K{item['row']}"
        refs = raw['Reference'].split(',')
        assert refs == item['reference_designators'] and len(refs) == raw['Quantity']
        assert item['dnp_explicit'] is (normalized_field(raw['ASSY_OPT']).upper() == 'DNP')
        assert item['manufacturer_part_number_text'] == (None if raw['MFG_PN'] is None else str(raw['MFG_PN']))
        assert item['manufacturer_part_number_cell_type'] == row['cell_types'][bom['columns'].index('MFG_PN')]
        for ref in refs:
            assert ref not in bom_by_ref
            bom_by_ref[ref] = item
    for item in text_bom['items']:
        raw = item['source_columns']
        assert raw['Reference'].split(',') == item['reference_designators']
        assert int(raw['Quantity']) == len(item['reference_designators'])
        for ref in item['reference_designators']:
            assert ref not in text_by_ref
            text_by_ref[ref] = item
            assert all(normalized_field(raw[column]) == normalized_field(bom_by_ref[ref]['source_columns'][column]) for column in text_bom['columns'])
    assert set(bom_by_ref) == set(text_by_ref) == set(parts) == set(components)
    assert {part['primitive'] for part in parts.values()} == set(primitives)

    connections, pin_assignments = defaultdict(list), set()
    node_refs, electrical_refs = set(), set()
    electrical, no_connect = [], []
    for net in nets.values():
        is_nc = net['name'] == net['instance_path'] == net['properties'].get('C_SIGNAL') == 'NC'
        assert net['record_kind'] == ('no_connect_group' if is_nc else 'electrical_net')
        (no_connect if is_nc else electrical).append(net)
        for node in net['nodes']:
            ref, pin = node['refdes'], node['pin']
            assert (ref, pin) not in pin_assignments, (ref, pin)
            pin_assignments.add((ref, pin))
            node_refs.add(ref)
            if not is_nc:
                electrical_refs.add(ref)
            part = parts[ref]
            assert pin in {number for p in primitives[part['primitive']]['pins'] for number in p['physical_pins']}
            assert node['instance_path'] in {section['instance_path'] for section in part['sections']}
            connections[ref].append({'net_record_id': net['id'], 'net_name': net['name'],
                                     'record_kind': net['record_kind'], 'pin': pin,
                                     'symbol_pin_name': node['symbol_pin_name'], 'source_lines': node['source_lines']})
    assert len(no_connect) == 1 and set(parts) == node_refs
    for ref, component in components.items():
        item, part = bom_by_ref[ref], parts[ref]
        raw, body = item['source_columns'], primitives[part['primitive']]['body_properties']
        assert component['bom_item_id'] == item['id']
        assert component['bom_source'] == {'file': sources['SCH-90828_C.BOM.xlsx']['path'],
                                          'sheet': item['sheet'], 'row': item['row'], 'range': item['range']}
        assert component['bom_columns'] == raw
        assert component['manufacturer_part_number_text'] == item['manufacturer_part_number_text']
        assert component['dnp_explicit_in_bom'] is item['dnp_explicit']
        assert component['native_part'] == part and component['primitive_body_properties'] == body
        assert normalized_field(raw['AgilePN']) == normalized_field(body['PART_NUMBER'])
        assert normalized_field(raw['VALUE']) == normalized_field(body['VALUE'])
        flags = [part['properties'].get('BOM_IGNORE')] + [section['properties'].get('BOM_IGNORE') for section in part['sections']]
        assert all((normalized_field(flag).upper() == 'DNP') == item['dnp_explicit'] for flag in flags)
        assert component['connections'] == connections[ref]
        expected_candidates = [{key: occurrences[identifier][key] for key in ('id', 'page', 'bbox_pt', 'raw_text', 'context')}
                               for identifier in index['by_refdes'].get(ref, [])]
        assert component['schematic_text_candidates'] == expected_candidates

    # These inexpensive checks bind structured sets/counts to native text when
    # materialized. Full grammar and worksheet extraction remain the separate
    # extractor's --check; pointer-only CI validates the declared source hashes.
    for source_name, pattern, expected in (
        ('allegro/pstxprt.dat', r'(?m)^PART_NAME\s*\n\s+(\S+)', list(parts)),
        ('allegro/pstchip.dat', r"(?m)^primitive '([^']*)';", list(primitives)),
        ('allegro/pstxnet.dat', r"(?m)^NET_NAME\s*\n'([^']*)'", [net['name'] for net in nets.values()]),
        ('allegro/pstxnet.dat', r'(?m)^NODE_NAME\s+(\S+)\s+(\S+)', list(pin_assignments)),
    ):
        raw_bytes = source_paths[source_name].read_bytes()
        if not raw_bytes.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            found = re.findall(pattern, raw_bytes.decode('utf-8-sig'))
            assert Counter(found) == Counter(expected), source_name

    statistics = {
        'bom_items': len(bom_items), 'bom_reference_designators': len(bom_by_ref),
        'bom_declared_quantity_sum': sum(item['source_columns']['Quantity'] for item in bom_items.values()),
        'bom_items_marked_DNP': sum(item['dnp_explicit'] for item in bom_items.values()),
        'bom_references_marked_DNP': sum(len(item['reference_designators']) for item in bom_items.values() if item['dnp_explicit']),
        'no_part_to_order_references': sum(len(item['reference_designators']) for item in bom_items.values() if 'NO PART TO ORDER' in str(item['source_columns']['Description']).upper()),
        'native_parts': len(parts), 'primitive_definitions': len(primitives),
        'net_records_including_NC': len(nets), 'electrical_net_records': len(electrical),
        'node_records_including_NC': len(pin_assignments),
        'no_connect_group_nodes': sum(len(net['nodes']) for net in no_connect),
        'electrical_net_nodes': sum(len(net['nodes']) for net in electrical),
        'references_on_electrical_nets': len(electrical_refs),
        'components_with_schematic_text_candidates': sum(bool(c['schematic_text_candidates']) for c in components.values()),
    }
    assert statistics == report['statistics']
    assert report['validation']['cross_source_comparisons_passed'] is True
    assert all(not value for value in report['validation']['cross_source_discrepancies'].values())
    return {'bundle': bundle, 'components_path': components_path, 'components': components,
            'sources': sources, 'report': report, 'statistics': statistics}


def validate_component_candidate(link, bundle_entry, structured):
    source = link['source_component']
    assert source['path'] == bundle_entry['structured_components']
    assert path_in_repo(source['path']) == structured['components_path']
    assert evidence_hash(structured['components_path'])[0] == source['sha256']
    ref = source['reference_designator']
    assert ref == link['observed_reference_designator'] == link['schematic']['reference_designator']
    component = structured['components'][ref]
    assert source['bom_item_id'] == component['bom_item_id']
    assert source['manufacturer_part_number_text'] == component['manufacturer_part_number_text']
    assert source['native_silk'] == component['native_part']['properties'].get('SILK')
    assert source['footprint_identifier'] == component['primitive_body_properties']['JEDEC_TYPE']
    bom_source, bom_record = source['bom_source'], structured['sources']['SCH-90828_C.BOM.xlsx']
    assert path_in_repo(bom_source['file']) == path_in_bundle(structured['bundle'], bom_record['path'])
    assert bom_source['sha256'] == bom_record['sha256']
    assert all(bom_source[key] == component['bom_source'][key] for key in ('sheet', 'row', 'range'))
    schematic = link['schematic']
    candidates = [row for row in component['schematic_text_candidates'] if row['id'] == schematic['occurrence_id']]
    assert len(candidates) == 1 and candidates[0]['page'] == schematic['page_1based']
    assert schematic['page_1based'] in {section['page_from_P_PATH'] for section in component['native_part']['sections']}
    assert schematic['value_text'] == component['primitive_body_properties']['VALUE']
    assert schematic['function_label'] == source['native_silk']
    assert link['source_board_model'] == structured['report']['board']
    assert link['source_revision'] == structured['report']['source_revision']


def validate_review_crops(link, annotated, index, occurrences, check_pixels):
    if 'photo_review' in link:
        review = link['photo_review']
        crop_path = path_in_repo(review['path'])
        assert evidence_hash(crop_path)[0] == review['sha256']
        assert link['review_preview'] == review['path']
        x0, y0, x1, y1 = review['source_crop_xyxy_pixels']
        assert all(isinstance(value, int) for value in (x0, y0, x1, y1))
        assert 0 <= x0 < x1 <= annotated['image_width']
        assert 0 <= y0 < y1 <= annotated['image_height']
        seed = next(row for row in annotated['annotations'] if row['id'] == link['annotation_id'])
        sx0, sy0, sx1, sy1 = seed['xyxy_pixels']
        assert x0 <= sx0 < sx1 <= x1 and y0 <= sy0 < sy1 <= y1
        angle, scale = review['rotation_degrees_counterclockwise'], review['scale']
        assert angle in (0, 90, 180, 270) and isinstance(scale, int) and scale > 0
        assert review['resampling'] == 'nearest_neighbor'
        if check_pixels:
            from PIL import Image, ImageChops
            with Image.open(path_in_repo(link['image_path'])) as original, Image.open(crop_path) as actual:
                expected = original.crop((x0, y0, x1, y1))
                transforms = {90: Image.Transpose.ROTATE_90, 180: Image.Transpose.ROTATE_180, 270: Image.Transpose.ROTATE_270}
                if angle:
                    expected = expected.transpose(transforms[angle])
                expected = expected.resize((expected.width * scale, expected.height * scale), Image.Resampling.NEAREST)
                assert actual.size == expected.size
                assert ImageChops.difference(expected.convert('RGB'), actual.convert('RGB')).getbbox() is None
    schematic = link['schematic']
    if 'review_crop' in schematic:
        review = schematic['review_crop']
        assert evidence_hash(path_in_repo(review['path']))[0] == review['sha256']
        page = next(row for row in index['pages'] if row['page'] == schematic['page_1based'])
        x0, y0, x1, y1 = review['bbox_pt']
        assert 0 <= x0 < x1 <= page['width_pt'] and 0 <= y0 < y1 <= page['height_pt']
        sx0, sy0, sx1, sy1 = occurrences[schematic['occurrence_id']]['bbox_pt']
        assert x0 <= sx0 < sx1 <= x1 and y0 <= sy0 < sy1 <= y1
        assert review['resolution_dpi'] > 0 and review['renderer']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-photo-crops', action='store_true', help='Require materialized LFS images and Pillow; reproduce every declared photo-review crop pixel-for-pixel')
    args = parser.parse_args()
    links = read_json('annotations/component-source-links.json')
    assert links['path_base'] == 'repository_root'
    seeds = read_json('annotations/nxp-component-seeds.json')
    assert seeds == read_json('data/photo-model/nxp-component-seeds.json')
    assert seeds['path_base'] == 'repository_root'
    assert evidence_hash(path_in_repo(seeds['source_image']))[0] == seeds['source_image_sha256']
    bundles = read_json('source-bundles.json')
    assert bundles == read_json('data/photo-model/source-bundles.json')
    nxp_bundle = bundles['nxp_frdm_mcxn236_board']
    archive_count = validate_archive(path_in_repo(nxp_bundle['design_archive_inventory']))
    structured = validate_structured_sources(nxp_bundle)
    ids = set()
    for link in links['links']:
        assert link['id'] not in ids
        ids.add(link['id'])
        annotated = read_json(link['annotation_path'])
        matches = [row for row in annotated['annotations'] if row['id'] == link['annotation_id']]
        assert len(matches) == 1
        annotation = matches[0]
        assert annotation['source_link_id'] == link['id']
        assert annotation['reference_designator'] == link['observed_reference_designator']
        assert annotated['source_image'] == link['image_path']
        assert evidence_hash(path_in_repo(link['image_path']))[0] == link['image_sha256']
        assert annotated['board_identity']['model'] == link['source_board_model']
        assert annotated['board_identity']['revision'] == link['specimen_revision']
        if link['specimen_revision'] is None:
            assert annotated['board_identity']['revision_status'] == 'unconfirmed'
            assert link['match_status'] == 'model_match_revision_unconfirmed'
            assert link['exact_installed_part_mapping'] is False
            assert link['manufacturer_part_number'] is None
            assert annotation['manufacturer_part_number'] is None
        schematic = link['schematic']
        pdf = path_in_repo(schematic['path'])
        assert evidence_hash(pdf)[0] == schematic['sha256']
        index, occurrences, indexed_pdf = validate_index(path_in_repo(schematic['reference_index']))
        assert pdf == indexed_pdf
        candidates = [occurrences[key] for key in index['by_refdes'][schematic['reference_designator']]]
        assert any(row['page'] == schematic['page_1based'] and row['id'] == schematic['occurrence_id'] for row in candidates)
        assert schematic['reference_designator'] == link['observed_reference_designator']
        validate_review_crops(link, annotated, index, occurrences, args.check_photo_crops)
        if link['source_board_model'] == 'FRDM-MCXN236':
            assert '/nxp-frdm-mcxn236/' in schematic['path']
            assert nxp_bundle['schematic_reference_index'] == schematic['reference_index']
            if link['specimen_revision'] is None:
                assert nxp_bundle['exact_component_mapping'] is False
            validate_component_candidate(link, nxp_bundle, structured)
    assert ids == {row['source_link_id'] for row in seeds['annotations'] if row.get('source_link_id')}
    status = read_json('data/board-sources/nxp-frdm-mcxn947/REFERENCE_STATUS.json')
    relocation = status['historical_photo_relocation']
    assert not (ROOT / relocation['path_at_initial_import']).exists()
    assert evidence_hash(path_in_repo(relocation['current_path']))[0] == relocation['sha256']
    assert status['exact_annotation_use'] is False
    assert bundles['nxp_frdm_mcxn236_board']['identification_photo'] == relocation['current_path']
    imported = read_json('import-summary.json')['files']
    moved = [row for row in imported if row['path'] == relocation['current_path']]
    assert len(moved) == 1 and moved[0]['sha256'] == relocation['sha256']
    assert moved[0]['path_at_initial_import'] == relocation['path_at_initial_import']
    counts = structured['statistics']
    print(f"Validated {len(ids)} photo/source candidate links, {archive_count} archive members, "
          f"{counts['native_parts']} source references, {counts['electrical_net_records']} electrical nets "
          f"plus {counts['no_connect_group_nodes']} isolated NC pin records, schematic candidates, and relocated photo hash.")


if __name__ == '__main__':
    main()
