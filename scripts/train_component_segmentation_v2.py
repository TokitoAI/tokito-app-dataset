"""Train a new hierarchical PCB component segmenter from verified mask sources.

PCB-Vision provides pixel labels for ICs, capacitors, connectors and explicitly
other pixels. Reviewed Tokito polygons add local package classes while
unreviewed pixels remain ignored. Unreviewed gallery photos are excluded.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import io
import json
import os
import random
import shutil
import time
import zipfile
from collections import Counter
from pathlib import Path

os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work' / 'component-segmentation-v2'
SOURCE_ZIP = ROOT / 'data/external/PCBVision/rgb-subset.zip'
SOURCE_PACKAGE = ROOT / 'data/external/PCBVision/rgb-subset-package.json'
SOURCE_MANIFEST = ROOT / 'data/external/PCBVision/box-candidate-manifest.json'
INITIAL_WEIGHTS = ROOT / 'work/partial-component-diagnostic/yolo11m-seg.pt'
CLASS_NAMES = ['ic_package', 'chip_passive', 'connector', 'rf_module', 'switch',
               'crystal', 'discrete_semiconductor', 'inductor']
CLASS_ID = {name: i for i, name in enumerate(CLASS_NAMES)}

LOCAL_CLASS_MAP = {
    'chip_passive_body': 'chip_passive', 'capacitor': 'chip_passive',
    'ceramic_capacitor': 'chip_passive', 'electrolytic_capacitor': 'chip_passive',
    'resistor': 'chip_passive', 'integrated_circuit': 'ic_package',
    'tactile_switch': 'switch', 'crystal_resonator': 'crystal',
    'rf_shield': 'rf_module', 'rf_module_substrate': 'rf_module',
    'esp12e_shield': 'rf_module', 'rf_shield_unresolved': 'rf_module',
    'switch_body': 'switch',
    'crystal_body': 'crystal',
    'three_terminal_body_unresolved': 'discrete_semiconductor',
    'power_package_unresolved': 'discrete_semiconductor',
    'diode_body': 'discrete_semiconductor',
    'inductor_body': 'inductor',
    'connector_housing': 'connector', 'usb_connector_body': 'connector',
    'usb_b_connector_body': 'connector', 'header_housing': 'connector',
    'terminal_block': 'connector',
}


def _partial_module():
    import importlib.util
    path = ROOT / 'scripts/train_partial_component_diagnostic.py'
    spec = importlib.util.spec_from_file_location('partial_component_v1', path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _connected_components(mask: np.ndarray, min_area: int = 16):
    import cv2
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8)
    out = []
    for label in range(1, count):
        x, y, w, h, area = map(int, stats[label])
        if area < min_area or w < 2 or h < 2:
            continue
        instance = labels == label
        out.append((instance, (x, y, x + w, y + h)))
    return out


def _letterbox_image(image: Image.Image, size: int):
    ratio = min(size / image.width, size / image.height)
    nw = max(1, round(image.width * ratio))
    nh = max(1, round(image.height * ratio))
    left, top = (size - nw) // 2, (size - nh) // 2
    canvas = Image.new('RGB', (size, size), (114, 114, 114))
    canvas.paste(image.resize((nw, nh), Image.Resampling.BILINEAR), (left, top))
    return canvas, (nw, nh, left, top)


def _to_sample(canvas: Image.Image, instance_specs, background: np.ndarray, entry):
    size = canvas.width
    masks, boxes, classes = [], [], []
    for mask, cls in instance_specs:
        mask = np.asarray(mask, dtype=bool)
        ys, xs = np.where(mask)
        if not len(xs):
            continue
        x1, x2 = int(xs.min()), int(xs.max()) + 1
        y1, y2 = int(ys.min()), int(ys.max()) + 1
        if x2 <= x1 or y2 <= y1:
            continue
        # Keep all prepared instance rasters byte-packed. Dense external frames
        # can have 200+ proposals: uint8 limits each 512px stack to ~53 MiB;
        # float expansion is deferred until the single current batch reaches GPU.
        masks.append(mask.astype(np.uint8))
        boxes.append([(x1 + x2) / 2 / size, (y1 + y2) / 2 / size,
                      (x2 - x1) / size, (y2 - y1) / size])
        classes.append(cls)
    if not masks:
        return None
    mask_array = np.stack(masks)
    bg = np.asarray(background, dtype=bool)
    if bg.shape == (size, size):
        bg = np.broadcast_to(bg[None], (len(CLASS_NAMES), size, size)).copy()
    if bg.shape != (len(CLASS_NAMES), size, size):
        raise ValueError('background mask has wrong canvas size: ' + str(entry.get('id')))
    for mask, cls in zip(mask_array, classes):
        if (mask.astype(bool) & bg[cls]).any():
            raise ValueError('a positive mask overlaps explicitly negative pixels: ' + str(entry.get('id')))
    pixels = np.asarray(canvas).copy()
    return {
        'image': torch.from_numpy(pixels).permute(2, 0, 1),
        'masks': torch.from_numpy(mask_array),
        'boxes': torch.tensor(boxes, dtype=torch.float32),
        'classes': torch.tensor(classes, dtype=torch.float32).view(-1, 1),
        'background': torch.from_numpy(bg),
        'entry': entry,
    }


def build_local_samples(size: int):
    partial = _partial_module()
    images, _, excluded = partial.collect()
    background_path = ROOT / 'work/partial-component-diagnostic/background-regions.json'
    background_docs = json.loads(background_path.read_text()) if background_path.exists() else {}
    if 'images' in background_docs:
        background_docs = {r['image_path']: r.get('regions', []) for r in background_docs['images']}
    fallback = {
        'data/phone-captures/2026-10-10/IMG_20261010_092144.jpg',
        'data/phone-captures/2026-10-10/IMG_20261010_092221.jpg',
        'data/phone-captures/2026-10-10/IMG_20261010_092203.jpg',
    }
    local_samples = []
    excluded_by_class = Counter()
    for entry in images:
        source = ROOT / entry['path']
        image = Image.open(source).convert('RGB')
        canvas, (nw, nh, left, top) = _letterbox_image(image, size)
        hmask = np.zeros((size, size), dtype=bool)
        instances = []
        for row in entry['rows']:
            cls = row['class_name']
            macro = ('ic_package' if cls.startswith('ic_') else LOCAL_CLASS_MAP.get(cls))
            if macro is None:
                excluded_by_class[cls] += 1
                continue
            poly = np.asarray(row['polygon'], dtype=np.float32)
            poly[:, 0] = poly[:, 0] * (nw / image.width) + left
            poly[:, 1] = poly[:, 1] * (nh / image.height) + top
            raster = Image.new('L', (size, size), 0)
            ImageDraw.Draw(raster).polygon([tuple(p) for p in poly], fill=1)
            mask = np.asarray(raster, dtype=bool)
            if not mask.any():
                continue
            instances.append((mask, CLASS_ID[macro]))
        if not instances:
            continue
        bg = np.zeros((size, size), dtype=bool)
        regions = list(background_docs.get(entry['path'], []))
        if entry['path'] in fallback and not regions:
            regions = [{'polygon_xy_pixels': [[0, 0], [600, 0], [600, 600], [0, 600]],
                        'image_sha256': entry['sha256'],
                        'review_evidence': 'Previously visually reviewed empty desk corner.'}]
        for region in regions:
            if region.get('image_sha256', entry['sha256']) != entry['sha256'] or not region.get('review_evidence'):
                raise ValueError('unbound/unsupported reviewed background region in ' + entry['path'])
            poly = np.asarray(region['polygon_xy_pixels'], dtype=np.float32)
            poly[:, 0] = poly[:, 0] * (nw / image.width) + left
            poly[:, 1] = poly[:, 1] * (nh / image.height) + top
            raster = Image.new('L', (size, size), 0)
            ImageDraw.Draw(raster).polygon([tuple(p) for p in poly], fill=1)
            bg |= np.asarray(raster, dtype=bool)
        for mask, _ in instances:
            if (mask & bg).any():
                raise ValueError('reviewed background overlaps local part mask: ' + entry['path'])
        sample = _to_sample(canvas, instances, bg, dict(
            source='tokito_reviewed', path=entry['path'], sha256=entry['sha256'],
            board_family=entry['board_family'], physical_specimen_id=entry['physical_specimen_id'],
            capture_group_id=entry['capture_group_id'], split=entry['split'],
            annotation_coverage='partial_visible_instances',
        ))
        if sample:
            local_samples.append(sample)
    return local_samples, excluded_by_class, excluded


def build_external_samples(size: int):
    package = json.loads(SOURCE_PACKAGE.read_text())
    if hashlib.sha256(SOURCE_ZIP.read_bytes()).hexdigest() != package['archive_sha256']:
        raise ValueError('PCB-Vision source archive hash mismatch')
    if package['dataset_license'] != 'CC BY 4.0' or not package['zip_testzip_passed']:
        raise ValueError('PCB-Vision package is not integrity/license verified')
    candidate_manifest = json.loads(SOURCE_MANIFEST.read_text())
    if hashlib.sha256(SOURCE_ZIP.read_bytes()).hexdigest() != candidate_manifest['source_archive_sha256']:
        raise ValueError('PCB-Vision candidate manifest does not bind the source archive')
    by_id = {row['image_id']: row for row in candidate_manifest['images']}
    samples = []
    with zipfile.ZipFile(SOURCE_ZIP) as archive:
        for image_id in sorted(by_id, key=int):
            row = by_id[image_id]
            image_path = 'PCBDataset/RGB/' + image_id + '.jpg'
            mask_path = 'PCBDataset/RGB/General/' + image_id + '.png'
            image = Image.open(io.BytesIO(archive.read(image_path))).convert('RGB')
            label_image = Image.open(io.BytesIO(archive.read(mask_path))).convert('L')
            if label_image.size != image.size:
                raise ValueError('PCB-Vision RGB/mask shape mismatch: ' + image_id)
            canvas, (nw, nh, left, top) = _letterbox_image(image, size)
            label_resized = label_image.resize((nw, nh), Image.Resampling.NEAREST)
            class_map = np.zeros((size, size), dtype=np.uint8)
            class_map[top:top + nh, left:left + nw] = np.asarray(label_resized, dtype=np.uint8)
            # Dataset ground-truth index map: 1=IC, 2=capacitor, 3=connector;
            # index 0 is the explicit "Others" class and is negative for these targets.
            external_to_local = {1: CLASS_ID['ic_package'], 2: CLASS_ID['chip_passive'],
                                 3: CLASS_ID['connector']}
            instances = []
            for pixel_class, local_class in external_to_local.items():
                for mask, _bbox in _connected_components(class_map == pixel_class, min_area=16):
                    instances.append((mask, local_class))
            if not instances:
                raise ValueError('PCB-Vision frame has no target components: ' + image_id)
            # The public masks only supervise three target classes. The remaining
            # Tokito-only classes stay unknown on external boards instead of being
            # taught as absent there.
            bg = np.zeros((len(CLASS_NAMES), size, size), dtype=bool)
            for pixel_class, local_class in external_to_local.items():
                bg[local_class] = class_map != pixel_class
            sample = _to_sample(canvas, instances, bg, dict(
                source='PCB-Vision', image_id=image_id, source_image=image_path,
                source_mask=mask_path, split=row['split'], physical_specimen_id='pcbvision:' + image_id,
                capture_group_id='pcbvision:' + image_id,
                annotation_coverage='semantic_pixel_labels_connected_components_as_instance_proposals',
                license='CC BY 4.0',
            ))
            samples.append(sample)
    return samples, package, candidate_manifest


def prepare(size: int):
    OUT.mkdir(parents=True, exist_ok=True)
    external, package, ext_manifest = build_external_samples(size)
    local, excluded, excluded_legacy = build_local_samples(size)
    all_samples = external + local
    by_split = {key: [s for s in all_samples if s['entry']['split'] == key]
                for key in ('train', 'val', 'test')}
    if not all(by_split[k] for k in by_split):
        raise ValueError('train, val and test partitions must be non-empty')
    # External source has only three pixel classes; keep its fixed image-level split.
    ext_splits = {s['entry']['image_id']: s['entry']['split'] for s in external}
    if Counter(ext_splits.values()) != Counter({'train': 33, 'val': 9, 'test': 11}):
        raise ValueError('external split does not match verified 33/9/11 manifest')
    train_groups, val_groups = set(), set()
    for split, bucket in [('train', by_split['train']), ('val', by_split['val'])]:
        groups = {s['entry']['capture_group_id'] for s in bucket if s['entry']['source'] == 'tokito_reviewed'}
        (train_groups if split == 'train' else val_groups).update(groups)
    if train_groups & val_groups:
        raise ValueError('Tokito capture-group leakage between local train and validation')
    source_hashes = {
        str(SOURCE_ZIP.relative_to(ROOT)): hashlib.sha256(SOURCE_ZIP.read_bytes()).hexdigest(),
        str(SOURCE_PACKAGE.relative_to(ROOT)): hashlib.sha256(SOURCE_PACKAGE.read_bytes()).hexdigest(),
        str(SOURCE_MANIFEST.relative_to(ROOT)): hashlib.sha256(SOURCE_MANIFEST.read_bytes()).hexdigest(),
    }
    if INITIAL_WEIGHTS.is_file():
        source_hashes[str(INITIAL_WEIGHTS.relative_to(ROOT))] = hashlib.sha256(INITIAL_WEIGHTS.read_bytes()).hexdigest()
    # Bind every annotation source used by the ignore-aware collector, including
    # single-frame complete reviews and the NXP full-frame partial review.
    annotation_files = sorted({str(f.relative_to(ROOT)) for f in (ROOT / 'annotations').glob('*dense-component-review.json')} |
                              set(_partial_module().FILES))
    for annotation_file in annotation_files:
        source_hashes[annotation_file] = hashlib.sha256((ROOT / annotation_file).read_bytes()).hexdigest()
    manifest = {
        'schema_version': '2.0', 'task': 'instance_segmentation', 'architecture': 'YOLO11m-seg',
        'image_size': size, 'class_names': CLASS_NAMES,
        'source_data': {
            'public': 'PCB-Vision RGB + General pixel masks', 'public_images': len(external),
            'public_split_counts': dict(Counter(s['entry']['split'] for s in external)),
            'public_license': package['dataset_license'], 'public_doi': package['source_doi'],
            'tokito_local_images': len(local),
            'tokito_reviewed_instance_count': sum(len(s['masks']) for s in local),
            'tokito_source_annotation_files': annotation_files,
            'new_iqoo_gallery_images_excluded_unreviewed': 68,
            'new_iqoo_gallery_images_partially_reviewed_for_training': 2,
            'new_iqoo_gallery_reviewed_training_masks': 11,
            'new_iqoo_gallery_exclusion_reason': 'The other gallery images have no verified component masks; unknown pixels are ignored rather than labeled as background.',
        },
        'source_hashes': source_hashes,
        'local_image_hashes': {s['entry']['path']: s['entry']['sha256'] for s in local},
        'source_mask_policy': 'External semantic classes split into connected-region proposals; local unknown pixels ignored; only explicitly reviewed local background is negative.',
        'split_policy': 'Public 53 distinct PCBs use fixed image split 33/9/11. Tokito local validation is same known physical specimens and is diagnostic only.',
        'class_policy': 'YOLO predicts visible physical package categories. Exact manufacturer/SKU/refdes/pin identity must be joined from board/BOM/Gerber review, not inferred from the coarse mask class.',
        'evaluation_valid': False, 'production_eligible': False,
        'partially_annotated_images': sum(s['entry']['source'] == 'tokito_reviewed' for s in all_samples),
        'instance_counts': dict(Counter(CLASS_NAMES[int(c)] for s in all_samples for c in s['classes'].flatten().tolist())),
        'excluded_local_rows': dict(excluded), 'excluded_legacy_rows': excluded_legacy,
        'external_mask_instances_are_proposals_not_exhaustively_reviewed_instances': True,
        'public_mask_disclaimer': 'Connected semantic regions can merge touching same-class components or split antialias fragments; all claims remain diagnostic until visual audit.',
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    for split, bucket in by_split.items():
        (OUT / (split + '-index.json')).write_text(json.dumps([
            {**s['entry'], 'instances': int(len(s['masks']))} for s in bucket
        ], indent=2))

    # Persist compact, lossless samples and keep only small references in RAM.
    # Repeated epochs load one image at a time, preventing accumulated dense
    # per-instance rasters and augmentation copies from exhausting host memory.
    cache_tag = hashlib.sha256(json.dumps({
        'size': size, 'source_hashes': source_hashes,
        'local_image_hashes': manifest['local_image_hashes'], 'schema': 2,
    }, sort_keys=True).encode()).hexdigest()[:12]
    cache_dir = OUT / f'cache-{size}-{cache_tag}'
    cache_dir.mkdir(parents=True, exist_ok=True)
    disk_splits = {key: [] for key in by_split}
    for split, bucket in by_split.items():
        for i, sample in enumerate(bucket):
            cache_path = cache_dir / f'{split}-{i:04d}'
            cache_path.mkdir(parents=True, exist_ok=True)
            for name, tensor in (('image', sample['image']), ('masks', sample['masks']),
                                 ('boxes', sample['boxes']), ('classes', sample['classes']),
                                 ('background', sample['background'])):
                np.save(cache_path / f'{name}.npy', tensor.contiguous().cpu().numpy())
            disk_splits[split].append({'entry': sample['entry'],
                                       'cache_path': str(cache_path.relative_to(ROOT))})
    manifest['sample_cache'] = str(cache_dir.relative_to(ROOT))
    manifest['sample_cache_format'] = 'memory-mapped NPY; uint8 images/masks and bool reviewed-background rasters'
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    del all_samples, external, local, by_split
    gc.collect()
    print(json.dumps({
        'train_images': len(disk_splits['train']), 'val_images': len(disk_splits['val']),
        'test_images': len(disk_splits['test']), 'class_names': CLASS_NAMES,
        'instances': manifest['instance_counts'], 'local_images': manifest['source_data']['tokito_local_images'],
        'local_partial_masks': manifest['source_data']['tokito_reviewed_instance_count'],
        'evaluation_valid': False,
    }), flush=True)
    return disk_splits, manifest


def _load_sample(sample):
    """Materialize one compact cached sample; pass through in-memory inputs."""
    cache_path = sample.get('cache_path')
    if not cache_path:
        return sample
    path = ROOT / cache_path
    if path.is_dir():
        arrays = {name: np.load(path / f'{name}.npy', mmap_mode='c', allow_pickle=False)
                  for name in ('image', 'masks', 'boxes', 'classes', 'background')}
        return {
            'entry': sample['entry'],
            'image': torch.from_numpy(arrays['image']),
            'masks': torch.from_numpy(arrays['masks']),
            'boxes': torch.from_numpy(arrays['boxes']),
            'classes': torch.from_numpy(arrays['classes']),
            'background': torch.from_numpy(arrays['background']),
        }
    with np.load(path, allow_pickle=False) as data:
        return {'entry': sample['entry'], **{name: torch.from_numpy(data[name])
                for name in ('image', 'masks', 'boxes', 'classes', 'background')}}


def _augment(sample):
    sample = _load_sample(sample)
    # Keep the full reviewed sample byte-packed on CPU. Real captured views are
    # required for 3D coverage; synthetic raster copies add memory pressure.
    return sample


def _batch(sample, device, training=False):
    sample = _load_sample(sample)
    image = sample['image'][None].to(device=device)
    image = image.float().div_(255) if image.dtype == torch.uint8 else image.float()
    if training:
        image.mul_(random.uniform(.88, 1.12)).clamp_(0, 1)
    return {
        # Transfer compact uint8 storage first, then expand on the GPU. Casting
        # in the CPU .to(device, dtype=...) path creates a large host temporary.
        'img': image,
        'masks': sample['masks'].to(device=device),
        'batch_idx': torch.zeros(len(sample['boxes']), device=device),
        'bboxes': sample['boxes'].to(device),
        'cls': sample['classes'].to(device),
        'reviewed_background_masks': sample['background'][None].to(device),
    }


def load_prepared(size: int):
    """Load the prepared cache references without rebuilding tensors in RAM."""
    manifest_path = OUT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('image_size') != size:
        raise ValueError(f'prepared cache is {manifest.get("image_size")}px, requested {size}px')
    cache_dir = ROOT / manifest['sample_cache']
    splits = {}
    for split in ('train', 'val', 'test'):
        index = json.loads((OUT / f'{split}-index.json').read_text())
        refs = []
        for i, entry in enumerate(index):
            stem = cache_dir / f'{split}-{i:04d}'
            cache_path = stem if stem.is_dir() else stem.with_suffix('.npz')
            if not cache_path.exists():
                raise FileNotFoundError(f'prepared sample cache missing: {cache_path}')
            refs.append({'entry': entry, 'cache_path': str(cache_path.relative_to(ROOT))})
        splits[split] = refs
    return splits, manifest


def _save_checkpoint(model, path, epoch, args):
    # torch.load in Ultralytics maps checkpoints to CPU. Serialize the live
    # module directly so Windows does not need a second full CPU model copy.
    model.names = dict(enumerate(CLASS_NAMES))
    model.task = 'segment'
    model.criterion = None
    torch.save({'model': model, 'epoch': epoch, 'train_args': vars(args),
                'diagnostic_only': True, 'evaluation_valid': False}, path)


def _predict_metrics(model, samples, device, conf=.25):
    tp = fp = fn = ignored = 0
    per_class = {name: {'tp': 0, 'fp': 0, 'fn': 0} for name in CLASS_NAMES}
    details = []
    for sample in samples:
        sample = _load_sample(sample)
        image = sample['image'].permute(1, 2, 0).cpu().numpy()
        if image.dtype != np.uint8:
            image = np.clip(image * 255, 0, 255).astype(np.uint8)
        image = image[:, :, ::-1].copy()
        result = model.predict(source=image, imgsz=image.shape[0], conf=conf, iou=.7,
                               device=device, verbose=False)[0]
        gt = sample['masks'].cpu().numpy() > .5
        gtcls = sample['classes'].flatten().cpu().numpy().astype(int)
        used, itp, ifp, iign = set(), 0, 0, 0
        if result.masks is not None:
            pred_masks = result.masks.data.cpu().numpy() > .5
            pred_cls = result.boxes.cls.cpu().numpy().astype(int)
            for pred, cls in zip(pred_masks, pred_cls):
                overlaps = [np.logical_and(pred, g).sum() / max(np.logical_or(pred, g).sum(), 1) for g in gt]
                matches = [(overlaps[i], i) for i in range(len(gt)) if gtcls[i] == cls and i not in used]
                best = max(matches, default=(0, -1))
                if best[0] >= .5:
                    used.add(best[1]); itp += 1; per_class[CLASS_NAMES[cls]]['tp'] += 1
                elif max(overlaps, default=0) >= .5:
                    ifp += 1; per_class[CLASS_NAMES[cls]]['fp'] += 1
                elif pred.any() and (pred & sample['background'][cls].cpu().numpy()).sum() / pred.sum() >= .9:
                    ifp += 1; per_class[CLASS_NAMES[cls]]['fp'] += 1
                else:
                    iign += 1
        ifn = len(gt) - len(used)
        for idx in range(len(gt)):
            if idx not in used:
                per_class[CLASS_NAMES[gtcls[idx]]]['fn'] += 1
        tp += itp; fp += ifp; fn += ifn; ignored += iign
        details.append({'source': sample['entry']['source'], 'id': sample['entry'].get('image_id', sample['entry'].get('path')),
                        'tp': itp, 'fp_in_reviewed_pixels': ifp, 'fn_reviewed': ifn,
                        'ignored': iign, 'ground_truth_instances': int(len(gt))})
    return {
        'confidence': conf, 'mask_iou_threshold': .5, 'tp': tp, 'fp_in_reviewed_pixels': fp,
        'fn_reviewed': fn, 'ignored': ignored,
        'precision_in_reviewed_scope': tp / (tp + fp) if tp + fp else None,
        'recall_of_reviewed_instances': tp / (tp + fn) if tp + fn else None,
        'evaluation_valid': False,
        'scope': 'external held-out connected semantic components plus local partial masks; touching regions/proposal errors remain possible',
        'per_class': per_class, 'images': details,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--use-prepared-cache', action='store_true',
                        help='Load compact cache references and avoid constructing the full dataset in the training process.')
    parser.add_argument('--initial-best-loss', type=float, default=None,
                        help='Carry the best validation loss forward when continuing a prior candidate checkpoint.')
    parser.add_argument('--initial-best-epoch', type=int, default=0,
                        help='Epoch index at which --initial-best-loss was observed.')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--epochs', type=int, default=1000)
    parser.add_argument('--patience', type=int, default=60)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--pretrained', default=str(INITIAL_WEIGHTS))
    parser.add_argument('--device', default='0')
    args = parser.parse_args()
    random.seed(42); np.random.seed(42); torch.manual_seed(42)
    splits, manifest = load_prepared(args.imgsz) if args.use_prepared_cache else prepare(args.imgsz)
    if args.prepare_only or not args.run:
        return
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA training environment required; refusing an implicit CPU run')
    torch.set_num_threads(1); torch.set_num_interop_threads(1); torch.backends.cudnn.benchmark = False
    from ultralytics import YOLO
    from ultralytics.nn.tasks import SegmentationModel
    from ultralytics.cfg import get_cfg
    from partial_component_segmentation_loss import build_partial_segmentation_loss
    run = OUT / ('run-' + time.strftime('%Y%m%d-%H%M%S'))
    if run.exists() and any(run.iterdir()):
        raise FileExistsError('Refusing to overwrite an existing v2 run: ' + str(run))
    weights = run / 'weights'; weights.mkdir(parents=True, exist_ok=True)
    pretrained = YOLO(args.pretrained)
    model = SegmentationModel(pretrained.model.yaml, nc=len(CLASS_NAMES), verbose=False)
    model.load(pretrained.model)
    model = model.cuda(); model.args = get_cfg(); model.args.overlap_mask = False
    model.args.task = 'segment'; model.names = dict(enumerate(CLASS_NAMES))
    criterion = build_partial_segmentation_loss(model)
    # Disable foreach's temporary tensor-list materialization on Windows; this
    # host is memory-constrained and the simple per-parameter path is steadier.
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5, weight_decay=5e-4,
                                  foreach=False)
    scaler = torch.cuda.amp.GradScaler()
    best = float('inf') if args.initial_best_loss is None else args.initial_best_loss
    best_epoch = args.initial_best_epoch
    records, started = [], time.time()
    (run / 'progress.json').write_text(json.dumps({'status': 'running', 'epoch': 0,
        'epoch_ceiling': args.epochs, 'patience': args.patience, 'dataset': manifest}, indent=2))
    for epoch in range(1, args.epochs + 1):
        model.train(); random.shuffle(splits['train']); total = 0.0
        lr = 1e-5 * (.1 + .9 * (1 + np.cos(np.pi * (epoch - 1) / args.epochs)) / 2) * min(1, epoch / 3)
        for group in optimizer.param_groups: group['lr'] = float(lr)
        for original in splits['train']:
            sample = _augment(original)
            batch = _batch(sample, 'cuda', training=True); optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type='cuda', dtype=torch.float16):
                loss, _ = criterion(model(batch['img']), batch); objective = loss.sum()
            if not torch.isfinite(objective): raise RuntimeError('non-finite training loss')
            scaler.scale(objective).backward(); scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 10)
            scaler.step(optimizer); scaler.update(); total += float(objective.item())
            # Drop the graph and current dense batch before opening the next
            # compressed sample. Otherwise Python keeps the prior mask stack
            # and activation graph alive while _augment allocates its copies.
            del sample, batch, loss, objective
        model.eval(); val_loss = 0.0
        with torch.no_grad():
            for sample in splits['val']:
                batch = _batch(sample, 'cuda')
                with torch.autocast(device_type='cuda', dtype=torch.float16):
                    loss, _ = criterion(model(batch['img']), batch)
                val_loss += float(loss.sum().item())
                del sample, batch, loss
        val_loss /= len(splits['val'])
        record = {'epoch': epoch, 'train_loss': total / len(splits['train']),
                  'validation_partial_loss': val_loss, 'lr': float(lr),
                  'elapsed_seconds': time.time() - started, 'evaluation_valid': False}
        if not np.isfinite(val_loss): raise RuntimeError('non-finite validation loss')
        if val_loss < best - 1e-4:
            best, best_epoch = val_loss, epoch
            _save_checkpoint(model, weights / 'best.pt', epoch, args)
        record['best_epoch'] = best_epoch; records.append(record)
        (run / 'history.json').write_text(json.dumps(records, indent=2))
        (run / 'progress.json').write_text(json.dumps({'status': 'running', 'epoch': epoch,
            'best_epoch': best_epoch, 'best_validation_partial_loss': best,
            'patience': args.patience, 'epoch_ceiling': args.epochs,
            'elapsed_seconds': record['elapsed_seconds'], 'latest': record}, indent=2))
        print(json.dumps(record), flush=True)
        if epoch % 10 == 0: _save_checkpoint(model, weights / 'last.pt', epoch, args)
        if epoch - best_epoch >= args.patience: break
    _save_checkpoint(model, weights / 'last.pt', epoch, args)
    del criterion, optimizer, model, pretrained; torch.cuda.empty_cache()
    best_model = YOLO(str(weights / 'best.pt'), task='segment')
    public_test = _predict_metrics(best_model, splits['test'], args.device)
    local_val = [s for s in splits['val'] if s['entry']['source'] == 'tokito_reviewed']
    local_diagnostic = _predict_metrics(best_model, local_val, args.device) if local_val else None
    (run / 'external-test-metrics.json').write_text(json.dumps(public_test, indent=2))
    (run / 'tokito-partial-validation.json').write_text(json.dumps(local_diagnostic, indent=2))
    checkpoint_sha = hashlib.sha256((weights / 'best.pt').read_bytes()).hexdigest()
    report = {
        'status': 'completed', 'architecture': 'YOLO11m-seg', 'classes': CLASS_NAMES,
        'epochs_completed': epoch, 'best_epoch': best_epoch, 'patience': args.patience,
        'stop_reason': 'patience' if epoch < args.epochs else 'epoch_ceiling',
        'checkpoint': str((weights / 'best.pt').relative_to(ROOT)), 'checkpoint_sha256': checkpoint_sha,
        'external_test': public_test, 'tokito_partial_validation': local_diagnostic,
        'evaluation_valid': False, 'production_eligible': False,
        'limitations': ['External test masks are connected semantic-region proposals, not exhaustively reviewed component instances.',
                        'Tokito validation reuses known specimens and partial masks.',
                        'Unreviewed gallery photos were excluded from supervised training.',
                        'Exact IC SKU, reference designator, pin identity and 3D pose require board-specific BOM/Gerber/reference registration.'],
    }
    (run / 'final-report.json').write_text(json.dumps(report, indent=2))
    target = ROOT / 'models/component-segmentation-v2'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(weights / 'best.pt', target / 'best.pt')
    (target / 'REPORT.json').write_text(json.dumps(report, indent=2))
    (target / 'MODEL_CARD.md').write_text(
        '# Tokito Component Segmentation v2\n\n'
        'YOLO11m-seg candidate trained on verified PCB-Vision pixel masks plus reviewed Tokito component polygons. '
        'It predicts coarse visible package categories, not exact part numbers or pins. '
        'The public mask regions are converted to connected-component instance proposals; touching components may merge. '
        'All scores are diagnostic and are not independent Tokito-board accuracy. See REPORT.json and the source manifest.\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
