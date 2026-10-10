"""Bind visually reviewed Ultimaker hole centers to the native PCB frame.

Four planar correspondences per still define a candidate homography exactly.
They do not validate physical camera pose, board revision or flip tracking.
"""
import hashlib
import json
import re
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / 'data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb'
GEOMETRY = ROOT / 'data/board-sources/ultimainboard-2.1.4/ar-source-candidate/contact-completion/geometry-coverage.json'
GALLERY = ROOT / 'data/phone-captures/2026-10-11/gallery'
INTAKE = GALLERY / 'manifest.json'
VIEW_REVIEW = GALLERY / 'view-review.json'
OUTPUT = ROOT / 'data/ar-alignment/ultimaker-planar-anchor-candidates.json'
PREVIEW = ROOT / 'previews/ultimaker-planar-anchor-candidates.jpg'

# Original image pixels. Enlarged crops were inspected for all eight centres;
# centers have about 15-25 px uncertainty due hollow/metallic spacer contrast.
PHOTO_HOLES = {
    'IMG_20261011_012109.jpg': {
        'SP1': (472, 1157), 'SP2': (465, 2667),
        'SP3': (3934, 751), 'SP4': (3963, 2329),
    },
    'IMG_20261011_012119.jpg': {
        'SP1': (2509, 3949), 'SP2': (648, 3961),
        'SP3': (2360, 158), 'SP4': (690, 128),
    },
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_holes():
    lines = PCB.read_text(encoding='utf-8').splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith('\t(footprint ')]
    holes = {}
    for index, line in enumerate(lines):
        if line.strip() != '(drill 4.22)':
            continue
        start = max(i for i in starts if i < index)
        header = '\n'.join(lines[start:start + 15])
        if 'Spacer M3-10ET' not in header:
            raise ValueError('4.22 mm drill belongs to an unexpected footprint')
        xy = re.search(r'\(at ([\d.]+) ([\d.]+)\)', header)
        ref = re.search(r'\(property "Reference" "(SP\d+)"', header)
        if not xy or not ref or ref.group(1) in holes:
            raise ValueError('ambiguous native spacer hole')
        holes[ref.group(1)] = [float(xy.group(1)), float(xy.group(2))]
    if set(holes) != {'SP1', 'SP2', 'SP3', 'SP4'}:
        raise ValueError(f'expected SP1-SP4, found {sorted(holes)}')
    return holes


def source_outline():
    lines = PCB.read_text(encoding='utf-8').splitlines()
    endpoints = []
    for index, line in enumerate(lines):
        if line.strip() != '(gr_line':
            continue
        end = next((i for i in range(index + 1, len(lines)) if lines[i] == '\t)'), None)
        if end is None:
            raise ValueError('unterminated board outline segment')
        block = '\n'.join(lines[index:end + 1])
        if '(layer "Edge.Cuts")' not in block:
            continue
        for x, y in re.findall(r'\((?:start|end) ([\d.]+) ([\d.]+)\)', block):
            endpoints.append((float(x), float(y)))
    if len(endpoints) != 8:
        raise ValueError(f'expected four outline segments, found {len(endpoints) // 2}')
    xs, ys = [point[0] for point in endpoints], [point[1] for point in endpoints]
    corners = [[min(xs), min(ys)], [max(xs), min(ys)],
               [max(xs), max(ys)], [min(xs), max(ys)]]
    if abs(max(xs) - min(xs) - 175) > .01 or abs(max(ys) - min(ys) - 79) > .01:
        raise ValueError('unexpected native board dimensions')
    return corners


def source_reference_xy(reference):
    lines = PCB.read_text(encoding='utf-8').splitlines()
    found = []
    for index, line in enumerate(lines):
        if not line.startswith('\t(footprint '):
            continue
        header = '\n'.join(lines[index:index + 15])
        if not re.search(r'\(property "Reference" "' + re.escape(reference) + r'"', header):
            continue
        xy = re.search(r'\(at ([\d.]+) ([\d.]+)', header)
        if xy:
            found.append([float(xy.group(1)), float(xy.group(2))])
    if len(found) != 1:
        raise ValueError(f'expected one native footprint {reference}: {found}')
    return found[0]


