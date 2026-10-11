"""Join reviewed ESP-12E photo/video bodies without inventing part identities."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTO = ROOT / 'annotations/esp8266-dense-component-review.json'
VIDEO = ROOT / 'annotations/esp8266-video-component-review.json'
MANIFEST = ROOT / 'data/video-captures/2026-10-10/esp12e-keyframes/manifest.json'
OUTPUT = ROOT / 'data/ar-alignment/esp12e-photo-video-instance-crosswalk.json'

# The 18 ending-keyframe bodies and two opening-keyframe resistors were compared
# against the photo overlays. Ordering is physical, never schematic refdes.
PAIRS = [
    ('usb_serial_controller_body', 'usb_serial_controller'),
    ('regulator_body', 'three_lead_regulator_candidate'),
    ('rf_module_shield', 'esp12e_rf_shield'),
    ('micro_usb_shell', 'micro_usb'),
    ('rst_button_body', 'rst_button'),
    ('flash_button_body', 'flash_button'),
    ('resistor_103_above_regulator', 'module_lower_resistor'),
    ('resistor_above_transistor', 'resistor_221'),
    ('resistor_103_between_transistors', 'resistor_103_lower'),
    ('three_lead_body_upper', 'three_terminal_upper'),
    ('three_lead_body_lower', 'three_terminal_lower'),
    ('capacitor_marked_106', 'polarized_capacitor_middle'),
    ('capacitor_marked_10_16V', 'polarized_capacitor_left'),
    ('passive_left_below_module', 'module_lower_capacitor_left'),
    ('passive_right_below_module', 'module_lower_capacitor_mid'),
    ('passive_above_regulator_right', 'module_lower_capacitor_right'),
    ('passive_below_controller_upper', 'usb_upper_capacitor_a'),
    ('passive_below_controller_lower', 'usb_upper_capacitor_b'),
    ('resistor_upper_224', 'upper_left_resistor_a'),
    ('resistor_upper_104', 'upper_left_resistor_b'),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    photo, video = [json.loads(path.read_text(encoding='utf-8')) for path in (PHOTO, VIDEO)]
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    frames = {Path(row['image_path']).name: row for row in manifest['keyframes']}
    if photo['physical_specimen_id'] != video['physical_specimen_id']:
        raise ValueError('Source reviews have different specimen IDs')
    # The dense photo file has four same-specimen frames; each suffix is unique
    # within an image. The first full-resolution photo is the reviewed join view.
    photo_rows = {row['instance_id'].split(':')[-1]: row for row in photo['masks']
                  if row['instance_id'].startswith('IMG_20261010_092221.jpg:')}
    video_rows = {row['instance_id'].split(':')[-1]: row for row in video['masks']}
    if len(photo_rows) != 23 or len(video_rows) != 20:
        raise ValueError('Reviewed body coverage changed; re-review crosswalk')
    if len({a for a, _ in PAIRS}) != len(PAIRS) or len({b for _, b in PAIRS}) != len(PAIRS):
        raise ValueError('Crosswalk is not one-to-one')
    joins = []
    for video_key, photo_key in PAIRS:
        v, p = video_rows[video_key], photo_rows[photo_key]
        frame_name = v['instance_id'].split(':', 1)[0]
        if frame_name not in frames:
            raise ValueError(f'Video frame absent from reviewed manifest: {frame_name}')
        if v['class_name'] != p['class_name'] and (v['class_name'], p['class_name']) != ('rf_module', 'rf_shield'):
            raise ValueError(f'Class mismatch: {video_key} / {photo_key}')
        joins.append({
            'canonical_local_instance_id': f"{photo['physical_specimen_id']}:{photo_key}",
            'photo_mask_instance_id': p['instance_id'],
            'video_mask_instance_id': v['instance_id'],
            'video_image_path': frames[frame_name]['image_path'],
            'video_image_sha256': frames[frame_name]['image_sha256'],
            'kind': p['class_name'],
            'correspondence_status': 'visual_candidate_same_specimen_assumed',
            'exact_order_code_verified': False,
            'source_refdes_verified': False,
            'selectable_3d_mesh_verified': False,
        })
    return {
        'schema_version': '1.0',
        'board_family': photo['board_family'],
        'physical_specimen_id': photo['physical_specimen_id'],
        'specimen_assignment_status': 'same_bench_specimen_assumed_for_leakage_control',
        'required_split_group': photo['physical_specimen_id'],
        'photo_review_path': PHOTO.relative_to(ROOT).as_posix(),
        'photo_review_sha256': digest(PHOTO),
        'video_review_path': VIDEO.relative_to(ROOT).as_posix(),
        'video_review_sha256': digest(VIDEO),
        'video_manifest_path': MANIFEST.relative_to(ROOT).as_posix(),
        'video_manifest_sha256': digest(MANIFEST),
        'photo_image_path': photo['image_path'],
        'photo_image_sha256': photo['image_sha256'],
        'joins': joins,
        'unjoined_photo_instance_ids': sorted(row['instance_id'] for key, row in photo_rows.items()
                                              if key not in {b for _, b in PAIRS}),
        'training_export_eligible': False,
        'evaluation_valid': False,
        'ar_activation_eligible': False,
        'limitations': [
            'Cross-view body correspondence is visual and specimen identity is assumed, not physically verified.',
            'Video and photo are the same assumed specimen and cannot form independent train/evaluation splits.',
            'No carrier schematic refdes, exact installed order code, metric pose, or selectable mesh is proved.',
            'Video views are front-side; underside, four oblique sides, and physical flip remain unverified.',
        ],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    payload = json.dumps(build(), indent=2) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != payload:
            raise SystemExit('ESP-12E photo/video crosswalk is stale')
    else:
        OUTPUT.write_text(payload, encoding='utf-8')
    print('ESP-12E photo/video crosswalk checked: 20 candidate joins')
