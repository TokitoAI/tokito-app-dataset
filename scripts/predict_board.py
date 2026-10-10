"""Run the board-family model and emit readable, thresholded JSON detections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    default_model = root / "data/photo-model/board-yolo11m-finetune-experiment/best.pt"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Image file or directory")
    parser.add_argument("--model", type=Path, default=default_model)
    parser.add_argument("--thresholds", type=Path, help="Class threshold JSON; defaults beside model if present")
    parser.add_argument("--device", default="auto", help="auto, cpu, or a CUDA index such as 0")
    args = parser.parse_args()

    source = args.source.resolve()
    model_path = args.model.resolve()
    if not source.exists():
        parser.error(f"Source does not exist: {source}")
    if not model_path.exists():
        parser.error(f"Model does not exist: {model_path}")

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    class_map = json.loads(
        (root / "data/photo-model/board-class-display-names.json").read_text(encoding="utf-8")
    )["ordered_classes"]
    display_names = {int(row["class_id"]): row["display_name"] for row in class_map}

    threshold_path = args.thresholds.resolve() if args.thresholds else model_path.parent / "confidence-thresholds.json"
    if threshold_path.exists():
        raw_thresholds = json.loads(threshold_path.read_text(encoding="utf-8"))["class_id_thresholds"]
        thresholds = {int(class_id): float(value) for class_id, value in raw_thresholds.items()}
    else:
        thresholds = {class_id: 0.75 for class_id in display_names}

    if args.device == "auto":
        import torch

        device = "0" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    lowest_threshold = min(thresholds.values())
    results = model.predict(
        source=str(source),
        imgsz=640,
        device=device,
        conf=lowest_threshold,
        iou=0.7,
        verbose=False,
        save=False,
    )
    output = []
    for result in results:
        detections = []
        if result.boxes is not None:
            for class_value, confidence, box in zip(
                result.boxes.cls.tolist(),
                result.boxes.conf.tolist(),
                result.boxes.xyxy.tolist(),
            ):
                class_id = int(class_value)
                cutoff = thresholds.get(class_id, 1.0)
                if confidence < cutoff:
                    continue
                detections.append(
                    {
                        "class_id": class_id,
                        "board": display_names.get(class_id, "unknown_board_class"),
                        "confidence": round(float(confidence), 4),
                        "minimum_confidence": cutoff,
                        "bbox_xyxy_pixels": [round(float(value), 2) for value in box],
                    }
                )
        detections.sort(key=lambda item: item["confidence"], reverse=True)
        output.append(
            {
                "image": Path(result.path).name,
                "status": "board_detected" if detections else "no_supported_board_detected",
                "detections": detections,
            }
        )

    print(json.dumps({"model": str(model_path), "thresholds": thresholds, "results": output}, indent=2))


if __name__ == "__main__":
    main()
