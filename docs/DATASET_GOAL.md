# Active dataset goal

Updated 2026-10-10 for the Tokito iQOO hackathon finale with Afnan and Navaneeth.

Build a board and component dataset for the photographed ESP32, ESP8266 ESP-12E clone, Ultimainboard 2.1.4, NXP FRDM-MCXN236 and Raspberry Pi 3B V1.2. Collect the available BOM, native board/layout files, schematics, Gerbers/manufacturing files, STEP/GLB models and relevant external datasets. Preserve source identity, revision, provenance, hashes and the limits of each reference match.

Use the 80 downloaded phone images to label every board family first, then its visible parts, then the physical pins of those parts where position and identity can be verified. Apply this order to all five board families. Link detections to supported source records and train YOLO models for the reviewed board, component and pin tasks when labels are sufficient. Publish dataset, tooling and model artifacts in the private `TokitoAI/tokito-app-dataset` repository through pull requests. Application development remains a separate later task.

## Current evidence

| Work | Status |
|---|---|
| Dataset repository and initial corpus | Published; PRs #1 and #2 merged into main |
| Phone photos | 80 files preserved: 47 captures and 33 crop variants |
| Board labels | Five families reviewed; 62 training images, 11 validation originals and 7 excluded validation crop variants |
| Board models | Experimental detector and crop classifier trained; publication to main proposed in PR #4 |
| Component labels | 204 partial major-component seeds across fifteen photos, including four validation originals; exhaustive labels and a component detector remain pending |
| Matching NXP sources | Published for review in [PR #5](https://github.com/TokitoAI/tokito-app-dataset/pull/5): CRC-verified Rev C archive with BRD, DSN/project, BOM text/XLSX and three netlist DAT files; structured extraction verified: 96 BOM items and 391 source references |
| Schematic lookup | MCXN236 PDF indexed across 13 sheets; 629 reference-like text occurrences, not BOM quantities |
| Component/source links | 10 readable photo reference labels linked to visually reviewed Rev C schematic symbols and BOM/native-part candidates; specimen revision and installed part identities unconfirmed |
| Board → part → pin hierarchy | Same rule across all five families: 80 board entries, 204 partial part boxes, four reviewed J22 photo pin boxes on Ultimainboard, 352 unregistered NXP source pin records under 10 candidate photo parts, and 1,443 separate ESP8266/Ultimainboard source pin records |
| Photo pin registration queue | Ten J12 contact boxes have provisional Rev C pad/net candidates; physical pin-1 mark and photographed revision still need checking, so no pin is promoted to training ground truth |
| Source separation | MCXN947 retained as a different-board reference; its BOM and layout are excluded from MCXN236 ground truth |
| Generated CAD references | ESP32 community clone, Ultimainboard 2.1.4 and FRDM-MCXN236 now have KiCad PCB, Gerber/drill and board-only STEP/GLB candidates; all have DRC errors and require engineering review before fabrication |
| Model readiness | Board-family experiment exists in PR #4; component labels are partial and absent from validation photos; no photo pin boxes or component/pin model yet |

## Remaining work

1. Review the verified MCXN236 source bundle and structured BOM/connectivity in PR #5, and extend the 10 supported photo-to-source candidates across the remaining visible objects. The extraction covers 391 source references (including 63 DNP and 37 NO PART TO ORDER references), 296 electrical nets and a separate NC group; these are design records, not fitted-part counts.
2. Complete part and then physical-pin annotation and review across every board family. Cover small passives, connectors, ICs, occluded/clipped objects and any available back views; partial seeds must not supply false negative regions during training. Pin numbers require checked orientation or markings before becoming photo labels.
3. Establish supported links from photo objects to matching board/revision source records. Preserve unknowns and distinguish source part numbers from identities confirmed on a physical specimen.
4. Review the generated [CAD reference exports](../data/board-sources/CAD_EXPORTS.md) before manufacturing use. The official MCXN236 ZIP has no separate Gerbers, drill files or STEP/GLB, but provisional exports now exist from its BRD. Exact ESP clone files, complete Pi BOM/layout/manufacturing files and populated 3D assemblies remain unresolved.
5. Train and evaluate the component detector after reviewed labels exist. Retain checkpoints, configurations, data lineage, predictions and failure cases.
6. Obtain independent captures/specimens for meaningful evaluation. Current board-model results use a small known-photo corpus; there is no independent specimen test and no held-out ESP32 pose group.
7. Keep the dataset and model changes reviewable in GitHub PRs, with complete artifacts in Git LFS where needed.

## Completion condition

The goal stays active until the requested collection, labeling, source-linking, training and publication work has evidence of completion. A successful board-model run or a merged dataset PR does not establish completion of component recognition or missing board files. Any unavailable source remains an explicit gap rather than being replaced silently by a different board or revision.

The built-in active objective retains the original dataset request. This tracker records the later instructions for photo labeling, YOLO training, the dataset repository and PR publication, together with current progress.
