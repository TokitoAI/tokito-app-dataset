"""Train the diagnostic five-family board detector.

The high epoch count is a ceiling. Early stopping chooses the actual duration,
and best.pt is the deployment candidate rather than the final epoch.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="yolo11m.pt")
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--patience", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--device", default="0")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--name", default="board-yolo11m-dynamic")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--freeze", type=int, default=10)
    parser.add_argument("--lr0", type=float, default=0.001)
    parser.add_argument("--lrf", type=float, default=0.01)
    parser.add_argument("--amp", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    os.environ["YOLO_CONFIG_DIR"] = str((root / "work/yolo-settings").resolve())

    import torch
    from ultralytics import YOLO

    if args.device != "cpu" and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA was requested but this Python environment has no CUDA-enabled "
            "PyTorch. Pass --device cpu only for a deliberately slow diagnostic run."
        )

    torch.set_num_threads(6)
    model = YOLO(args.checkpoint)
    data = str((root / "data/photo-model/yolo-boards/data.yaml").resolve())
    result = model.train(
        data=data,
        epochs=args.epochs,
        patience=args.patience,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=str((root / "data/photo-model/runs").resolve()),
        name=args.name,
        exist_ok=True,
        seed=args.seed,
        deterministic=True,
        optimizer="AdamW",
        lr0=args.lr0,
        lrf=args.lrf,
        cos_lr=True,
        warmup_epochs=3,
        freeze=args.freeze,
        amp=args.amp,
        cache=False,
        degrees=180,
        translate=0.1,
        scale=0.4,
        fliplr=0.5,
        flipud=0.5,
        close_mosaic=20,
        plots=True,
        save=True,
        save_period=25,
    )

    run = Path(result.save_dir)
    report = {
        "run": str(run),
        "best_checkpoint": str(run / "weights/best.pt"),
        "last_checkpoint": str(run / "weights/last.pt"),
        "checkpoint": args.checkpoint,
        "epochs_ceiling": args.epochs,
        "early_stopping_patience": args.patience,
        "image_size": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "amp": args.amp,
        "freeze_layers": args.freeze,
        "initial_learning_rate": args.lr0,
        "final_learning_rate_factor": args.lrf,
        "seed": args.seed,
        "started_from_pretrained": True,
        "selection_rule": "best validation fitness checkpoint; never deploy last.pt by default",
        "scope": "five-family board identification only; exact parts and pins require board registration plus source resolution",
        "dataset_limitations": [
            "one physical specimen per family",
            "validation has no ESP32 images",
            "results are diagnostic and cannot establish unseen-specimen accuracy",
        ],
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    (root / "data/photo-model/board-training-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()

