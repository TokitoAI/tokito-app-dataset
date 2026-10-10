# ESP-12E video review

The iQOO source video `video_20261010_122211.mp4` is retained unchanged in
`data/video-captures/2026-10-10/`. Its SHA-256 matches the device file.
Ten upright keyframes retain actual source frame indexes and presentation timestamps.
All frames belong to one capture session and one conservatively assigned bench
specimen; they must stay in the same split group as that specimen's photos.

The reviewed last keyframe shows a module shield marked `MODEL: ESP-12E` and
carrier PCB text `Ver 0.1`. Four visible-body polygons and fifteen individually
identified right-header solder contacts are recorded in
`esp12e-keyframes/reviewed-component-masks.json`. Repeated ground and power aliases
have distinct instance IDs. Contact circles are approximate visible regions,
not physical calibration landmarks or full segmentation masks.

Controller and regulator exact ordering codes remain unreadable. Their IDs are
local instance identifiers, not verified schematic reference designators. The RF
shield mask is distinct from the complete module assembly, including its antenna.
USB annotation covers the visible shell body. This partial frame does not provide
a complete board outline, left header, metric calibration, underside or verified
physical flip sequence. No electrical GPIO mapping or numeric pinout is asserted.

These annotations are excluded from training and production export. Synthetic
views cannot replace missing real observations. Before model training, finish
visible component/contact coverage, match source design and orientation, join
independently selectable component geometry, and establish leakage-safe evaluation.

Validate the downloaded payload and reviewed geometry locally:

```powershell
python scripts/validate_board_video.py data/video-captures/2026-10-10/esp12e-keyframes/manifest.json
```

Review previews live beside the keyframes. The original video and JPEGs use Git LFS.
