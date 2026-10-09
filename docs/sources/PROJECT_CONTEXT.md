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
