"""Evaluate and publish the best checkpoint from an early-stopped v2 run."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from ultralytics import YOLO

from train_component_segmentation_v2 import CLASS_NAMES, ROOT, _predict_metrics, load_prepared


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--imgsz', type=int, default=512)
    parser.add_argument('--device', default='0')
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to((ROOT / 'work/component-segmentation-v2').resolve()):
        raise ValueError('run must be inside the v2 training work directory')
    weights = run / 'weights/best.pt'
    history = json.loads((run / 'history.json').read_text())
    if not weights.is_file() or not history:
        raise FileNotFoundError('best checkpoint and history are required')
    best = min(history, key=lambda row: row['validation_partial_loss'])
    splits, _ = load_prepared(args.imgsz)
    model = YOLO(str(weights), task='segment')
    public_test = _predict_metrics(model, splits['test'], args.device)
    local = [s for s in splits['val'] if s['entry']['source'] == 'tokito_reviewed']
    local_val = _predict_metrics(model, local, args.device) if local else None
    (run / 'external-test-metrics.json').write_text(json.dumps(public_test, indent=2))
    (run / 'tokito-partial-validation.json').write_text(json.dumps(local_val, indent=2))
    sha = hashlib.sha256(weights.read_bytes()).hexdigest()
    report = {
        'status': 'completed', 'architecture': 'YOLO11m-seg', 'classes': CLASS_NAMES,
        'epochs_completed': history[-1]['epoch'], 'best_epoch': best['epoch'],
        'stop_reason': 'manual early stop after persistent validation degradation',
        'best_validation_partial_loss': best['validation_partial_loss'],
        'checkpoint': str(weights.relative_to(ROOT)), 'checkpoint_sha256': sha,
        'external_test': public_test, 'tokito_partial_validation': local_val,
        'evaluation_valid': False, 'production_eligible': False,
        'limitations': [
            'External test masks are connected semantic-region proposals, not exhaustively reviewed component instances.',
            'Tokito validation reuses known specimens and partial masks.',
            'Unreviewed gallery photos were excluded from supervised training.',
            'Exact IC SKU, reference designator, pin identity and 3D pose require board-specific BOM/Gerber/reference registration.',
        ],
    }
    (run / 'final-report.json').write_text(json.dumps(report, indent=2))
    (run / 'progress.json').write_text(json.dumps({'status': 'completed', 'best_epoch': best['epoch'],
        'epochs_completed': history[-1]['epoch'], 'stop_reason': report['stop_reason']}, indent=2))
    target = ROOT / 'models/component-segmentation-v2'
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(weights, target / 'best.pt')
    (target / 'REPORT.json').write_text(json.dumps(report, indent=2))
    (target / 'MODEL_CARD.md').write_text(
        '# Tokito Component Segmentation v2\n\n'
        'YOLO11m-seg candidate trained on PCB-Vision pixel masks and reviewed Tokito polygons. '
        'It predicts coarse visible package categories, not exact part numbers or pins. '
        'Public semantic regions are converted to instance proposals; touching parts may merge. '
        'Scores in REPORT.json are diagnostic, not independent Tokito-board accuracy.\n')
    print(json.dumps({'checkpoint': str(target / 'best.pt'), 'sha256': sha,
                      'epochs': history[-1]['epoch'], 'best_epoch': best['epoch'],
                      'external_test': public_test, 'tokito_partial_validation': local_val}), flush=True)


if __name__ == '__main__':
    main()
