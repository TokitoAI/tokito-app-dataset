# TokitoAI hackathon dataset context

Recorded 2026-10-09, Asia/Calcutta.

The user is preparing for the iQOO hackathon finale after winning Battle City. Today’s collaborators are Afnan and Navaneeth. Dataset collection comes before repository work. The final product aim will be provided later. Earlier Battle City implementation details are not available in this chat and must not be invented.

Collect board photos, schematics, BOMs, PCB source, Gerbers, STEP and GLB wherever available. Retain provenance and distinguish reference designs from exact physical-board matches. User is willing to log in to required sources. Phone-camera photographs will be added later.

## Boards from supplied photographs

| ID | Photo | Identification | Evidence and uncertainty |
|---|---|---|---|
| raspberry-pi-3b-v1.2 | 1 | Raspberry Pi 3 Model B V1.2 | Printed board marking visible; case and heatsink obscure components |
| esp8266-nodemcu-reference | 2 | ESP8266 ESP-12E NodeMCU-style board | ESP-12E and ESP8266MOD markings; wide CH340-style clone, Ver 0.1; official NodeMCU sources are reference only |
| ultimainboard-2.1.4 | 3 | Ultimaker Ultimainboard V2.1.4 | Silkscreen revision visible; confirm component population against source |
| esp32-devkit-30pin | 4 | ESP32 30-pin DevKit-style board | ESP-32 module, two 15-pin rows; manufacturer and PCB revision unconfirmed |
| nxp-frdm-mcxn947 | 5 | Likely NXP FRDM-MCXN947 | FRDM-MCXN marking and layout; exact suffix/revision needs clearer photograph |

## Collection state

manifest.csv records actual download results, file sizes, SHA-256 checksums, source URLs and source Git blob IDs. A listed reference is not proof of a physical-board match. Native Altium files require a compatible viewer/editor for engineering inspection; they have not yet been opened or converted.

- Ultimaker: revision-matched native source located at https://github.com/Ultimaker/Ultimaker2/tree/master/1546%20ultimainboard%20V2.1.4 . PCB and schematic sheets; no exact-revision BOM, Gerber or board STEP/GLB verified yet.
- ESP8266: https://github.com/nodemcu/nodemcu-devkit-v1.0 supplies native PCB/schematics, schematic PDF and four RAR Gerber archives. Physical photo shows a clone, so these cannot serve as exact ground truth without layout comparison. RAR contents remain to be inspected.
- ESP32: https://github.com/playelek/pinout-doit-32devkitv1 supplies a community pinout reference. Exact PCB, schematic, BOM and 3D model remain unresolved.
- Raspberry Pi: https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-reduced-schematics.pdf and https://datasheets.raspberrypi.com/rpi3/raspberry-pi-3-b-mechanical-drawing.pdf . Reduced schematic only; full BOM/PCB/Gerbers have not been found. Board STEP/GLB remain unresolved.
- NXP: https://www.nxp.com/webapp/Download?colCode=FRDM-MCXN947-DESIGN-FILES and https://www.nxp.com/webapp/Download?colCode=90818-MCXN947SH redirect to NXP login. User login/download needed. Community enclosure STEP archive is an enclosure, not a board model.

## Next collection work

Inspect and unpack acquired archives; import the NXP download; locate exact ESP clone sources; investigate board 3D models and existing PCB vision datasets; extract BOMs and structured reference-designator/net information only from verified sources; generate derived formats with explicit derivation labels when practical. Preserve original licensing and check redistribution permission before publishing a shared dataset.

## NXP acquisition update
2026-10-09: Browser download succeeded without a credential prompt. Official Rev C archive downloaded and extracted. Contains Allegro LAY_90818_C.brd, OrCAD schematic DSN/project, BOM XLSX, connectivity files, Gerber ART layers, NC drill/route and fabrication/assembly PDFs. Physical board revision remains unverified. No board STEP/GLB is present in this archive. Earlier login/download-needed entry is superseded by this acquisition.

## Structured NXP data
Official-source Rev C connectivity extracted into structured-rev-c/netlist.json and net-pins.csv: 354 nets, 1470 pin connections. Raw BOM sheet exported as CSV: 315 rows, 19 columns including report metadata. These are sheet dimensions, not component counts. BOM contains Item Revision A1 metadata; do not equate that with PCB Rev C. Original workbook remains intact. No physical specimen labels have been inferred. NodeMCU RAR extraction is partial and explicitly marked incomplete. file-inventory.csv records hashes for currently saved dataset files.

