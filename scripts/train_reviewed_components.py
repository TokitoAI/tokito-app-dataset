"""Run medium segmentation only from an explicitly reviewed complete export.

No raw/partial dataset is automatically exported by this launcher.
"""
import argparse
import hashlib
import json
from pathlib import Path


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    errors = validate(json.loads(args.manifest.read_text(encoding='utf-8')))
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
        project=str(Path(__file__).parent / 'runs'), name='reviewed-medium-seg',
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
