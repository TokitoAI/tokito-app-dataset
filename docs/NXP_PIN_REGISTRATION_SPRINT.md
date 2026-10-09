# FRDM-MCXN236 photo pin registration sprint

## Result

The ten contact openings in J12 (MCU SWD 2×5 header) are visually distinguishable in `data/photo-model/photos/raw/IMG_20261009_221755_1.jpg`. Candidate 16×16 pixel boxes and the Rev C CAD pad-number/net mapping are recorded in `annotations/nxp-pin-proposals.json`. These are **not reviewed photo pin labels**: the specimen PCB revision is unconfirmed, and the board's physical pin-1 mark is not legible in this photo. Keep them out of `annotations/pin-annotations.json` and training labels until those checks are resolved.

## Evidence checked

- The source image is 1600×3888 pixels, SHA-256 `39fc7bf72f364c0b0e848dc9fe9492b85efbdef1481a28d9bbecf4787e51a47e`. J12's populated object is `nxp_seed_006`; its adjacent `J12` and `MCU SWD` marks are visible. The review crop is `previews/mcxn236-source-links/nxp_seed_006-rot90-2x.png`, derived from original pixels `[1060,3450,1520,3888]` (90° counterclockwise, 2×).
- The official Rev C Allegro source is `data/board-sources/nxp-frdm-mcxn236/original-design-files/Design Files/LAY-90828_C.brd`, imported into `data/board-sources/nxp-frdm-mcxn236/generated-kicad/FRDM-MCXN236.imported.kicad_pcb`. The imported J12 footprint is at `(-1.159993,-6.085002)` mm with 90° rotation. Its local pad coordinates are `(0,0)` for 1, `(1.27,0)` for 2, and successive numbered pairs at local y increments of 1.27 mm through pads 9 and 10. F.SilkS includes `1`, `2`, `9`, `10`, and `MCU SWD` text.
- Board-scale orientation is consistent between CAD and photo: J3 and J4 lie on the photo's right edge, J5/J6 above the central IC, and J12 near the lower right edge. The J12 `MCU SWD` text lies to the right of the photographed socket, matching the rotated CAD footprint. Under this registration, the raw photo's upper-left contact is CAD pad 10, upper-right is pad 9, lower-left is pad 2, and lower-right is pad 1.
- The CAD pad nets agree with the Rev C native extracted netlist. The proposal's box centers were manually read from the bright metal contacts in the unrotated original photo at approximately x=1241/1279 and y=3659/3702/3744/3788/3832. Box edges remain approximate at this resolution.

## Approval blockers

1. The physical board revision marking has not been confirmed against the Rev C layout. J12's local topology could be unchanged across revisions, but that cannot be assumed for a verified pin label.
2. The F.SilkS pin-1 numeral near J12 is hidden or unreadable in the available image; CAD/photo alignment alone is a candidate association. A straight, sharp close-up showing the header, one end's `1` or keyed notch, and the board revision would independently confirm the numbering.
3. The source conversion has reported padstack warnings and the generated board has DRC violations. The extracted source netlist and pad numbering are useful reference data but not fabrication-approved evidence.

The proposal is a review queue item. All ten pin numbers and source nets should be promoted together only after pin 1 and revision are checked on the physical specimen.