## NXP schematic verification
The downloaded Rev C archive already contains PDF/spf-90818_c.pdf: 13 pages, verified title FRDM-MCXN947, document SCH-90818 / SPF-90818, Rev C dated March 28, 2024. Page text and source hash indexed in structured-rev-c/schematic-index.json. Separate browser schematic download timed out, but does not leave a content gap. PDF carries NXP proprietary-use restrictions; redistribution permission is unestablished.

## Additional reference assets
Ultimaker official repository Ultimaker/Ultimaker2Go contains 1546/1546-A.STEP, downloaded intact at 29,997,472 bytes; source tree pinned in official-3d/provenance.json. Assembly-model geometry and physical revision comparison pending. ESP32 community clone interactive BOM decoded to structured/interactive-bom-data.json and bom-components.csv: 24 BOM component entries, 26 footprints, 2 explicitly skipped. Reference clone only, not physical board labels. CAD runtime installation succeeded; two GLB conversion sessions were launched.

NodeMCU solid-RAR limitation resolved using workspace library node-unrar-js. All 62 archive files extracted and size/member-count checked; see gerbers-verified/extraction-report.json. Ultimaker part 1546 GLB conversion completed and reopened successfully with matching bounds. Exact physical-board match not yet established.

## Raspberry Pi and auxiliary data update
Community cluster STEP obtained from FSkavlem/CAD_Raspberrypi_cluster at pinned tree. Named RPi3_ModelB v1 subassembly extracted to standalone reference STEP, converted to GLB and reloaded with matching bounds. Extents 86.091 x 18.740 x 56.135 mm in inherited coordinate orientation. Exact physical model and licensing comparison remain open. DeepPCB source-complete.zip download completed and passed all ZIP CRC checks. Raw repository has 1503 test images and 1504 template images; official split lists are authoritative for usable benchmark samples. Do not use the timed-out source.zip.

## Ultimaker native PCB extraction
Parsed 574 component property records and 252 net-name records from official Ultimaker_V2.1.4.PcbDoc; extracted 61 embedded STEP models by decompressing native model streams. Source hash and model hashes retained in structured-source/extraction.json. Component inventory preserves source description/designator/footprint/coordinates; do not treat it as a verified procurement BOM or physical population labels. PCBVision official Zenodo metadata collected: 11,392,398,155-byte archive, CC BY 4.0 dataset license. Range-based archive inspection encountered gateway timeout; full dataset download remains pending.

## NodeMCU reference extraction and PCBVision range access
Parsed official NodeMCU reference PCB: 34 component records, 41 net records, 17 embedded STEP component models. These are not a model of the photographed CH340 clone. PCBVision archive central directory retrieved successfully through cached range requests; RGB-directory contents total approximately 20.5 MB compressed. Selective RGB and label acquisition is active; hyperspectral acquisition is separate. COVERAGE.md rewritten to reflect current state and remove superseded pending statements.

## Native schematic records
Extracted 14155 FileHeader records from 13 Altium schematic sheets (Ultimaker and NodeMCU reference). JSON preserves field names and stream record indexes. Schematic component inventories join owner-linked designators and parameters, with unmatched-owner diagnostics retained. No physical-board labels or procurement assertions added. PCBVision mirror full-file download stalled on a read timeout and is terminal; no acquisition process remains running.

## NXP normalized BOM
Grouped manufacturer alternatives into 108 part groups (278 manufacturer rows), 434 distinct reference designators; source BOM and source netlist refdes sets match exactly, with no quantity conflicts or duplicated refdes groups. bom-parts.json preserves alternatives and CSV row numbers. Remaining verified source leads recorded separately; paid model not purchased and not assumed to match.

## 2026-10-10 board identity, photos and repository context

Readable phone silkscreen confirms **FRDM-MCXN236**, superseding the earlier MCXN947 hypothesis. Earlier NXP archive, BOM, connectivity and enclosure entries in this history describe MCXN947 only. They remain a different-board reference and cannot establish labels for the photographed MCXN236. Ultimainboard 2.1.4 and Raspberry Pi 3B V1.2 markings are also confirmed; ESP clone manufacturers/revisions and the MCXN236 physical PCB revision remain unresolved.

