# YOLO segmentation phone test preparation

This is a diagnostic camera test path for the forthcoming component segmentation checkpoint. It is not model release approval or an accuracy evaluation.

## Verified device and existing application

On 2026-10-11, ADB initially listed no devices. After reconnection it listed authorized serial `10BFC41S57001UZ`, model `I2501` (iQOO). Installed package `dev.tokito.componentsmoke` is debuggable and exposes its existing smoke report. Its current component runtime is **detection only**: it requires exactly one output with `4 + C` channels and draws boxes. A YOLO segmentation export must not be substituted into that application unchanged.

The existing source is in the Tokito mobile repository under `physical-runtime/component-camera-smoke`, with its runtime at `physical-runtime/app/src/main/java/dev/tokito/physical/LocalComponentVisionRuntime.kt`.

## Required segmentation contract

- One float32 RGB input, NCHW `[1,3,S,S]` or NHWC `[1,S,S,3]`, normalized to `[0,1]`.
- Two float32 outputs: predictions `[1,4+C+32,N]` (or transposed) and 32 prototype channels `[1,32,H,W]` (or NHWC).
- `C` and class order come directly from `checkpoint.names`; generic package labels never establish exact installed identities.
- ONNX box coordinates are model-input pixels. Standard Ultralytics TFLite box coordinates are normalized; the manifest records this distinction.
- Decode class scores separately from mask coefficients; perform class-aware NMS, multiply coefficients by prototypes, crop each mask to its detection box, and undo letterbox padding when rendering on the camera preview.
- The local prototype renderer is a diagnostic coarse-mask visualization. It uses prototype-grid thresholding and is not claimed to match a production-resolution renderer at mask boundaries.

The prepared training manifest currently has **21 classes at input size 640**, so the expected prediction shape is `[1,57,8400]` and prototype shape is `[1,32,160,160]`. The verifier still reads the actual checkpoint class list and rejects shape disagreement rather than trusting this documented count.

## Export conformance before deployment

[The verifier](../scripts/verify_partial_model_phone.py) compares checkpoint and exported raw prediction/prototype tensors, class order after NMS, and decoded mask IoU. It rejects disagreement and writes hashes, shapes, labels, and binary mask PNG evidence. Its synthetic self-check exercises NMS, normalized/pixel boxes, tensor layouts and negative mask logits:

```powershell
python scripts/verify_partial_model_phone.py --self-test
```

Once the **new** diagnostic checkpoint exists, export it using the environment that supports Ultralytics export. Do not reuse external PCBVision checkpoints or older generic detector weights under the new model identity. Run:

```powershell
python scripts/verify_partial_model_phone.py `
  --checkpoint work/partial-component-diagnostic/run/weights/best.pt `
  --export-model <matching-float32-export.tflite> `
  --image data/phone-captures/2026-10-10/IMG_20261010_092221.jpg `
  --output work/phone-yolo-diagnostic/conformance.json `
  --phone-bundle work/phone-yolo-diagnostic/assets
```

`--phone-bundle` creates `model.tflite` plus a hash-verified `component-manifest.json` only after conformance passes. Both remain `release_eligible: false` and `evaluation_valid: false`. This test uses a known captured specimen and does not measure unseen-board generalization.

An isolated native camera smoke project is prepared in ignored `work/phone-yolo-diagnostic/android`, using distinct package `dev.tokito.yolosegsmoke`. It implements two-output prototype decoding and colored masks, retains class names, records the model hash in its camera report, and leaves the existing mobile application and AR/alignment code untouched. Build its debug APK using the existing Gradle wrapper with `TOKITO_SMOKE_ASSETS_DIR` set to the newly verified bundle. An APK compiled without assets is only a compile check and must not be deployed as a completed model test.

The isolated application's empty-assets compile check passed on 2026-10-11. Its final labels/model assets must come from the new checkpoint; the build check does not prove inference or segmentation quality. Run export and numerical comparison on CPU while GPU training remains active to avoid competing for the laptop's GPU memory.

## Remaining evidence gates

The new checkpoint must finish training; its matching float32 export must pass conformance; the asset-containing APK must build; and the actual iQOO camera report/screenshot must show that exact new model hash and segmentation output. Until those events occur, device connectivity, source code and a successful compile do not constitute an on-device inference result.
