"""Compare a board LiteRT export with its PyTorch checkpoint on square inputs.

This establishes export conformance on known photos, not independent accuracy.
Run in the Linux export environment with ai-edge-litert and Ultralytics installed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import cv2
import numpy as np
import torch
from ai_edge_litert.interpreter import Interpreter
from ultralytics import YOLO
from ultralytics.data.augment import LetterBox


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(raw: np.ndarray, thresholds: np.ndarray, names: dict[int, str]) -> list[dict]:
    """Class-aware NMS in the normalized letterboxed input coordinate frame."""
    classes = raw[4:].argmax(axis=0)
    scores = raw[4:].max(axis=0)
    indices = np.flatnonzero(scores >= thresholds[classes])
    indices = indices[np.argsort(-scores[indices], kind="stable")]
    accepted = []
    for index in indices:
        cx, cy, width, height = raw[:4, index]
        box = np.array([cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2])
        suppressed = False
        for previous in accepted:
            if previous["class_id"] != int(classes[index]):
                continue
            other = np.array(previous["box_xyxy_normalized"])
            overlap = np.maximum(0, np.minimum(box[2:], other[2:]) - np.maximum(box[:2], other[:2]))
            intersection = float(np.prod(overlap))
            union = float(width * height + np.prod(other[2:] - other[:2]) - intersection)
            if union > 0 and intersection / union > 0.7:
                suppressed = True
                break
        if not suppressed:
            accepted.append({
                "class_id": int(classes[index]),
                "board": names[int(classes[index])],
                "confidence": float(scores[index]),
                "box_xyxy_normalized": box.tolist(),
            })
    return accepted


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    folder = root / "data/photo-model/board-yolo11m-finetune-experiment"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=folder / "best.pt")
    parser.add_argument("--model", type=Path, default=folder / "best.tflite")
    parser.add_argument("--images", type=Path, default=root / "data/photo-model/yolo-boards/images/val")
    parser.add_argument("--thresholds", type=Path, default=folder / "confidence-thresholds.json")
    parser.add_argument("--output", type=Path, default=folder / "litert-conformance.json")
    parser.add_argument("--tolerance", type=float, default=0.001)
    args = parser.parse_args()
    torch.set_num_threads(4)
    checkpoint = YOLO(str(args.checkpoint))
    names = checkpoint.names
    thresholds = json.loads(args.thresholds.read_text())["class_id_thresholds"]
    cutoffs = np.array([thresholds[str(index)] for index in range(len(names))])
    reference = checkpoint.model.fuse(verbose=False).eval()
    interpreter = Interpreter(model_path=str(args.model), num_threads=4)
    interpreter.allocate_tensors()
    inputs = interpreter.get_input_details()[0]
    outputs = interpreter.get_output_details()[0]
    assert inputs["dtype"] == outputs["dtype"] == np.float32
    assert inputs["shape"].tolist() == [1, 3, 640, 640]
    assert outputs["shape"].tolist() == [1, len(names) + 4, 8400]
    photos = sorted(path for path in args.images.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not photos:
        raise RuntimeError("No conformance images found")
    rows = []
    for photo in photos:
        image = cv2.imread(str(photo))
        if image is None:
            raise RuntimeError(f"Image could not be decoded: {photo}")
        image = LetterBox((640, 640), auto=False)(image=image)
        sample = np.ascontiguousarray(image[..., ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255
        with torch.inference_mode():
            expected = reference(torch.from_numpy(sample))[0].numpy()[0].copy()
        expected[:4] /= 640
        interpreter.set_tensor(inputs["index"], sample)
        interpreter.invoke()
        actual = interpreter.get_tensor(outputs["index"])[0]
        if not np.isfinite(actual).all():
            raise RuntimeError(f"Non-finite output for {photo.name}")
        difference = np.abs(actual - expected)
        pytorch_detections = decode(expected, cutoffs, names)
        litert_detections = decode(actual, cutoffs, names)
        classes_equal = [row["class_id"] for row in pytorch_detections] == [row["class_id"] for row in litert_detections]
        rows.append({
            "image": photo.name, "sha256": digest(photo),
            "maximum_normalized_coordinate_error": float(difference[:4].max()),
            "maximum_class_score_error": float(difference[4:].max()),
            "same_post_nms_classes": classes_equal,
            "pytorch_detections": pytorch_detections,
            "litert_detections": litert_detections,
        })
        print(f"Verified {photo.name}: max error {difference.max():.8f}, same classes {classes_equal}", flush=True)
    passed = all(row["maximum_normalized_coordinate_error"] <= args.tolerance
                 and row["maximum_class_score_error"] <= args.tolerance
                 and row["same_post_nms_classes"] for row in rows)
    report = {
        "schema_version": "1.0", "task": "board_export_conformance",
        "passed": passed, "release_eligible": False, "evaluation_valid": False,
        "purpose": "Known-photo numerical export check; not an independent accuracy evaluation or Android preprocessing conformance",
        "checkpoint_sha256": digest(args.checkpoint), "model_sha256": digest(args.model),
        "model_bytes": args.model.stat().st_size,
        "environment": {"platform": platform.platform(), "python": platform.python_version(),
                        **{package: importlib.metadata.version(package) for package in ("torch", "ultralytics", "litert-torch", "ai-edge-litert")}},
        "input_shape": inputs["shape"].tolist(), "output_shape": outputs["shape"].tolist(),
        "preprocessing": "OpenCV RGB float32 /255; Ultralytics LetterBox 640x640 auto=False; NCHW",
        "comparison": "PyTorch decoded xywh divided by 640 against normalized LiteRT xywh; raw class scores unchanged",
        "absolute_tolerance": args.tolerance, "class_id_thresholds": thresholds,
        "nms_iou_threshold": 0.7, "image_count": len(rows), "images": rows,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "image_count", "model_sha256", "model_bytes")}), flush=True)
    if not passed:
        raise SystemExit("Export conformance failed")


if __name__ == "__main__":
    main()
