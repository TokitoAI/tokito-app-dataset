"""Verify a diagnostic YOLO segmentation export before Android integration.

This validates two-output tensor decoding; it does not deploy a model or measure
recognition accuracy. ONNX boxes are input pixels; Ultralytics TFLite boxes are
normalized. Direct PyTorch-to-LiteRT exports retain pixel boxes and require the
explicit coordinate flag. Masks stay in the square letterboxed input frame.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def decode(prediction, prototypes, names, size, normalized=False, conf=.25, iou=.45):
    """Decode YOLO11 segmentation scores, NMS and binary prototype masks."""
    raw = np.asarray(prediction, dtype=np.float32)
    proto = np.asarray(prototypes, dtype=np.float32)
    if raw.ndim != 3 or proto.ndim != 4 or raw.shape[0] != 1 or proto.shape[0] != 1:
        raise ValueError("Expected one rank-3 prediction and one rank-4 prototype output")
    # Ultralytics ONNX uses BCHW; common TFLite exports use BHWC prototypes.
    if proto.shape[1] != 32 and proto.shape[-1] == 32:
        proto = proto.transpose(0, 3, 1, 2)
    channels = 4 + len(names) + proto.shape[1]
    if raw.shape[1] == channels:
        raw = raw[0]
    elif raw.shape[2] == channels:
        raw = raw[0].T
    else:
        raise ValueError(f"Prediction shape {raw.shape} disagrees with {len(names)} classes and {proto.shape[1]} coefficients")
    if not np.isfinite(raw).all() or not np.isfinite(proto).all():
        raise ValueError("Non-finite model output")
    classes = raw[4:4 + len(names)].argmax(0)
    scores = raw[4:4 + len(names)].max(0)
    xywh = raw[:4].T.copy() * (size if normalized else 1)
    boxes = np.concatenate((xywh[:, :2] - xywh[:, 2:] / 2, xywh[:, :2] + xywh[:, 2:] / 2), axis=1)
    order = np.flatnonzero((scores >= conf) & (xywh[:, 2:] > 0).all(1))
    order = order[np.argsort(-scores[order], kind="stable")]
    kept = []
    for index in order:
        b = boxes[index]
        suppress = False
        for previous in kept:
            if classes[index] != classes[previous]:
                continue
            p = boxes[previous]
            area = np.maximum(0, np.minimum(b[2:], p[2:]) - np.maximum(b[:2], p[:2])).prod()
            union = np.maximum(0, b[2:] - b[:2]).prod() + np.maximum(0, p[2:] - p[:2]).prod() - area
            if union > 0 and area / union > iou:
                suppress = True
                break
        if not suppress:
            kept.append(int(index))
        if len(kept) >= 300:
            break
    import cv2
    _, _, height, width = proto.shape
    rows = []
    for index in kept:
        coefficients = raw[4 + len(names):, index]
        logits = coefficients @ proto[0].reshape(proto.shape[1], -1)
        logits = logits.reshape(height, width)
        # Crop the prototype logits to the box before interpolation, matching
        # Ultralytics process_mask. Outside-box logits become zero (false).
        scaled = boxes[index] * np.array([width, height, width, height]) / size
        xx, yy = np.arange(width)[None, :], np.arange(height)[:, None]
        inside = (xx >= scaled[0]) & (xx < scaled[2]) & (yy >= scaled[1]) & (yy < scaled[3])
        binary = cv2.resize(logits * inside, (size, size), interpolation=cv2.INTER_LINEAR) > 0
        rows.append({"class_id": int(classes[index]), "class_name": names[int(classes[index])],
                     "confidence": float(scores[index]), "box_xyxy_input_pixels": boxes[index].tolist(),
                     "mask": binary, "identity_status": "diagnostic_model_class_only"})
    return rows


def self_test():
    pred = np.zeros((1, 4 + 2 + 32, 2), np.float32)
    pred[0, :4, :] = np.array([[32, 32], [32, 32], [32, 32], [32, 32]])
    pred[0, 4, :] = [.9, .8]
    pred[0, 6, :] = 1
    proto = np.ones((1, 32, 16, 16), np.float32)
    rows = decode(pred, proto, ["body_a", "body_b"], 64)
    assert len(rows) == 1 and rows[0]["class_name"] == "body_a"
    assert rows[0]["mask"][32, 32] and not rows[0]["mask"][0, 0]
    normalized = pred.copy()
    normalized[:, :4] /= 64
    alt = decode(normalized.transpose(0, 2, 1), proto.transpose(0, 2, 3, 1), ["body_a", "body_b"], 64, True)
    assert np.array_equal(rows[0]["mask"], alt[0]["mask"])
    pred[0, 6, :] = -1
    assert not decode(pred, proto, ["body_a", "body_b"], 64)[0]["mask"].any()
    print("Segmentation decoder synthetic NMS/layout/mask checks passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--export-model", type=Path)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--output", type=Path, default=Path("work/phone-yolo-diagnostic/conformance.json"))
    parser.add_argument("--tolerance", type=float, default=.01)
    parser.add_argument("--phone-bundle", type=Path, help="Copy a conformant TFLite export and verified class manifest for the isolated Android smoke app")
    parser.add_argument("--tflite-box-coordinates", choices=("normalized", "pixels"), default="normalized")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.checkpoint or not args.export_model or not args.image:
        parser.error("--checkpoint, --export-model and --image are required")
    import cv2
    import torch
    from ultralytics import YOLO
    from ultralytics.data.augment import LetterBox
    checkpoint = YOLO(str(args.checkpoint))
    if checkpoint.task != "segment":
        raise ValueError("Checkpoint must be a segmentation model")
    names = [checkpoint.names[i] for i in range(len(checkpoint.names))]
    is_tflite = args.export_model.suffix.lower() == ".tflite"
    normalized = is_tflite and args.tflite_box_coordinates == "normalized"
    if args.phone_bundle and not is_tflite:
        parser.error("--phone-bundle requires a TFLite export")
    if is_tflite:
        try:
            from ai_edge_litert.interpreter import Interpreter
        except ImportError:
            from tensorflow.lite import Interpreter
        runtime = Interpreter(model_path=str(args.export_model), num_threads=4)
        runtime.allocate_tensors()
        inputs = runtime.get_input_details()
        outputs = runtime.get_output_details()
        input_shape = inputs[0]["shape"].tolist()
        if len(inputs) != 1 or len(outputs) != 2 or any(d["dtype"] != np.float32 for d in inputs + outputs):
            raise ValueError("Float32 single-input/two-output export required")
    else:
        import onnxruntime as ort
        runtime = ort.InferenceSession(str(args.export_model), providers=["CPUExecutionProvider"])
        inputs, outputs = runtime.get_inputs(), runtime.get_outputs()
        input_shape = inputs[0].shape
        if len(inputs) != 1 or len(outputs) != 2:
            raise ValueError("Single-input/two-output segmentation export required")
    nchw = input_shape[1] == 3
    size = int(input_shape[2] if nchw else input_shape[1])
    original = cv2.imread(str(args.image))
    if original is None:
        raise ValueError("Image decode failed")
    frame = LetterBox((size, size), auto=False)(image=original)
    sample = np.ascontiguousarray(frame[..., ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255
    reference = checkpoint.model.cpu().float().eval()
    reference.model[-1].export = True
    with torch.inference_mode():
        reference_pred, reference_proto = reference(torch.from_numpy(sample))
    expected_pred, expected_proto = reference_pred.numpy(), reference_proto.numpy()
    if is_tflite:
        runtime.set_tensor(inputs[0]["index"], sample if nchw else sample.transpose(0, 2, 3, 1))
        runtime.invoke()
        actual = [runtime.get_tensor(o["index"]) for o in outputs]
    else:
        actual = runtime.run(None, {inputs[0].name: sample if nchw else sample.transpose(0, 2, 3, 1)})
    pred = next((o for o in actual if o.ndim == 3), None)
    proto = next((o for o in actual if o.ndim == 4), None)
    if pred is None or proto is None:
        raise ValueError("Expected rank-3 predictions and rank-4 prototypes")
    canonical = pred if pred.shape[1] == expected_pred.shape[1] else pred.transpose(0, 2, 1)
    canonical = canonical.copy()
    if normalized:
        canonical[:, :4] *= size
    canonical_proto = proto if proto.shape == expected_proto.shape else proto.transpose(0, 3, 1, 2)
    if canonical.shape != expected_pred.shape or canonical_proto.shape != expected_proto.shape:
        raise ValueError("Export/checkpoint output shapes disagree")
    coordinate_error = float(np.abs(canonical[:, :4] - expected_pred[:, :4]).max() / size)
    score_coefficient_error = float(np.abs(canonical[:, 4:] - expected_pred[:, 4:]).max())
    prototype_error = float(np.abs(canonical_proto - expected_proto).max())
    reference_rows = decode(expected_pred, expected_proto, names, size)
    export_rows = decode(pred, proto, names, size, normalized)
    same_classes = [r["class_id"] for r in reference_rows] == [r["class_id"] for r in export_rows]
    mask_ious = []
    if same_classes:
        for first, second in zip(reference_rows, export_rows):
            union = np.logical_or(first["mask"], second["mask"]).sum()
            mask_ious.append(float(np.logical_and(first["mask"], second["mask"]).sum() / union) if union else 1.)
    valid = (max(coordinate_error, score_coefficient_error, prototype_error) <= args.tolerance
             and same_classes and all(value >= .98 for value in mask_ious))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(export_rows):
        mask_path = args.output.parent / f"mask-{index:03d}.png"
        cv2.imwrite(str(mask_path), row.pop("mask").astype(np.uint8) * 255)
        row["mask_path"] = mask_path.name
    report = {"schema_version": "1.0", "task": "component_segmentation_diagnostic", "release_eligible": False,
              "evaluation_valid": False, "export_conformance_passed": valid,
              "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
              "model_sha256": hashlib.sha256(args.export_model.read_bytes()).hexdigest(),
              "class_names": names, "input_shape": input_shape, "output_shapes": [list(o.shape) for o in actual],
              "coordinates_normalized": normalized, "mask_coordinate_frame": "square_letterboxed_model_input",
              "maximum_normalized_box_error": coordinate_error, "maximum_score_coefficient_error": score_coefficient_error,
              "maximum_prototype_error": prototype_error, "same_post_nms_classes": same_classes, "mask_ious": mask_ious,
              "detections": export_rows, "existing_android_smoke_decoder_compatible": False,
              "android_requirement": "Use two-output segmentation decoder; current one-output detection loader rejects this export."}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(args.output), "conformance_passed": valid, "detections": len(export_rows)}))
    if not valid:
        raise SystemExit(1)
    if args.phone_bundle:
        import shutil
        args.phone_bundle.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.export_model, args.phone_bundle / "model.tflite")
        manifest = {"schema_version": "1.0", "task": "component_segmentation_diagnostic",
                    "release_eligible": False, "evaluation_valid": False,
                    "model_sha256": report["model_sha256"], "source_checkpoint_sha256": report["checkpoint_sha256"],
                    "input_size": size, "class_names": names, "confidence_threshold": .25, "iou_threshold": .45,
                    "maximum_detections": 30, "coordinates_normalized": normalized,
                    "identity_status": "diagnostic_model_class_only", "class_names_source": "checkpoint.names"}
        (args.phone_bundle / "component-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
