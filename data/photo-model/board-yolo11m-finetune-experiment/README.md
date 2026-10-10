# YOLO11m dynamic fine-tune candidate

This medium YOLO11m checkpoint fine-tunes the earlier five-family board detector. Training used a 1,000-epoch ceiling and stopped dynamically at epoch 113 after 100 epochs without a new best validation result; epoch 13 was selected. The checkpoint stores readable board-family names; see `../board-class-display-names.json`.

The candidate's confidence-integrated mAP50-95 is 0.9417 versus 0.9186 for the baseline (mAP50 is 0.995 for both). A manual fixed-confidence audit at 0.75 and IoU 0.5 found 11 true detections, 1 false positive and 0 misses for this fine-tune; the extra Raspberry Pi prediction at 0.7606 was on an Ultimainboard photo. The baseline had 11 true detections, 0 false positives and 0 misses. A Pi-only threshold of 0.78 removes that false positive on the same fold, but this threshold was selected after inspecting that error and needs independent validation. See `confidence-thresholds.json` and the exact counts in `training-report.json`.

These are diagnostic comparisons only: the fold has one physical specimen per family, shares specimens with training and contains no ESP32 image.

`best.pt` is the selected PyTorch checkpoint. `best.tflite` is the matching fine-tuned LiteRT export; `litert-conformance.json` records numerical agreement on all 11 known validation photos. The model was also run through the iQOO I2501 live-camera smoke app: it detected an Ultimainboard 2.1.4 at 0.7786 confidence with a single observed inference time of about 1.07 seconds. See `android-camera-smoke.json`. This is one known specimen and one live observation, not independent accuracy or performance validation.

This detector identifies the board family only. In the live smoke test, the separate component detector returned two generic `ic` labels and no exact part names; its report also marks evaluation invalid. It does not identify component part numbers, designators, pins, BOMs, schematics or Gerbers. Parts and pins must be resolved after board detection through reviewed, revision-aware photo-to-source links. The 240 current component boxes are partial seeds, not complete training labels.
