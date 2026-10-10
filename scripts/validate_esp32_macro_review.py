"""Validate the reviewed ESP32 macro evidence without promoting partial labels."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'data/video-captures/2026-10-10/esp32-keyframes/reviewed-front-macro.json'


def validate(review_path=REVIEW):
    data = json.loads(Path(review_path).read_text(encoding='utf-8'))
    assert data['training_export_eligible'] is False
    assert data['production_eligible'] is False
    assert data['coverage'].startswith('partial_')
    image = ROOT / data['image_path']
    assert hashlib.sha256(image.read_bytes()).hexdigest() == data['image_sha256']
    ids = set()
    for item in data['masks'] + data['contacts']:
        assert item['instance_id'] not in ids
        ids.add(item['instance_id'])
        points = item.get('polygon_xy_pixels', [item.get('point_xy_pixels')])
        for x, y in points:
            assert 0 <= x < data['image_width'] and 0 <= y < data['image_height']
        if 'polygon_xy_pixels' in item:
            assert item['installed_order_code_confirmed'] is False
            assert item['exact_part_name'] is None
            assert item['class_name'] not in ['mounting_hole', 'header_contact']
        else:
            assert item['not_component_body'] is True
            assert item['numeric_chip_pin'] is None
            assert item['function_mapping_verified'] is False
            assert item['source_metric_xyz_m'] is None
    assert data['unreviewed_regions']
    return {'reviewed_body_count': len(data['masks']), 'printed_contact_count': len(data['contacts']),
            'exhaustive_training_coverage': False, 'exact_order_codes_verified': False}


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
