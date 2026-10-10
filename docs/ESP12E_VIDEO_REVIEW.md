# ESP-12E video review

The iQOO source video `video_20261010_122211.mp4` is retained unchanged in
`data/video-captures/2026-10-10/`. Its SHA-256 matches the device file.
Ten upright keyframes retain actual source frame indexes and presentation timestamps.
All frames belong to one capture session and one conservatively assigned bench
specimen; they must stay in the same split group as that specimen's photos.

The reviewed last keyframe shows a module shield marked `MODEL: ESP-12E` and
carrier PCB text `Ver 0.1`. Eighteen visible-body polygons and fifteen individually
identified right-header solder contacts are recorded in
`esp12e-keyframes/reviewed-component-masks.json`. Repeated ground and power aliases
have distinct instance IDs. Contact circles are approximate visible regions,
not physical calibration landmarks or full segmentation masks.

Body coverage includes two tactile switches, visible passive bodies and two
three-terminal semiconductor bodies. Markings are retained as observed strings;
the resistor above the upper three-terminal body has an ambiguous first digit
(`?21`) and is not assigned a resistance value. Exact ordering codes, physical
placement and source reference designators are still unconfirmed. These local
instance IDs identify photographed bodies only.

Controller and regulator exact ordering codes remain unreadable. Their IDs are
local instance identifiers, not verified schematic reference designators. The RF
shield mask is distinct from the complete module assembly, including its antenna.
USB annotation covers the visible shell body. This partial frame does not provide
a complete board outline, left header, metric calibration, underside or verified
physical flip sequence. No carrier electrical GPIO mapping or numeric header pinout is asserted.

`reviewed-module-contacts.json` separately records 22 module contact correspondences
to the Ai-Thinker ESP-12E Version 1.0 top-view diagram and pin table (pages 7, 8,
10). The manufacturer-authored PDF was retrieved from a third-party mirror; its
URL and exact digest are retained. Side points mark visible castellation hole
centers; bottom points mark visible gold lands. These different physical features
must not be substituted for footprint pad centers in metric calibration. The
source-family correspondence does not establish carrier connectivity, specimen
electrical continuity, or hidden ESP8266EX chip pins. The contact preview has
been visually inspected against the original frame and the source diagram.

These annotations are excluded from training and production export. Synthetic
views cannot replace missing real observations. Before model training, finish
visible component/contact coverage, match source design and orientation, join
independently selectable component geometry, and establish leakage-safe evaluation.

Validate the downloaded payload and reviewed geometry locally:

```powershell
python scripts/validate_board_video.py data/video-captures/2026-10-10/esp12e-keyframes/manifest.json
```

Review previews live beside the keyframes. The original video and JPEGs use Git LFS.
