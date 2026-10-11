# ESP-12E component segmentation smoke export

`python scripts/export_esp12e_component_smoke.py` exports the explicitly complete-reviewed ESP-12E top-side image into a conventional YOLO segmentation directory at `data/photo-model/component-smoke-esp12e/`. Run `python scripts/export_esp12e_component_smoke.py --check` to verify image/annotation hashes, dimensions, polygon-derived label formatting, class IDs and counts without rewriting the export.

The fixture includes 22 reviewed, classifiable component bodies from one 3072 × 4080 photograph. The defocused `unknown_package` remains excluded from class training. This is enough to exercise a segmentation parser, mask rendering, class mapping, and image pre/postprocessing in the app.

This is **not** a train/validation/test dataset. Its convenience `data.yaml` points all three keys to the same image so standard loaders can be smoke-tested; training and metric reporting on it are prohibited. It represents one known specimen, one capture session and one top-side pose. It provides no independent evaluation, other board families, underside/oblique coverage, pin labels, exact installed part IDs, camera calibration or 3D registration.

The recommended current model remains [`../models/component-segmentation-v2/best.pt`](../models/component-segmentation-v2/best.pt), as recorded in the [model selection note](../models/COMPONENT_MODEL_SELECTION.md). The smoke fixture is useful for integration checks while complete annotations and independent specimens are collected; it does not establish that model as production-ready.
