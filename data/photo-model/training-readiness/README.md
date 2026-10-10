# Medium component training readiness

The runtime evidence is synthetic, not dataset training or accuracy evidence.
With single CPU threads, batch 1 and mixed precision, random-weight YOLO11m-seg
completed loss/backward and one optimizer step at 640×640 on the RTX 3050 Laptop
GPU. Gradients were finite; peak allocated VRAM was 751,265,280 bytes. This shows
an initial viable configuration, not long-run stability on dense PCB labels.
Earlier float32 640 execution failed allocation and is retained for transparency.

No final component model checkpoint has been produced. Reviewed real masks remain
partial and source identities incomplete. The 45-mask dense NXP file and the
255 drawn planar source proposals are explicitly candidates, not accepted labels.
Unannotated visible components must not silently become background in YOLO loss.
Complete the relevant class coverage or implement tested ignore-region losses.

`scripts/train_reviewed_components.py` defaults to readiness validation. It requires
reviewed exhaustive coverage, image/label hashes, resolved identities and explicit
specimen splits before `--run`. Config: YOLO11m segmentation, maximum 1000 epochs,
patience 80, 640 pixels, batch 1, mixed precision, single threads, AdamW/cosine;
select best checkpoint with validation, then evaluate the locked test set. A
known-specimen/view-specific diagnostic study needs a separate explicitly scoped
manifest; it cannot be reported as unseen-specimen production accuracy.

Segmentation training alone does not complete exact instance identities, pin
numbering, metric anchors, mobile export or physical rotation/flip verification.
The final ZIP remains deferred until those required gates and construction pass.