def build():
    holes = source_holes()
    outline = source_outline()
    geometry = json.loads(GEOMETRY.read_text(encoding='utf-8'))
    intake = json.loads(INTAKE.read_text(encoding='utf-8'))
    views = json.loads(VIEW_REVIEW.read_text(encoding='utf-8'))
    image_rows = {Path(row['path']).name: row for row in intake['images']}
    view_rows = {Path(row['image_path']).name: row for row in views['images']}
    ox, oy = geometry['source_export_origin_mm']
    frames, previews = [], []
    order = ('SP1', 'SP2', 'SP3', 'SP4')
    board_xy = np.float32([holes[ref] for ref in order])
    source_u1 = source_reference_xy('U1')
    for name, points in PHOTO_HOLES.items():
        source = image_rows[name]
        review = view_rows[name]
        path = ROOT / source['path']
        if digest(path) != source['sha256'] or digest(path) != review['image_sha256']:
            raise ValueError(f'photo hash mismatch: {name}')
        if review['board_family'] != 'ultimainboard_2_1_4':
            raise ValueError(f'board-family review mismatch: {name}')
        if set(points) != set(order):
            raise ValueError(f'missing hole in {name}')
        image = cv2.imread(str(path))
        height, width = image.shape[:2]
        if [width, height] != [source['width'], source['height']]:
            raise ValueError(f'image dimensions differ from intake: {name}')
        photo_xy = np.float32([points[ref] for ref in order])
        a = np.array(points['SP3']) - np.array(points['SP1'])
        b = np.array(points['SP2']) - np.array(points['SP1'])
        signed_area = float(a[0] * b[1] - a[1] * b[0])
        parity = 'same_as_source_face' if signed_area > 0 else 'mirrored_from_source_face'
        expected_parity = ('same_as_source_face' if review['visible_face'] == 'component_face'
                           else 'mirrored_from_source_face')
        if parity != expected_parity:
            raise ValueError(f'face orientation contradicts hole correspondences: {name}')
        image_to_source = cv2.getPerspectiveTransform(photo_xy, board_xy)
        source_to_image = cv2.getPerspectiveTransform(board_xy, photo_xy)
        projected_outline = cv2.perspectiveTransform(
            np.float32(outline).reshape(1, 4, 2), source_to_image)[0]
        anchors = [{
            'landmark_id': ref,
            'source_board_xy_mm': holes[ref],
            'asset_xz_metres': [round((holes[ref][0] - ox) / 1000, 9),
                                round((holes[ref][1] - oy) / 1000, 9)],
            'image_xy_pixels': list(points[ref]),
            'image_center_uncertainty_pixels': 25,
            'feature': '4.22mm spacer hole centre',
            'review_status': 'manual_crop_review_candidate',
        } for ref in order]
        frames.append({
            'image_path': source['path'], 'image_sha256': source['sha256'],
            'image_dimensions_wh': [width, height], 'visible_face': review['visible_face'],
            'capture_session_id': intake['capture_session_id'],
            'physical_specimen_id': None,
            'source_to_image_planar_parity': parity,
            'landmarks': anchors,
            'source_board_outline_xy_mm': outline,
            'predicted_image_outline_xy_pixels': np.round(projected_outline.astype(float), 1).tolist(),
            'image_to_source_board_homography': np.round(image_to_source, 12).tolist(),
            'source_board_to_image_homography': np.round(source_to_image, 9).tolist(),
            'homography_fit_note': 'Exactly four input pairs; zero fit residual by construction is not an independent accuracy test.',
            'metric_camera_pose_verified': False, 'same_specimen_flip_verified': False,
            'ar_calibration_release_eligible': False,
        })
        if review['visible_face'] == 'component_face':
            predicted = cv2.perspectiveTransform(
                np.float32([[source_u1]]), source_to_image)[0, 0]
            # Independent visible-package check. The large dark U1 body is the
            # largest connected dark object in this inspected original crop.
            crop_x, crop_y, crop_w, crop_h = 3000, 1500, 800, 700
            crop = image[crop_y:crop_y + crop_h, crop_x:crop_x + crop_w]
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            binary = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY_INV)[1]
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            bx, by, bw, bh = max((cv2.boundingRect(c) for c in contours),
                                 key=lambda rect: rect[2] * rect[3])
            if not (250 <= bw <= 450 and 250 <= bh <= 450):
                raise ValueError('U1 body candidate has unexpected dimensions')
            observed = [crop_x + bx + bw / 2, crop_y + by + bh / 2]
            residual = float(np.linalg.norm(predicted - observed))
            frames[-1]['independent_visible_component_check'] = {
                'reference': 'U1', 'source_footprint_xy_mm': source_u1,
                'projected_footprint_center_xy_pixels': np.round(predicted.astype(float), 1).tolist(),
                'photo_body_bbox_xywh_pixels': [crop_x + bx, crop_y + by, bw, bh],
                'photo_body_center_xy_pixels': observed,
                'center_offset_pixels': round(residual, 1),
                'projected_center_inside_photo_body': bool(
                    crop_x + bx <= predicted[0] <= crop_x + bx + bw and
                    crop_y + by <= predicted[1] <= crop_y + by + bh),
                'measurement_scope': 'same-photo U1 dark-body candidate; not independent specimen or pose validation',
            }
            if not frames[-1]['independent_visible_component_check']['projected_center_inside_photo_body']:
                raise ValueError('source U1 projection misses the photographed body')
        preview = cv2.resize(image, (round(width * min(1200 / width, 1200 / height)),
                                     round(height * min(1200 / width, 1200 / height))))
        scale_x, scale_y = preview.shape[1] / width, preview.shape[0] / height
        image_outline = np.round(projected_outline * [scale_x, scale_y]).astype(np.int32)
        cv2.polylines(preview, [image_outline], True, (255, 80, 0), 3)
        for ref in order:
            px, py = points[ref]
            center = (round(px * scale_x), round(py * scale_y))
            cv2.drawMarker(preview, center, (0, 0, 255), cv2.MARKER_CROSS, 22, 3)
            cv2.putText(preview, ref, (center[0] + 12, center[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 255), 2)
        if 'independent_visible_component_check' in frames[-1]:
            check = frames[-1]['independent_visible_component_check']
            px, py = check['projected_footprint_center_xy_pixels']
            cv2.drawMarker(preview, (round(px * scale_x), round(py * scale_y)),
                           (0, 170, 0), cv2.MARKER_CROSS, 20, 3)
            cv2.putText(preview, 'U1 source', (round(px * scale_x) + 12, round(py * scale_y) - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 125, 0), 2)
        previews.append(preview)
    # Normalize preview tile heights without changing source coordinate data.
    tile_height = max(tile.shape[0] for tile in previews)
    tiles = [cv2.copyMakeBorder(tile, 0, tile_height - tile.shape[0], 0, 0,
                                cv2.BORDER_CONSTANT, value=(45, 45, 45)) for tile in previews]
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(PREVIEW), np.hstack(tiles))
    return {
        'schema_version': '1.0', 'board_family': 'ultimainboard_2_1_4',
        'source_files_sha256': {str(path.relative_to(ROOT)): digest(path)
                                for path in (PCB, GEOMETRY, INTAKE, VIEW_REVIEW)},
        'source_frame': 'native imported PCB millimetres; same fixed XY source coordinates on both visible faces',
        'asset_frame': 'GLB metres; x=(PCB_X-origin_X)/1000, z=(PCB_Y-origin_Y)/1000, y=height',
        'asset_source_origin_mm': [ox, oy],
        'native_hole_drill_mm': 4.22,
        'same_physical_specimen_verified': False, 'continuous_flip_verified': False,
        'four_distinct_oblique_sides_verified': False,
        'metric_camera_pose_verified': False, 'release_eligible': False,
        'limitations': [
            'Four planar holes define homographies but cannot validate 3D pose or camera intrinsics.',
            'Two photos are from one gallery session; a continuous same-specimen flip is not documented.',
            'Image hole centers are visually reviewed candidates with 25-pixel uncertainty.',
            'Native source versus photographed PCB revision is not physically verified.',
        ],
        'frames': frames,
        'review_preview': str(PREVIEW.relative_to(ROOT)),
        'review_preview_sha256': digest(PREVIEW),
    }


if __name__ == '__main__':
    with OUTPUT.open('w', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(build(), indent=2) + '\n')
    print(str(OUTPUT))
