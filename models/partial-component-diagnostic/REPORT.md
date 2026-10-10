# Partial component YOLO11m-seg diagnostic

This checkpoint is a reproducible, known-specimen diagnostic trained with ignore-aware loss on incomplete component masks. It is not a production model.

Training used 10 images, 394 reviewed body masks, 21 observable body classes, 640-pixel inputs, batch size 1, AMP, an AdamW peak learning rate of 1e-5, a 1,000-epoch ceiling and patience 80. It stopped at epoch 91 after 80 epochs without improving the held-out partial loss; epoch 11 was selected. Four validation images came from the same known physical specimens/capture sources, and Ultimaker has no validation image. There is no independent specimen test.

At mask IoU 0.5 and confidence 0.25, audited-region evaluation found 3 true positives, 4 false positives within reviewed regions and 41 missed reviewed instances: precision 0.429 and recall 0.068. Predictions outside reviewed background/positive regions are ignored. These values are not full-scene accuracy and show that this checkpoint is not useful for production use.

The files beside this model include the exact source/annotation manifest, epoch history, and scoped metric counts. Checkpoint SHA-256: `c49095ae6802c418a1c1d04094b6a7f0740a46df820fde48cb3afca94f02b38e`.
