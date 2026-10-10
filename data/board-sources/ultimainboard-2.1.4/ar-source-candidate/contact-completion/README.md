# Ultimaker source geometry candidate

This directory is isolated work output, not a production release. The candidate retains the entire previously reviewed source mesh graph and binary buffer, then adds independently selectable source contact surface proxies and two approximate package envelopes plus two detailed matching package KiCad STEP models.

Coverage: 310 existing source body references + 252 test contacts + 3 fiducials + JP2 + J34/U9 library packages plus K1/L2 envelopes = 570 distinct reference selectors. Only four mechanical spacers SP1–SP4 remain without geometry. Each reference has independent nodes and meshes; validation checks preservation of every original mesh/material/accessor/buffer view and all original binary bytes.

`source-pad-inventory.json` was extracted from the native imported PCB with KiCad 10.0.7 pcbnew. It records all 574 footprints and 1,322 pads, including numbered pad centres, shapes, dimensions, drills, layer membership, orientations and source PCB SHA-256.

The source exporter centres PCB X/Y at [148.5011, 105.003595] mm. glTF units are metres; glTF X follows PCB X, glTF Z follows PCB Y, and glTF Y is thickness/height. Pad proxies sit at Y=1.72mm or -0.13mm to avoid coincident copper surfaces. These are selection overlays, not measured copper thickness. The source model surface thickness is 1.58mm whereas imported stackup metadata says 1.74mm; this discrepancy is unresolved.

The K1/L2 package envelopes are clearly approximate and MUST NOT be promoted to manufacturer-verified final geometry. J34 and U9 use matching KiCad 10.0.7 library STEP geometry; their library hashes and corrective transforms are recorded in library-model-provenance.json. Exact library STEP inputs are included under library-models. Source pad placement and source component values are preserved, but relay/inductor heights and envelope extents are assumptions. All source population remains unverified against the photographed specimen. Photo registration, camera calibration and physical board flipping have not been tested.

Scripts here reproduce inventory extraction, candidate assembly, preservation/ownership validation and triangle-surface review. The renderer ignores source line/point primitives only for preview; the candidate GLB preserves them.


source-contact-targets.json additionally records 1,322 uniquely identified source copper-land centres, numbered-pad relationships and GLB parent selectors in the metric export frame. These are source geometry targets only: copper-land centres must not be substituted for observed solder joints, hole rims or visible leads without feature-specific review. Electrical net functions are not extracted. Every contact remains excluded from training until photographed correspondence and visibility are reviewed.
