"""Validate ESP12E saved AR joins with LFS pointers or downloaded assets."""
import json
from pathlib import Path

from build_ar_alignment_dataset import content_sha, sha

ROOT = Path(__file__).resolve().parents[1]


def validate(root, index):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(not index['release_eligible'] and not index['training_export_eligible']
            and not index['evaluation_valid'], 'Partial annotations cannot activate release')
    for source in index['source_files']:
        require(sha(root / source['path']) == source['sha256'], 'Stale annotation source digest')
    require(content_sha(root / index['image_path']) == index['image_sha256'], 'Image digest mismatch')
    base = root / 'data/video-captures/2026-10-10/esp12e-keyframes'
    bodies = json.loads((base / 'reviewed-component-masks.json').read_text())
    module = json.loads((base / 'reviewed-module-contacts.json').read_text())
    require(bodies['image_path'] == module['image_path'] == index['image_path'], 'Mixed source images')
    records = {row['instance_id']: row for row in index['instances']}
    require(len(records) == len(index['instances']), 'Duplicate identities')
    specimen = index['physical_specimen_id']
    require(index['required_split_group'] == specimen, 'Specimen split mismatch')
    for row in records.values():
        require(row['parent_id'] in set(records) | {specimen}, 'Missing parent')
        require(row['glb_selector'] is None, 'Unverified mesh selector')
    width, height = index['image_dimensions']
    for body in bodies['masks']:
        row = records[body['instance_id']]
        require(row['parent_id'] == body.get('parent_component_id', specimen), 'Changed body parent')
        require(row['visible_polygon_normalized'] == [[x / width, y / height]
                for x, y in body['polygon_xy_pixels']], 'Changed body geometry')
    names = ['RST','ADC','EN','IO16','IO14','IO12','IO13','VCC','CS0','MISO','IO9',
             'IO10','MOSI','SCLK','GND','IO15','IO2','IO0','IO4','IO5','RXD','TXD']
    require([pin['source_pin_name'] for pin in module['contacts']] == names,
            'Module names disagree with reviewed manufacturer table')
    require([pin['source_module_pin_number'] for pin in module['contacts']] == list(range(1, 23)),
            'Module numbering mismatch')
    for pin in bodies['pin_annotations'] + module['contacts']:
        row = records[pin['instance_id']]
        x, y = pin['center_xy_pixels']
        require(row['point_normalized'] == [x / width, y / height], 'Changed contact geometry')
        require(row['parent_id'] == pin.get('parent_component_id', specimen), 'Changed contact parent')
        require(row['source_module_pin_number'] == pin.get('source_module_pin_number')
                and row['source_pin_name'] == pin.get('source_pin_name')
                and row['printed_alias'] == pin.get('printed_alias'), 'Swapped contact identity')
        require(not row['electrical_continuity_verified'] and row['metric_position_metres'] is None,
                'Unverified electrical or metric activation')
    require(len(records) == 1 + len(bodies['masks']) + len(bodies['pin_annotations'])
            + len(module['contacts']), 'Unexpected instance coverage')
    spacing = json.loads((root / 'data/ar-alignment/esp12e-module-spacing-constraints.json').read_text())
    require(spacing['source_contacts_sha256'] == sha(base / 'reviewed-module-contacts.json'),
            'Stale spacing source')
    require(not spacing['calibration_eligible'] and spacing['absolute_landmarks'] == [],
            'Relative distances cannot activate calibration')
    expected = [(a, a + 1) for first, last in ((1,8),(9,14),(15,22))
                for a in range(first,last)]
    require([tuple(pair['module_pin_numbers']) for pair in spacing['constraints']] == expected,
            'Wrong spacing pairs')
    for pair in spacing['constraints']:
        a, b = [module['contacts'][number - 1] for number in pair['module_pin_numbers']]
        require(pair['contact_ids'] == [a['instance_id'], b['instance_id']]
                and pair['image_points_xy_pixels'] == [a['center_xy_pixels'], b['center_xy_pixels']],
                'Spacing contact association mismatch')
        require(pair['nominal_distance_metres'] == .002, 'Wrong source pitch')
    return len(records)


if __name__ == '__main__':
    index = json.loads((ROOT / 'data/ar-alignment/esp12e-video-instances.json').read_text())
    count = validate(ROOT, index)
    print(f'Validated {count} ESP12E AR records; production calibration remains unverified')
