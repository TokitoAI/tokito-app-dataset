# YOLO11m dynamic fine-tune candidate

This medium YOLO11m checkpoint fine-tunes the earlier five-family board detector. Training used a 1,000-epoch ceiling and stopped dynamically at epoch 113 after 100 epochs without a new best validation result; epoch 13 was selected. The checkpoint stores readable board-family names; see `../board-class-display-names.json`.

The candidate's confidence-integrated mAP50-95 is 0.9417 versus 0.9186 for the baseline (mAP50 is 0.995 for both). A manual fixed-confidence audit at 0.75 and IoU 0.5 found 11 true detections, 1 false positive and 0 misses for this fine-tune; the extra Raspberry Pi prediction at 0.7606 was on an Ultimainboard photo. The baseline had 11 true detections, 0 false positives and 0 misses. A Pi-only threshold of 0.78 removes that false positive on the same fold, but this threshold was selected after inspecting that error and needs independent validation. See `confidence-thresholds.json` and the exact counts in `training-report.json`.

These are diagnostic comparisons only: the fold has one physical specimen per family, shares specimens with training and contains no ESP32 image.

`best.pt` is the selected PyTorch checkpoint. `results.csv` and the plots preserve its training history. A LiteRT export was not produced in this Windows environment because this Ultralytics LiteRT exporter supports Linux x86/macOS only. The previous baseline LiteRT file in `../board-yolo11m-experiment/` does not contain these fine-tuned weights.

This detector identifies the board family only. It does not detect or identify component part numbers, designators, pins, BOMs, schematics or Gerbers. Parts and pins must be resolved after board detection through reviewed, revision-aware photo-to-source links. The 240 current component boxes are partial seeds, not complete training labels.
