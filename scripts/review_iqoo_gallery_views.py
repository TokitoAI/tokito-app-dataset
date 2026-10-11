"""Record visually checked board/view references from the October 11 gallery.

This is a capture-view index, not a component-mask or pose-calibration export.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / 'data/phone-captures/2026-10-11/gallery'
MANIFEST = GALLERY / 'manifest.json'
OUTPUT = GALLERY / 'view-review.json'

# Only full original photos whose board family and visible face were checked.
# An oblique face view does not establish which one of four physical side slots
# it covers; no single still establishes a same-specimen flip sequence.
REVIEWS = {
    'IMG_20261011_012207.jpg': ('esp8266_nodemcu_esp12e_clone_unknown_variant', 'component_face', 'full-board frontal view'),
    'IMG_20261011_012141.jpg': ('esp32_devkit_30pin_unknown_variant', 'component_face', 'full-board frontal view'),
    'IMG_20261011_011853.jpg': ('nxp_frdm_mcxn236_board', 'component_face', 'full-board frontal view'),
    'IMG_20261011_011939.jpg': ('nxp_frdm_mcxn236_board', 'oblique_component_face', 'board thickness and component-face perspective visible; physical side unregistered'),
    'IMG_20261011_012109.jpg': ('ultimainboard_2_1_4', 'component_face', 'full-board frontal view'),
    'IMG_20261011_012119.jpg': ('ultimainboard_2_1_4', 'solder_face', 'full-board backside with solder pads and printed test points'),
}


def build():
    intake = json.loads(MANIFEST.read_text(encoding='utf-8'))
    rows = {Path(row['path']).name: row for row in intake['images']}
    reviewed = []
    for name, (family, view, evidence) in REVIEWS.items():
        source = rows[name]
        path = ROOT / source['path']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != source['sha256']:
            raise ValueError(f'intake hash mismatch: {name}')
        if sorted((source['width'], source['height'])) != [3072, 4096]:
            raise ValueError(f'expected full original rather than crop: {name}')
        reviewed.append({
            'image_path': source['path'], 'image_sha256': digest,
            'board_family': family, 'visible_face': view,
            'visual_evidence': evidence, 'capture_session_id': intake['capture_session_id'],
            'physical_specimen_id': None, 'camera_intrinsics_registered': False,
            'metric_pose_verified': False, 'component_masks_complete': False,
            'training_export_eligible': False, 'evaluation_eligible': False,
        })
    return {
        'schema_version': '1.0', 'source_manifest': str(MANIFEST.relative_to(ROOT)),
        'review_scope': 'board family and visible face only; no component, pin, mesh or pose labels',
        'same_specimen_front_back_verified': False,
        'continuous_flip_sequence_verified': False,
        'four_distinct_oblique_sides_verified': False,
        'images': reviewed,
    }


if __name__ == '__main__':
    with OUTPUT.open('w', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(build(), indent=2) + '\n')
    print(str(OUTPUT))
