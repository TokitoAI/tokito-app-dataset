# Active dataset goal

Today's implementation priority is ESP32, ESP-12E, Ultimainboard 2.1.4 and NXP.
Raspberry Pi work is deferred at the user's request, with its data retained.
Inspect and improve the Antigravity ESP32/Ultimaker geometry before continuing
NXP model work. The full multi-view AR objective remains unchanged; today's
completion target is not evidence of readiness. See
[Antigravity intake review](ANTIGRAVITY_3D_INTAKE_REVIEW.md).

Updated 2026-10-10 for the Tokito iQOO hackathon finale with Afnan and Navaneeth.

Build a board and component dataset for the photographed ESP32, ESP8266 ESP-12E clone, Ultimainboard 2.1.4, NXP FRDM-MCXN236 and Raspberry Pi 3B V1.2. Collect the available BOM, native board/layout files, schematics, Gerbers/manufacturing files, STEP/GLB models and relevant external datasets. Preserve source identity, revision, provenance, hashes and the limits of each reference match.

Use the 80 downloaded phone images to label every board family first, then its visible parts, then the physical pins of those parts where position and identity can be verified. Apply this order to all five board families. Link detections to supported source records and train YOLO models for the reviewed board, component and pin tasks when labels are sufficient. Publish dataset, tooling and model artifacts in the private `TokitoAI/tokito-app-dataset` repository through pull requests. Application development remains a separate later task.

## Current evidence

Latest follow-up (2026-10-10): four initial iQOO videos covering ESP32,
ESP-12E, Ultimainboard and NXP have been hash-verified and preserved. Two later
clips add underside views and visible flip motion for ESP32 and Ultimainboard;
their source hashes and review sheets are recorded in the
[supplemental flip-clip manifest](../data/video-captures/2026-10-10/physical-view-followup/additional-flip-clips/manifest.json).
Later clips add NXP component-face and underside views as separate short
recordings, plus another Ultimaker underside sequence. Their hashes and
per-board view claims are in the
[additional board views manifest](../data/video-captures/2026-10-10/physical-view-followup/additional-board-views/manifest.json).
Four distinct oblique sides are not verified for any board, and a dedicated
ESP-12E view/flip capture is still missing. No complete real six-view specimen
or calibrated continuous-flip evaluation is established.
ESP32 now has a reviewed partial macro seed with 19 visible body masks and 12
literal printed-contact centers. U2's same-specimen photo supports the visible
family marking `SILABS / CP2102`; the full order suffix remains unreadable.
Camera2 factory intrinsics for the connected iQOO and an explicit crop/resize/
rotation transform are recorded, but independent optical and physical pose
validation remain false. The YOLO trainer now verifies that the actual YAML
loader selects the exact reviewed images and labels. No exhaustive component
export or final model is available.

The updated end goal is calibrated, multi-view AR with independent component
selection: reviewed board boundaries and semantic metric anchors, visible
component masks, source/refdes/pin links and per-component 3D mesh selectors.
The same physical component and fixed board frame must persist through
rotation and flipping. Each specimen needs top/underside and four oblique side
views plus physical flip-sequence evaluation. Apply this to all five families;
the NXP implementation below is the first source-linked path, not completion
of the full cross-board goal. See [AR alignment dataset](AR_ALIGNMENT_DATASET.md).

The 2026-10-11 segmentation audit consolidates eight existing annotation
sources into a per-frame review queue: 424 source mask records, 398 unique
image/instance pairs across 14 frames, and zero frames with verified complete
visible-instance coverage for ordinary YOLO segmentation training. The queue
is `data/photo-model/component-review-backlog.json`; the public-source/license
review is [PUBLIC_COMPONENT_DATASET_AUDIT_2026-10-11.md](PUBLIC_COMPONENT_DATASET_AUDIT_2026-10-11.md).
Partial frames can still support the ignore-aware diagnostic trainer, but do
not count as an exhaustive component dataset or valid independent evaluation.

