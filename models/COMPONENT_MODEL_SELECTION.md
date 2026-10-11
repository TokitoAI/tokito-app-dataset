# Component segmentation model selection

## Use this checkpoint for the current implementation

Use [`component-segmentation-v2/best.pt`](component-segmentation-v2/best.pt) (Git LFS) as the current YOLO11m segmentation candidate. Its SHA-256 is `bde65db58f0aa724b9bb84a98e9f71c9657f2a3c07a07b7074f93424bb81eea9`.

The model predicts eight **generic visible package** classes: `ic_package`, `chip_passive`, `connector`, `rf_module`, `switch`, `crystal`, `discrete_semiconductor`, and `inductor`. It does not predict exact component SKUs, board-specific reference designators, pin identities, or 3D coordinates. Those need a separate board-family/component registration layer grounded in markings and revision-matched BOM/PCB sources.

## Do not select the partial diagnostic checkpoint

[`partial-component-diagnostic/best.pt`](partial-component-diagnostic/best.pt) is an experiment trained on incomplete masks with a custom ignore-aware loss. At its documented confidence of 0.25, it recalls only 3 of 44 reviewed validation instances (0.068); its threshold sweep trades substantial false positives for more recall. It is not a replacement or a production model.

## Evidence and limits

The selected v2 checkpoint's [`REPORT.json`](component-segmentation-v2/REPORT.json) records the training run and diagnostic evaluations: 25 epochs, best epoch 2; 0.75 precision and 0.30 recall on a partial external connected-region audit, and 1.0 scoped precision with 0.136 recall on known-specimen Tokito partial masks. The report marks both evaluations invalid for general accuracy claims and the model ineligible for production. Do not describe these as independent board accuracy or complete-image component metrics.

This selection answers which existing artifact to integrate while annotation and evaluation improve. Keep model output confidence visible and allow abstention; do not interpret a generic mask as an exact part identity. The model file is tracked through Git LFS, so clone with Git LFS installed and run `git lfs pull`.
