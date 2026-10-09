#!/usr/bin/env python3
"""Train the scoped PCB-Vision three-class YOLO box-candidate experiment."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / 'work/pcbvision-yolo-boxes'
MANIFEST = ROOT / 'data/external/PCBVision/box-candidate-manifest.json'
PUBLISH = ROOT / 'data/external/PCBVision/component-yolo-experiment'


def scalar(value):
    return float(value.item() if hasattr(value, 'item') else value)


def metric_summary(metrics):
    box = metrics.box
    return {
        'precision_mean': scalar(box.mp),
        'recall_mean': scalar(box.mr),
        'map50': scalar(box.map50),
        'map50_95': scalar(box.map),
        'map50_95_by_class': {metrics.names[index]: scalar(value)
                              for index, value in enumerate(box.maps)},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', default='yolo11n.pt')
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--imgsz', type=int, default=512)
    parser.add_argument('--batch', type=int, default=4)
    parser.add_argument('--name', default='pcbvision-boxes-yolo11n')
    args = parser.parse_args()
    assert args.epochs > 0 and args.imgsz > 0 and args.batch > 0
    data_yaml = DATASET / 'data.yaml'
    assert data_yaml.is_file() and MANIFEST.is_file()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert manifest['split_counts'] == {'train': 33, 'val': 9, 'test': 11}
    for split, count in manifest['split_counts'].items():
        assert len(list((DATASET / 'images' / split).glob('*.jpg'))) == count
        assert len(list((DATASET / 'labels' / split).glob('*.txt'))) == count
    os.environ['YOLO_CONFIG_DIR'] = str((ROOT / 'work/yolo-settings').resolve())
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(min(12, os.cpu_count() or 1))
    project = ROOT / 'work/pcbvision-yolo-training'
    trained = YOLO(args.checkpoint)
    result = trained.train(
        data=str(data_yaml), epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
        device='cpu', workers=0, project=str(project), name=args.name, exist_ok=True,
        seed=42, deterministic=True, patience=8, cache='ram', degrees=180,
        fliplr=0.5, flipud=0.5, scale=0.35, optimizer='AdamW', lr0=0.002,
        warmup_epochs=1, plots=True, verbose=True,
    )
    run = Path(result.save_dir)
    best = run / 'weights/best.pt'
    assert best.is_file()
    model = YOLO(best)
    validation = model.val(data=str(data_yaml), split='val', imgsz=args.imgsz,
                           batch=args.batch, device='cpu', workers=0, plots=False)
    test = model.val(data=str(data_yaml), split='test', imgsz=args.imgsz,
                     batch=args.batch, device='cpu', workers=0, plots=False)
    PUBLISH.mkdir(parents=True, exist_ok=True)
    checkpoint = PUBLISH / 'best.pt'
    shutil.copy2(best, checkpoint)
    for filename in ('results.csv', 'confusion_matrix.png', 'confusion_matrix_normalized.png',
                     'results.png', 'PR_curve.png', 'F1_curve.png'):
        source = run / filename
        if source.is_file():
            destination = PUBLISH / filename
            if source.suffix == '.csv':
                destination.write_bytes(('\n'.join(source.read_text(encoding='utf-8').splitlines()) + '\n').encode('utf-8'))
            else:
                shutil.copy2(source, destination)
    report = {
        'schema_version': 1,
        'status': 'external_three_class_candidate_box_experiment',
        'scope': 'PCB-Vision IC, capacitor and connector connected-mask-region boxes only',
        'not_a_tokito_board_part_model': True,
        'training_source_manifest': str(MANIFEST.relative_to(ROOT)).replace('\\', '/'),
        'training_source_manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        'split': manifest['split_counts'], 'split_seed': manifest['split_seed'],
        'class_names': manifest['class_names'], 'candidate_box_counts': manifest['box_counts'],
        'checkpoint_start': args.checkpoint, 'epochs_requested': args.epochs,
        'epochs_completed': len((run / 'results.csv').read_text(encoding='utf-8').splitlines()) - 1,
        'image_size': args.imgsz, 'batch': args.batch, 'device': 'cpu',
        'ultralytics_version': __import__('ultralytics').__version__,
        'torch_version': torch.__version__,
        'validation_candidate_metrics': metric_summary(validation),
        'test_candidate_metrics': metric_summary(test),
        'checkpoint_path': str(checkpoint.relative_to(ROOT)).replace('\\', '/'),
        'checkpoint_sha256': hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        'checkpoint_bytes': checkpoint.stat().st_size,
        'limits': [
            'Connected semantic regions are automatic box candidates, not exhaustively reviewed instances.',
            'The three external classes do not cover every visible PCB component.',
            'Metrics compare predictions with candidate boxes on distinct external PCB images.',
            'This checkpoint does not identify Tokito board family, refdes, net, pin, BOM or Gerber records.',
        ],
    }
    (PUBLISH / 'training-report.json').write_bytes((json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
