"""Run medium segmentation only from an explicitly reviewed complete export.

No raw/partial dataset is automatically exported by this launcher.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'


def validate(manifest):
    errors = []
    if manifest.get('coverage') != 'complete_visible_instances':
        errors.append('Partial frames require an ignore-aware loss; stock YOLO loss is prohibited.')
    if not manifest.get('source_identity_review_complete'):
        errors.append('Component identity review incomplete.')
    rows = manifest.get('images', [])
    groups = {}
    for row in rows:
        group = row.get('physical_specimen_id')
        split = row.get('split')
        if not group or split not in ('train', 'val', 'test'):
            errors.append('Each image needs a specimen ID and explicit train/val/test split.')
        if group in groups and groups[group] != split:
            errors.append('Physical specimen leakage between splits: ' + str(group))
        groups[group] = split
        if row.get('annotation_review') != 'complete':
            errors.append('Incomplete annotation: ' + row.get('path', 'unknown'))
        for kind in ('image', 'label'):
            path = Path(row.get(kind + '_path', ''))
            if not path.is_file():
                errors.append('Missing ' + kind + ': ' + str(path))
            elif hashlib.sha256(path.read_bytes()).hexdigest() != row.get(kind + '_sha256'):
                errors.append('Changed ' + kind + ': ' + str(path))
    if set(groups.values()) != {'train', 'val', 'test'}:
        errors.append('Need independent specimens in all three splits.')
    for board in manifest.get('active_board_families', []):
        present = {r.get('split') for r in rows if r.get('board_family') == board}
        if present != {'train', 'val', 'test'}:
            errors.append('Missing board-family split coverage: ' + board)
    if not manifest.get('active_board_families'):
        errors.append('Active board-family list absent.')
    return sorted(set(errors))


def validate_loader_inputs(manifest, data, data_file):
    """Bind the actual YOLO dataset to the reviewed manifest before any training."""
    errors = []
    root = Path(data.get('path', data_file.parent)).expanduser()
    if not root.is_absolute():
        errors.append('Dataset path must be absolute to avoid Ultralytics datasets_dir rebasing.')
        root = data_file.parent / root
    root = root.resolve()
    suffixes = {'.bmp', '.dng', '.jpeg', '.jpg', '.mpo', '.png', '.tif',
                '.tiff', '.webp', '.pfm', '.heic'}
    for split in ('train', 'val', 'test'):
        entries = data.get(split)
        if not entries:
            errors.append('Dataset YAML missing explicit ' + split + ' input.')
            continue
        entries = entries if isinstance(entries, list) else [entries]
        actual = set()
        for entry in entries:
            path = Path(entry)
            path = path if path.is_absolute() else root / path
            path = path.resolve()
            if path.is_dir():
                actual.update(p.resolve() for p in path.rglob('*')
                              if p.is_file() and p.suffix.lower() in suffixes)
            elif path.is_file() and path.suffix.lower() == '.txt':
                for line in path.read_text(encoding='utf-8').splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    item = Path(line)
                    if not item.is_absolute():
                        if not line.startswith('./'):
                            errors.append('Image list relative paths must begin ./: ' + line)
                            continue
                        item = path.parent / item
                    actual.add(item.resolve())
            else:
                errors.append('Unsupported or missing dataset input: ' + str(path))
        expected = {Path(r['image_path']).resolve() for r in manifest.get('images', [])
                    if r.get('split') == split and r.get('image_path')}
        if actual != expected:
            errors.append('Dataset ' + split + ' differs from reviewed manifest: '
                          + str(len(actual - expected)) + ' unreviewed, '
                          + str(len(expected - actual)) + ' missing images.')
    for row in manifest.get('images', []):
        image = Path(row.get('image_path', '')).resolve()
        # Ultralytics replaces the final /images/ path segment with /labels/.
        value = image.as_posix()
        if '/images/' not in value:
            errors.append('Image lacks conventional /images/ label mapping: ' + value)
            continue
        prefix, tail = value.rsplit('/images/', 1)
        loaded_label = Path(prefix + '/labels/' + tail).with_suffix('.txt').resolve()
        if loaded_label != Path(row.get('label_path', '')).resolve():
            errors.append('YOLO label mapping differs from reviewed label: ' + value)
    if data.get('download'):
        errors.append('Dataset download hooks are prohibited for a reviewed export.')
    return sorted(set(errors))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    import yaml
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    data = yaml.safe_load(args.data.read_text(encoding='utf-8'))
    errors = validate(manifest) + validate_loader_inputs(manifest, data, args.data.resolve())
    print(json.dumps({'ready': not errors, 'errors': errors}, indent=2))
    if errors:
        raise SystemExit(2)
    if not args.run:
        return
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.backends.cudnn.benchmark=False
    if not torch.cuda.is_available():
        raise SystemExit('CUDA environment required; no implicit CPU fallback.')
    model = YOLO('yolo11m-seg.pt')
    result = model.train(data=str(args.data.resolve()), epochs=1000, patience=80,
        imgsz=640, batch=1, device=0, workers=0, optimizer='AdamW', lr0=0.001,
        cos_lr=True, warmup_epochs=3, close_mosaic=20, seed=42,
        deterministic=True, cache=False, amp=True, freeze=0,
        fliplr=0, flipud=0, degrees=180, save=True, save_period=25,
        project=str(Path(__file__).resolve().parents[1] / 'work/training-runs'), name='reviewed-medium-seg',
        exist_ok=False)
    best = Path(result.save_dir) / 'weights' / 'best.pt'
    validation = YOLO(str(best)).val(data=str(args.data.resolve()), split='test', device=0)
    report = {'checkpoint': str(best), 'sha256': hashlib.sha256(best.read_bytes()).hexdigest(),
        'test_metrics': validation.results_dict, 'release_eligible': False,
        'remaining': ['per-instance identity evaluation', 'pin/anchor reprojection evaluation',
                      'mobile numerical conformance', 'physical rotation and flip verification']}
    (Path(result.save_dir) / 'evaluation.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
