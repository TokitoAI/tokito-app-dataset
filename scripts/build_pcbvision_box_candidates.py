#!/usr/bin/env python3
"""Make inspectable YOLO box proposals from PCB-Vision General semantic masks.

These connected regions are candidates, not reviewed instances or complete
component detection ground truth. The script writes only to ignored work/.
"""
from __future__ import annotations

import argparse
from collections import Counter
from io import BytesIO
import hashlib
import json
from pathlib import Path
import random
import zipfile

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'data/external/PCBVision/rgb-subset.zip'
PACKAGE_METADATA = ROOT / 'data/external/PCBVision/rgb-subset-package.json'
PUBLISHED_CANDIDATES = ROOT / 'data/external/PCBVision/box-candidate-manifest.json'
CLASSES = {'ic': 1, 'capacitor': 2, 'connector': 3}


def proposals(mask: np.ndarray, min_area: int) -> list[tuple[int, tuple[int, int, int, int], int]]:
    height, width = mask.shape
    result = []
    for class_id, value in enumerate(CLASSES.values()):
        connected, count = ndimage.label(mask == value)
        for component_id, region in enumerate(ndimage.find_objects(connected), 1):
            if region is None:
                continue
            area = int(np.count_nonzero(connected[region] == component_id))
            if area < min_area:
                continue
            y, x = region
            bounds = (x.start, y.start, x.stop, y.stop)
            assert 0 <= bounds[0] < bounds[2] <= width
            assert 0 <= bounds[1] < bounds[3] <= height
            result.append((class_id, bounds, area))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/pcbvision-yolo-boxes')
    parser.add_argument('--min-area', type=int, default=16)
    parser.add_argument('--split-seed', type=int, default=42)
    parser.add_argument('--preview-ids', default='1,20,40', help='Comma-separated image IDs to draw for review')
    parser.add_argument('--check', action='store_true', help='Compare proposals with the published candidate manifest')
    args = parser.parse_args()
    assert args.min_area > 0
    output = args.output.resolve()
    # Candidate output is deliberately kept outside the curated photo labels.
    assert output == (ROOT / 'work').resolve() or (ROOT / 'work').resolve() in output.parents
    metadata = json.loads(PACKAGE_METADATA.read_text(encoding='utf-8'))
    assert hashlib.sha256(PACKAGE.read_bytes()).hexdigest() == metadata['archive_sha256']
    summary = {'source_archive_sha256': metadata['archive_sha256'],
               'mask_variant': 'General', 'minimum_connected_region_pixels': args.min_area,
               'annotation_status': 'automatic_semantic_mask_box_candidates_not_reviewed_instances',
               'split_method': 'reproducible_random_split_of_53_distinct_PCB_images',
               'split_seed': args.split_seed, 'split_counts': {'train': 33, 'val': 9, 'test': 11},
               'class_names': list(CLASSES), 'images': [], 'box_counts': {}}
    preview_dir = output / 'previews'
    for split in summary['split_counts']:
        (output / 'labels' / split).mkdir(parents=True, exist_ok=True)
        (output / 'images' / split).mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_ids = set(args.preview_ids.split(','))
    counts = Counter()
    with zipfile.ZipFile(PACKAGE) as archive:
        names = set(archive.namelist())
        photos = sorted(name for name in names if name.startswith('PCBDataset/RGB/') and name.endswith('.jpg'))
        assert len(photos) == 53
        shuffled = [Path(name).stem for name in photos]
        random.Random(args.split_seed).shuffle(shuffled)
        split_by_id = {image_id: ('train' if index < 33 else 'val' if index < 42 else 'test')
                       for index, image_id in enumerate(shuffled)}
        assert Counter(split_by_id.values()) == summary['split_counts']
        for name in photos:
            stem = Path(name).stem
            split = split_by_id[stem]
            mask_name = f'PCBDataset/RGB/General/{stem}.png'
            assert mask_name in names
            rgb = archive.read(name)
            with Image.open(BytesIO(rgb)) as im:
                im.load()
                width, height = im.size
            with Image.open(BytesIO(archive.read(mask_name))) as im:
                im.load()
                mask = np.asarray(im)
            assert mask.shape == (height, width)
            assert set(np.unique(mask)) <= {0, 1, 2, 3}
            boxes = proposals(mask, args.min_area)
            lines = []
            for class_id, (x0, y0, x1, y1), area in boxes:
                lines.append(f'{class_id} {(x0+x1)/(2*width):.8f} {(y0+y1)/(2*height):.8f} {(x1-x0)/width:.8f} {(y1-y0)/height:.8f}')
                counts[list(CLASSES)[class_id]] += 1
            (output / 'images' / split / f'{stem}.jpg').write_bytes(rgb)
            (output / 'labels' / split / f'{stem}.txt').write_text(
                '\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
            if stem in preview_ids:
                with Image.open(BytesIO(rgb)) as im:
                    overlay = im.convert('RGB')
                draw = ImageDraw.Draw(overlay)
                for class_id, bounds, _ in boxes:
                    draw.rectangle(bounds, outline=['red', 'yellow', 'cyan'][class_id], width=3)
                overlay.save(preview_dir / f'{stem}.jpg', quality=90)
            summary['images'].append({'image_id': stem, 'split': split,
                                      'source_image': name, 'source_mask': mask_name,
                                      'width': width, 'height': height, 'proposal_count': len(boxes),
                                      'proposals': [{'class_id': class_id, 'bbox_xyxy_pixels': list(bounds),
                                                     'mask_area_pixels': area} for class_id, bounds, area in boxes]})
    summary['box_counts'] = dict(sorted(counts.items()))
    yaml_path = output / 'data.yaml'
    yaml_path.write_text(
        f"path: '{output.as_posix()}'\ntrain: images/train\nval: images/val\ntest: images/test\n"
        "names:\n  0: ic\n  1: capacitor\n  2: connector\n", encoding='utf-8')
    (output / 'proposal-manifest.json').write_bytes((json.dumps(summary, indent=2) + '\n').encode('utf-8'))
    if args.check:
        assert json.loads(PUBLISHED_CANDIDATES.read_text(encoding='utf-8')) == summary
        print('Published candidate manifest matches the packaged RGB masks.')
    print(f"Wrote {sum(counts.values())} candidate boxes across {len(summary['images'])} images to {output}")
    print('Class candidates:', summary['box_counts'])


if __name__ == '__main__':
    main()
