# Dense YOLO review QA

Four dense files contain 370 body annotation records: ESP32 84, ESP8266 89, NXP 104 and Ultimaker 93. Source hashes, dimensions and polygon bounds pass the annotation integrity validator. That check does not prove complete class coverage, exact identities or pixel-perfect masks.

Representative original-pixel overlays and originals were visually inspected for all four boards. They show physical package bodies rather than mounting holes, bare PCB pads or detached silkscreen boxes. Small blurred packages have greater boundary uncertainty. Leads/contacts are generally excluded; pin labels remain a separate scope. Whole-frame coverage is still partial.

## Corrections and training contracts

QA found ESP32 `rf_module` masks spanning the complete module substrate/antenna while ESP8266 `rf_module` masks span only the metal shield. Parent corrected the ESP8266 dense and legacy rows to `rf_shield`; these classes must stay distinct in export/training.

ESP32 `chip_passive` contains unresolved passive identities. Other boards use typed resistor/capacitor labels. A pooled classifier must use an explicit common observable passive-body class or ignore typed classification where the identity is unresolved; it cannot infer installed resistor/capacitor labels from a candidate BOM or appearance alone. `switch`/`tactile_switch`, connector types and crystal/resonator types also need a documented common output taxonomy.

Twenty-six instance keys repeat between dense and older central/legacy files. All repeated polygons are identical; there are zero polygon conflicts. They must be deduplicated by image hash and instance ID, with the dense/superseding file authoritative. Legacy records supply provenance, not extra targets. The ESP32 source-annotation hash join matches the current central mask file.

## Limits

Unreviewed board pixels remain unknown, not background. All dense datasets remain ineligible for a complete standard whole-frame component export. An ignore-aware diagnostic may learn reviewed positive bodies and explicitly reviewed empty outside-board negatives, with the rest ignored. It must not claim full-scene precision/recall from partial ground truth.

The current board-family YOLO export contains one reviewed board box per photo. Its training and validation images do not establish multi-board-in-one-frame behavior. The detector can emit multiple boxes in principle, but reliable simultaneous recognition requires scenes with several boards and a reviewed box for each board, including multi-board holdout scenes.

The dated NXP captures provide separate capture sessions of the likely same specimen. Other near-identical photo bursts and video frames must remain in their capture groups. Ultimaker has one documented dense-review photo with no explicit capture-group field: all crops/segments from it belong to one group and cannot form independent train/validation evidence.

Exact part order codes remain unresolved in many photos. Readable MCXN236V, CP2102 or Winbond family text does not confirm an ordering suffix. Source CAD/BOM mapping does not confirm the photographed revision/population. No AR calibration or 3D alignment was certified by this QA.

## Reviewed negative regions

`annotations/reviewed-component-background-regions.json` supplies eight original-pixel, hash-bound, individually inspected empty desk/wall/cloth regions. It includes NXP Oct9 and the exact ESP32/ESP12 start/end video validation frames. Only those polygons are background; no convex-hull complement or unreviewed board surface is accepted as a negative. The training mapping copy is in ignored `work/partial-component-diagnostic/background-regions.json`.

Machine-readable findings, duplicate records and per-file validation results: `annotations/dense-review-quality-audit.json`. This QA supports a documented diagnostic; it does not certify a production release.
