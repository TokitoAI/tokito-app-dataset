# Partial component segmentation diagnostics

`partial_component_segmentation_loss.py` provides an isolated loss for the local
Ultralytics **8.4.174** / YOLO11 segmentation runtime. It does not change source
annotations, the production export gate, or the existing complete-data trainer.

Stock YOLO treats every unassigned anchor as a classification negative. On a
partially labelled board this penalizes actual components that have not yet been
reviewed. The diagnostic loss keeps Ultralytics assignment, bounding-box loss,
DFL, and reviewed-instance mask loss, but multiplies elementwise classification
BCE by the union of:

- anchors assigned a reviewed positive (all classes retain supervised competition);
- anchor centres inside explicitly reviewed empty-background pixels.

Every other unassigned anchor has exactly zero classification loss and zero
classification-logit gradient. Reviewed positives keep their original soft
assignment scores and normalization. Mask loss remains cropped to the bounding
box of each reviewed instance. That requires the instance's complete visible
body polygon, not a partial trace across one edge of an object.

## Required integration contract

Pass `reviewed_background_masks` as a boolean `[batch,height,width]` tensor in the
**actual `batch['img']` canvas**. True means a reviewer established that the pixel
contains no component in the defined classes. Unlabelled board surface, unknown
parts, occluded objects, empty connector holes, and unreviewed pixels are not
implicitly background. An all-false raster is allowed and trains positives only;
it cannot teach false-positive suppression and must not be presented as an
accurate detector.

The factory `build_partial_segmentation_loss(model)` returns a criterion; attach
it to the already device/configured training model. Missing rasters, nonboolean
rasters, mismatched raster/image sizes, unknown runtime versions, E2E heads and
auxiliary semantic heads fail. No package monkeypatch is required.

The raster must follow the same proven resize/letterbox operation as the source
image and instance polygons, including border placement. The loss intentionally
never guesses or resizes this raster. Upstream batching must establish the
image/hash/annotation linkage and transform consistency.

Do not launch this through an unchanged stock data loader. Disable mosaic,
mixup, cutmix, copy-paste, rotations, translate, scale, shear, perspective,
fliplr, flipud, multi-scale and random resizing/cropping. Leave them disabled
until the raster follows each operation with tested equivalence. The current
loss tests cover fixed canvases, not an arbitrary augmentation pipeline. Pinning
an augmentation flag alone is not proof that background rasters align.

## Verification

Run in the GPU runtime:

```
E:/tokito-build/yolo-gpu-runtime/Scripts/python.exe -m unittest discover -s tests -p test_partial_component_segmentation_loss.py -v
```

The tests verify ignored negatives have zero gradients on CPU and CUDA, reviewed
positives and reviewed background retain stock BCE, changing ignored logits
cannot change the objective, invalid canvases fail, and a real YOLO11m-seg
128-pixel CUDA forward/loss/backward keeps positive and reviewed-background
classification gradients while suppressing every unassigned unknown anchor's
classification gradient.

These are loss correctness tests, not accuracy measurements. Training from these
partial views is a **known-specimen diagnostic**. It does not create independent
validation/test data or verify installed component part numbers, pin electrical
identity, OCR, calibration, AR alignment, mobile performance or production
precision/recall. The existing complete-data trainer remains the production path.

## Launched diagnostic adapter

`train_partial_component_diagnostic.py` builds a fixed 640-pixel letterbox canvas
with a tested common transform for images, polygons and background rasters. It
uses no geometry augmentation. Partial labels never enter a stock YOLO loss.
The run is a YOLO11m-seg / AdamW / batch-one / AMP experiment with a 1e-5 peak learning rate, lowered after the initial 1e-3 run diverged. It has a 1000-epoch
ceiling and patience 80 on held-out **partial validation loss**. That loss is not
precision, recall or production accuracy.

The prepared manifest contains 394 reviewed body instances, 21 observable
classes, ten training images and four validation images. Oct10 photo bursts are
kept together; separate ESP32/ESP12E videos and the NXP Oct9 session form known-
specimen validation. Ultimaker has no separate validation view. No independent
specimen test split exists. Typed chip resistors/capacitors and unknown chip
passives share one observable body class. Source BOM candidates do not become
installed part names. Readable CP2102, MCXN236 and 25Q64JV families stay separate;
ESP12E shield surfaces stay separate from complete ESP32 module substrates.

The audited-region evaluator greedily matches predicted masks to reviewed
positive masks at mask IoU 0.5 and confidence 0.25. A matching-class mask is a
true positive. Unmatched duplicate/wrong-class masks with IoU at least 0.5 to a
reviewed positive, or masks occupying at least 90% reviewed empty background,
are false positives. Remaining unmatched predictions are ignored. Unmatched
reviewed ground-truth bodies are false negatives. Counts and region scope must
accompany metrics; these measurements cannot describe unreviewed pixels or
unseen boards. A numerical test verifies all five adjudication cases.

The live handle/log and prepared manifest are in ignored
`work/partial-component-diagnostic/`. The parent coordinates final checkpoint
publication and mobile export. Normal Ultralytics checkpoints omit the training
criterion, preserving standard inference loading.

The full-resolution segmentation objective uses eight-instance chunks with
activation checkpointing. Loss values and gradients match stock segmentation
loss numerically; this removes its huge foreground-by-640-by-640 BCE temporary
without lowering mask resolution, shrinking the model or changing labels.
Metadata-only CI skips this optional numerical test module when torch is absent;
the dedicated GPU runtime runs all eight tests.

## Latest checkpoint audit — 2026-10-11

The dynamic run already completed; do not repeat it from the same partial labels
and present the result as a new accuracy gain. `work/partial-component-diagnostic/run/progress.json`
is authoritative: 91 epochs completed under a 1000-epoch ceiling, patience 80,
best validation partial loss at epoch 11, and stop reason `patience`. The
checkpoint is `models/partial-component-diagnostic/best.pt` with SHA-256
`c49095ae6802c418a1c1d04094b6a7f0740a46df820fde48cb3afca94f02b38e`.

At confidence 0.25, the four known-specimen partial validation frames yielded
3 true-positive reviewed masks, 4 false positives in audited regions, 41
missed reviewed masks and 8 ignored predictions: audited-region precision
0.429 and reviewed-instance recall 0.068. The separate confidence sweep traded
that high-cutoff precision for recall (at confidence 0.01: precision 0.288,
recall 0.477, 52 audited-region false positives). Both are diagnostic-only,
not held-out accuracy. The checkpoint is not an every-part detector and must
not be selected as production-ready from these measurements.

The latest dataset audit found 435 source records / 409 unique image-instance
pairs across 14 reviewed frames; all polygon integrity checks pass, but no
frame has verified exhaustive visible-component coverage. The generated
`data/photo-model/component-review-backlog.json` is the annotation queue.
See [public component dataset audit](PUBLIC_COMPONENT_DATASET_AUDIT_2026-10-11.md)
for external sources and access/licensing status. A meaningful next checkpoint
requires additional complete Tokito masks and independent specimen/session
evaluation, or a reviewed import of compatible public instance masks.