The MCXN236 SPF-90828 Rev C schematic is preserved: 13 sheets, SCH-90828 / SPF-90828, drawing date 2024-03-25, copied unchanged from Downloads with its earlier download provenance unknown. The matching design ZIP is still unavailable. On 2026-10-10 the official download page was reached, the browser download timed out after 45 seconds, and curl against the observed official cache URL returned HTTP 403 and zero bytes. Matching BOM, BRD, Gerbers and populated-board models remain missing.

The dataset now includes 80 phone files (47 captures and 33 cropped variants), reviewed board identities/boxes, and 107 partial major-component seed boxes across five close-ups. The board detector split contains 62 training images, 11 validation originals and seven excluded validation crops; original/crop groups do not cross folds. There is one specimen/session per family and no independent ESP32 validation pose. Experimental YOLO board detector and crop-classifier training has completed. Known-photo diagnostics, including a front-view filter selected after inspecting errors, do not establish independent generalization. Complete component labels, exact source registration and a trained every-component detector remain unfinished.

The private [TokitoAI/tokito-app-dataset](https://github.com/TokitoAI/tokito-app-dataset) repository is shared for the hackathon work with Afnan and Navaneeth. Dataset/model changes go through PRs. GitHub state read on 2026-10-10 shows [PR #2](https://github.com/TokitoAI/tokito-app-dataset/pull/2) merged into main with the corpus, [PR #3](https://github.com/TokitoAI/tokito-app-dataset/pull/3) merged into the dataset branch, and [PR #4](https://github.com/TokitoAI/tokito-app-dataset/pull/4) open to publish the experimental model results on main. Repository sharing does not establish broader rights to third-party source assets. COVERAGE.md and board-specific provenance record current scope; the preceding entries retain acquisition history.

## 2026-10-10 MCXN236 official archive acquired

The user completed the official MCXN236 design-file download after the failed browser/curl attempts above. The 21,418,523-byte archive was ingested with a passing ZIP CRC check; SHA-256 is `e1ee1755a9cc2c1efa27ceb25cc459d7e55f0626f4ee3037199183ee45482ff2`. The archive inventory records eight actual files: LAY-90828_C.brd, SCH-90828_C.DSN/.opj/.BOM/.BOM.xlsx, and allegro/pstchip.dat/pstxnet.dat/pstxprt.dat. This successful acquisition supersedes the earlier entry saying the design ZIP and native BOM/BRD sources were unavailable.

No separate Gerber, drill, STEP or GLB exports occur in this archive. At acquisition, structured BOM/netlist records had not yet been extracted; the completion entry below supersedes that status. The native files have not been engineering-validated in their authoring tools, and the photographed PCB revision remains unknown. Original files and provenance are preserved; acquisition does not establish broader rights or physical-part equivalence.

The separate SPF-90828 schematic index now has 629 reference-like occurrences and 410 distinct normalized strings. BGA pin names, change history, aliases and repeated symbols create ambiguity; these are not BOM quantities or verified component counts. The readable photo SW3 is linked to the ISP pushbutton on schematic page 10 as a model-level source candidate, with exact specimen revision and installed manufacturer part still unresolved.

## 2026-10-10 MCXN236 structured extraction completed

Verified structured records now contain 96 source BOM items / 391 reference designators, with identical reference sets across text BOM, XLSX, pstxprt and pstxnet. They preserve 92 primitives, 296 electrical nets / 1,243 pin records, and a separate literal NC group / 87 pin records. The source marks 63 references DNP and 37 NO PART TO ORDER; these totals do not describe fitted parts. Source provenance and comparisons are recorded in structured-rev-c/README.md and extraction-report.json.

379 native references have ambiguous schematic-text candidates. SW3 joins to source BOM item 79, worksheet row 93, MPN `434123025826`, and the page-10 ISP schematic switch. This identifies the Rev C source part; the photo link remains model-level because physical PCB revision and exact installed part are unknown. Native CAD engineering review, photo registration and separate Gerber/drill/STEP/GLB exports remain outstanding.