| Work | Status |
|---|---|
| Dataset repository and initial corpus | Published; PRs #1 and #2 merged into main |
| AR identity/geometry joins | 243 partial part boxes, one reviewed U1 body polygon, four named NXP mounting-hole image/metric pairs and 11 revision-unverified image-to-mesh candidates. The released NXP GLB has 354 independently selectable source component meshes; this does not establish 354 photographed matches |
| Multi-view coverage | Six source-CAD views generated with depth-tested instance masks and fixed component IDs. Real underside video views now exist for ESP32, Ultimainboard and NXP, but four distinct oblique sides remain unverified and no complete real six-view specimen or calibrated physical flip evaluation is verified. Synthetic views cannot replace real-camera evaluation |
| Phone photos | 80 files preserved: 47 captures and 33 crop variants |
| Board labels | Five families reviewed; 62 training images, 11 validation originals and 7 excluded validation crop variants |
| Board models | YOLO11m baseline plus a dynamic medium-model fine-tune; 1,000-epoch ceiling, 100-patience stop at epoch 113, best epoch 13. Confidence-integrated candidate mAP50-95 is 0.9417 versus 0.9186 baseline on the 11-image known-specimen fold; a fixed 0.75-confidence audit found one fine-tune false positive versus zero for the baseline. ESP32 is missing from validation. The matching LiteRT export passed numerical conformance; the iQOO I2501 camera smoke detected Ultimainboard correctly once, missed it twice, and once mislabeled it as ESP8266 at 0.9405 confidence. Parts remain generic `ic` labels. |
| Component labels | 240 partial part boxes across nineteen photos, including four validation originals; exhaustive labels and a component detector remain pending |
| Matching NXP sources | Merged in [PR #5](https://github.com/TokitoAI/tokito-app-dataset/pull/5): CRC-verified Rev C archive with BRD, DSN/project, BOM text/XLSX and three netlist DAT files; structured extraction verified: 96 BOM items and 391 source references |
| Raspberry Pi source files | Official Pi 3 Model B mechanical DXF added with source URL, SHA-256, entity/layer inventory and LFS tracking; it is mechanical geometry, not an electrical PCB project or Gerber set |
| Schematic lookup | MCXN236 PDF indexed across 13 sheets; 629 reference-like text occurrences, not BOM quantities |
| Component/source links | 10 readable photo reference labels linked to visually reviewed Rev C schematic symbols and BOM/native-part candidates; specimen revision and installed part identities unconfirmed |
| Board → part → pin hierarchy | Same rule across all five families: 80 board entries, 240 partial part boxes, 62 numbered source-linked photo pins (22 Ultimainboard, 40 Pi J8) and 103 ESP contacts with printed aliases across four photos. The 352 NXP source pin records remain unregistered; 22 of the 1,443 ESP8266/Ultimainboard reference records now join photo pins |
| Photo pin registration queue | Ten NXP J12 contact boxes remain proposals after all 18 available front photos were reviewed; its pin-1 mark and physical board revision are unreadable. ESP32 has 45 and ESP8266 has 58 printed contact aliases across repeat photos; numeric pin numbers and source nets remain unknown |
| External component images | PCB-Vision's 53 RGB photographs and 106 segmentation masks are verified and packaged with attribution in Git LFS. A separate manifest contains 2,384 unreviewed box proposals for three external component classes. A 20-epoch YOLO11n smoke run is published with board-disjoint test mAP50-95 0.0419; connector mAP50-95 is 0.0, so this is failure evidence and a phone-runtime test artifact rather than a finished parts model |
| Source separation | MCXN947 retained as a different-board reference; its BOM and layout are excluded from MCXN236 ground truth |
| Generated CAD references | ESP32 community clone, Ultimainboard 2.1.4 and FRDM-MCXN236 now have KiCad PCB, Gerber/drill and board-only STEP/GLB candidates; all have DRC errors and require engineering review before fabrication |
| Model readiness | The YOLO11m fine-tune is a board-only evaluation candidate, not an independently validated release model. It improves confidence-integrated mAP50-95 on four represented classes, but fixed-threshold review found one false positive at uniform confidence 0.75; the baseline had none. A Pi-specific cutoff removes it only on the same fold. Its matching LiteRT export passed numerical conformance and ran in the iQOO I2501 camera smoke app; the component detector still emitted generic `ic` labels. The external PCBVision candidate-box model's low held-out scores do not qualify it as the Tokito component model. All 240 part boxes and 165 pin/contact boxes remain partial seeds; reviewed component and pin models remain pending |

## Remaining work

1. Extend the 10 supported MCXN236 photo-to-source candidates across the remaining visible objects. The verified source bundle and structured BOM/connectivity were merged in PR #5. The extraction covers 391 source references (including 63 DNP and 37 NO PART TO ORDER references), 296 electrical nets and a separate NC group; these are design records, not fitted-part counts.
2. Complete part and then physical-pin annotation and review across every board family. Cover small passives, connectors, ICs, occluded/clipped objects and any available back views; partial seeds must not supply false negative regions during training. Pin numbers require checked orientation or markings before becoming photo labels.
3. Establish supported links from photo objects to matching board/revision source records. Preserve unknowns and distinguish source part numbers from identities confirmed on a physical specimen.
4. Review the generated [CAD reference exports](../data/board-sources/CAD_EXPORTS.md) before manufacturing use. The official MCXN236 ZIP has no separate Gerbers, drill files or STEP/GLB, but provisional exports now exist from its BRD. Exact ESP clone files, complete Pi BOM/layout/manufacturing files and populated 3D assemblies remain unresolved.
5. Replace the external candidate-box smoke model with a detector trained from reviewed, exhaustive Tokito component labels. Retain checkpoints, configurations, data lineage, predictions and failure cases, including the current connector failure.
6. Obtain independent captures/specimens for meaningful evaluation. Current board-model results use a small known-photo corpus; there is no independent specimen test and no held-out ESP32 pose group.
7. Keep the dataset and model changes reviewable in GitHub PRs, with complete artifacts in Git LFS where needed.

## Completion condition

The goal stays active until the requested collection, labeling, source-linking, training and publication work has evidence of completion. A successful board-model run or a merged dataset PR does not establish completion of component recognition or missing board files. Any unavailable source remains an explicit gap rather than being replaced silently by a different board or revision.

The built-in active objective retains the original dataset request. This tracker records the later instructions for photo labeling, YOLO training, the dataset repository and PR publication, together with current progress.
