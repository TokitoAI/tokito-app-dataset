"""Package reviewed photo identities and source links for local camera registration.

No generic detector class is promoted to a reference designator or part number.
Only photo-located contacts and existing source-linked parts receive geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Local assets/references directory')
    args = parser.parse_args()
    output = args.output.resolve()
    images_dir = output / 'images'
    images_dir.mkdir(parents=True, exist_ok=True)
    hierarchy_path = ROOT / 'data/photo-model/label-hierarchy.json'
    hierarchy = json.loads(hierarchy_path.read_text(encoding='utf-8'))
    names = {row['class_id']: row['display_name'] for row in json.loads(
        (ROOT / 'data/photo-model/board-class-display-names.json').read_text())['ordered_classes']}
    templates = []
    skipped_unreviewed_pins = 0
    for image in hierarchy['images']:
        if not image['parts']:
            continue
        source = ROOT / image['image_path']
        if sha(source) != image['image_sha256']:
            raise RuntimeError(f'Photo digest mismatch: {source.name}')
        with Image.open(source) as raw:
            photo = ImageOps.exif_transpose(raw).convert('RGB')
            if photo.size != (image['image_width'], image['image_height']):
                raise RuntimeError(f'Photo coordinate dimensions mismatch: {source.name}')
            photo.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
            target = images_dir / source.name
            photo.save(target, quality=95)
            width, height = photo.size
        labels = []
        for part in image['parts']:
            candidate = part.get('source_component_candidate')
            if candidate:
                refdes = candidate['source_refdes']
                value = candidate.get('source_manufacturer_part_number_text')
                label = f'{refdes} — {value} [source candidate]' if value else refdes
                labels.append({
                    'id': part['id'], 'kind': 'part', 'label': label,
                    'bbox_xyxy_normalized': part['bbox_xyxy_normalized'],
                    'identity_status': 'source_candidate_installed_part_unconfirmed',
                    'source': candidate,
                })
            for pin in part['pins']:
                box = pin.get('photo_bbox_xyxy_pixels')
                if box is None:
                    continue
                status = pin['mapping_status']
                if status not in {'reviewed_photo_pin_with_source_link', 'reviewed_photo_pin_with_source_document_link',
                                   'reviewed_photo_contact_with_printed_alias'}:
                    # A source-only or candidate contact has no safe camera label.
                    skipped_unreviewed_pins += 1
                    continue
                if pin.get('printed_alias'):
                    label = pin['printed_alias'] + ' [printed alias]'
                else:
                    refdes = candidate['source_refdes'] if candidate else part.get('observed_reference_designator')
                    if not refdes:
                        raise RuntimeError('Numbered contact has no parent reference')
                    suffix = pin.get('source_net_name') or pin.get('symbol_pin_name') or ''
                    label = f'{refdes}.{pin["pin_number"]}' + (f' — {suffix}' if suffix else '')
                labels.append({
                    'id': pin['photo_pin_annotation_id'], 'kind': 'pin', 'label': label,
                    'bbox_xyxy_normalized': [box[0] / image['image_width'], box[1] / image['image_height'],
                                             box[2] / image['image_width'], box[3] / image['image_height']],
                    'identity_status': status,
                    'source': {key: value for key, value in pin.items() if key != 'photo_bbox_xyxy_pixels'},
                })
        templates.append({
            'id': image['image_file'], 'class_id': image['board']['class_id'],
            'board': names[image['board']['class_id']],
            'image': f'images/{source.name}', 'image_sha256': sha(target),
            'width': width, 'height': height,
            'source_photo': image['image_path'], 'source_photo_sha256': image['image_sha256'],
            'board_bbox_xyxy_normalized': image['board']['bbox_xyxy_normalized'],
            'source_reference': image['board']['source_reference'], 'labels': labels,
        })
    review_path = ROOT / 'data/phone-captures/2026-10-10/reviewed-scan-references.json'
    if review_path.is_file():
        review = json.loads(review_path.read_text(encoding='utf-8'))
        if review['release_eligible'] or review['evaluation_valid']:
            raise RuntimeError('Scan references must remain experimental')
        for row in review['templates']:
            source = ROOT / row['image_path']
            if sha(source) != row['image_sha256']:
                raise RuntimeError(f'Scan photo digest mismatch: {source.name}')
            with Image.open(source) as raw:
                photo = ImageOps.exif_transpose(raw).convert('RGB')
                photo.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
                target = images_dir / source.name
                photo.save(target, quality=95)
                width, height = photo.size
            for label in row['labels']:
                box = label['bbox_xyxy_normalized']
                if not (len(box) == 4 and all(0 <= x <= 1 for x in box) and box[0] < box[2] and box[1] < box[3]):
                    raise RuntimeError(f'Invalid reviewed label box: {label["id"]}')
                label['source']['scan_review_sha256'] = sha(review_path)
            entry = {
                'id': row['id'], 'class_id': row['class_id'], 'board': row['board'],
                'image': f'images/{source.name}', 'image_sha256': sha(target),
                'width': width, 'height': height, 'source_photo': row['image_path'],
                'source_photo_sha256': row['image_sha256'],
                'board_bbox_xyxy_normalized': row['board_bbox_xyxy_normalized'],
                'source_reference': row['source_reference'], 'labels': row['labels'],
            }
            for key in ('pose_corners_normalized', 'pose_corner_status', 'pose_asset_id', 'pose_alignment_scope',
                        'pose_landmark_kind', 'pose_landmark_ids', 'pose_metric_landmarks_metres',
                        'metric_landmark_source', 'corner_uncertainty_pixels'):
                if key in row:
                    entry[key] = row[key]
            templates.append(entry)
    report = {
        'schema_version': '1.0', 'release_eligible': False, 'evaluation_valid': False,
        'scope': 'Known photographed specimens only; partial source-linked parts and reviewed contacts',
        'hierarchy_sha256': sha(hierarchy_path), 'templates': templates,
        'scan_review_sha256': sha(review_path) if review_path.is_file() else None,
        'skipped_unreviewed_pin_count': skipped_unreviewed_pins,
        'limits': [
            'A board-family detector score cannot enable labels without image registration.',
            'Template registration is not independent specimen or global-board recognition.',
            'BOM candidates remain unconfirmed installed parts; source-only pins have no camera geometry.',
            'There are no labels for unreviewed or unlabeled component instances.',
        ],
        'registration_policy': {
            'long_edge': 1280, 'orb_features': 2500, 'ratio_test': 0.7,
            'ransac_threshold_pixels': 3.0, 'minimum_inliers': 20,
            'minimum_inlier_fraction': 0.5, 'minimum_template_hull_fraction': 0.15,
            'minimum_occupied_template_grid_cells': 6, 'maximum_median_reprojection_pixels': 2.0,
            'maximum_p95_reprojection_pixels': 4.0,
            'pin_projection_policy': 'p95 registration error must be less than one quarter of projected contact short edge',
        },
    }
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'templates': len(templates), 'parts': sum(x['kind'] == 'part' for t in templates for x in t['labels']),
                      'contacts': sum(x['kind'] == 'pin' for t in templates for x in t['labels']),
                      'skipped_unreviewed_pins': skipped_unreviewed_pins, 'output': str(output)}))


if __name__ == '__main__':
    main()
