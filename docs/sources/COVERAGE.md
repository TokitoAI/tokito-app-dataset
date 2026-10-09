# Dataset coverage

Updated 2026-10-10. Collected sources and derived files are preserved separately. The photographed NXP board is **FRDM-MCXN236**. The previously collected MCXN947 package belongs to a different board and cannot supply its component, BOM or manufacturing labels.

| Board | Schematic | BOM / component inventory | PCB source | Manufacturing files | STEP and GLB |
|---|---|---|---|---|---|
| NXP FRDM-MCXN236 (photographed board; PCB revision unconfirmed) | SPF-90828 Rev C PDF plus official SCH-90828_C.DSN/project | 96 source BOM items / 391 designators; text/XLSX/native reference sets agree | Official LAY-90828_C.brd and Allegro connectivity DAT files; provisional KiCad import | Generated Gerber/drill references; none separately supplied in official archive; DRC errors remain | Generated board-only STEP/GLB; complete populated-board model not located |
| NXP FRDM-MCXN947 (incompatible reference) | Official Rev C DSN and 13-page PDF | Official XLSX, extracted CSV | Official Allegro BRD | Official Gerber ART, drill, route, fabrication PDFs | Enclosure STEP only; no complete board model |
| Ultimainboard 2.1.4 | Official Altium sheets | 574 PCB component records; procurement BOM not verified | Official PcbDoc; 252 net records; provisional KiCad import | Generated Gerber/drill references with DRC errors; engineering review pending | Official part 1546 STEP and derived GLB; 61 embedded component STEP models; generated board-only STEP/GLB |
| ESP32 30-pin | Community clone KiCad/PDF reference | 24 reference BOM entries, JSON/CSV | Reference KiCad PCB | Generated clone-reference Gerber/drill files with DRC errors; exact specimen match unresolved | Community STEP and verified derived GLB; generated board-only STEP/GLB |
| ESP8266 ESP-12E clone | Official NodeMCU reference Altium/PDF | 34 reference PCB component records, JSON/CSV | Reference PcbDoc; 41 net records | Four reference archives fully unpacked: 62 verified files | 17 embedded component STEP models; complete photographed-clone board model not located |
| Raspberry Pi 3B V1.2 | Official reduced schematic PDF | Complete procurement BOM not located | Native board layout not located | Gerbers not located | Community assembly submodel extracted as STEP and converted to GLB |

## MCXN236 acquisition

The preserved `nxp-frdm-mcxn236/SPF-90828.pdf` identifies FRDM-MCXN236, SCH-90828 / SPF-90828, Rev C, 13 sheets, dated 2024-03-25. It was copied unchanged from Downloads; its earlier download provenance is unknown. Its title and revision match the manufacturer's listing. A matching schematic model does not establish the physical specimen's PCB revision.

On 2026-10-10 the user completed the official design-file download. The 21,418,523-byte ZIP passed CRC verification and all eight files were ingested: LAY-90828_C.brd, SCH-90828_C.DSN/.opj/.BOM/.BOM.xlsx, and allegro/pstchip.dat/pstxnet.dat/pstxprt.dat. Archive SHA-256: `e1ee1755a9cc2c1efa27ceb25cc459d7e55f0626f4ee3037199183ee45482ff2`. `archive-inventory.json` records each file's size and hash. Earlier browser timeouts and HTTP 403/zero-byte responses remain acquisition history in PROVENANCE.md.

The actual eight archive members include no separately exported Gerbers, drill, STEP or GLB files, despite the broader download-page description. Structured extraction is complete: 96 BOM items expand to 391 reference designators, with identical reference sets in text BOM, XLSX, pstxprt and pstxnet. There are 92 primitives, 296 electrical nets with 1,243 pin records, and a separate literal NC group with 87 pins. The source marks 63 references DNP and 37 NO PART TO ORDER; 391 is not a fitted-part or procurement count. See `structured-rev-c/README.md` and `extraction-report.json`. Native CAD has not been engineering-validated in its authoring tools, and the physical PCB revision remains unconfirmed.

The schematic text index contains 629 reference-like occurrences and 410 distinct normalized strings. BGA pin names, change history, aliases and repeated symbols can resemble refdes, so these are not component or BOM counts. 379 native references have schematic-text candidates, which retain that ambiguity. The photographed SW3 has a model-level link to the ISP pushbutton on schematic page 10 and source BOM item 79, worksheet row 93, MPN `434123025826`. This identifies the Rev C design record; exact installed-part and specimen-revision mapping remain unverified.

## Images, labels and models

Five original identification photographs are preserved, plus the 80 phone files collected from Downloads: 47 captures and 33 cropped variants. The phone corpus contains 12 ESP32, 14 ESP8266, 18 Ultimainboard, 18 FRDM-MCXN236 and 18 Raspberry Pi 3B files. Board-family identities and boxes were reviewed from the photos.

The board detector split contains 62 training images and 11 validation originals; seven corresponding validation crop variants are excluded. Original/crop groups do not cross folds. There is one physical specimen and one capture session per family. ESP32 has no separate validation pose group. This split cannot establish performance on new specimens, sessions or unseen ESP32 poses.

Component seeds contain 240 visible part boxes across nineteen photos. They are partial and require further box review and exhaustive labeling of the intended classes before component-detector training. Tiny passives, obscured parts and board backs remain incomplete. Source records and model-level candidate links do not establish exact populated-part identity.

All five families follow board → visible part → physical contact/pin. There are 165 reviewed photo contact boxes: 22 numbered Ultimainboard contacts on J22/J23/J1/J2, 40 numbered Raspberry Pi J8 contacts linked to its revision 1.2 reduced schematic, and 103 ESP contacts carrying their photographed printed aliases (45 ESP32, 58 ESP8266 across repeat views). The ESP aliases have no assigned physical pin number, source refdes or net. NXP J12 remains a photo/source candidate because the specimen revision and physical pin 1 are unreadable. These are partial contact labels and are not eligible as complete pin-detector training ground truth. See [Ultimainboard pin evidence](../ULTIMAINBOARD_PIN_EXPANSION.md), [Pi J8 evidence](../PI_J8_PIN_LABELS.md) and [ESP alias evidence](../ESP_ADDITIONAL_CONTACTS.md).

Experimental YOLO board detector and crop-classifier training has been performed. Reported predictions on the same 80 known photos are diagnostics, including a front-view geometric filter chosen after inspecting errors; they are not independent accuracy measurements. No complete component detector or exact BOM/refdes/Gerber inference is established. Model artifacts are handled through separate repository PRs.

## Auxiliary datasets and source joins

DeepPCB: the full local original download passed ZIP CRC checks. Official splits contain 1000 trainval and 500 test pairs. All referenced local image/template/annotation paths exist, splits do not overlap, and all 10013 defect boxes have valid bounds and class IDs. MIT source license is retained. These are bare-PCB copper-defect examples. The repository includes metadata/audits; bulk auxiliary images are retained in the local collection.

PCB-Vision: all 53 RGB photos and 106 masks (53 General, 53 Monoseg) are acquired from the official Zenodo archive. All 159 files pass source-member CRC, byte-count, SHA-256 and image decoding checks; all 106 mask/photo pairs match dimensions. [rgb-subset.zip](../../data/external/PCBVision/rgb-subset.zip) packages the files with CC BY 4.0 attribution through Git LFS, and its member hashes/CRCs match the acquired manifest. A [separate manifest](../PCB_VISION_BOX_CANDIDATES.md) records 2,384 connected-region box proposals for ICs, capacitors and connectors. These require instance review and are not labels for our board identities, refdes or pins. HSI and the full upstream archive checksum remain unverified. See [acquisition and package evidence](../PCB_VISION_RGB_ACQUISITION.md).

Ultimaker and NodeMCU schematic inventories include owner-linked designators and component parameters. All 574 Ultimaker and 34 NodeMCU designators match their corresponding native PCB inventories. This establishes source-document consistency. Photo-to-PCB registration and physical population checks remain necessary; the NodeMCU source is a different clone variant.

## Verification and limits

ESP32, Ultimaker and Pi GLBs reopen successfully, contain finite geometry, and preserve tessellated STEP bounds after converting millimetres to metres. Original coordinate offsets are retained; materials and source colours are not. These checks do not prove a physical specimen match.

Separate generated KiCad references now exist for the ESP32 community clone, Ultimainboard 2.1.4 and FRDM-MCXN236 Rev C: PCB files, Gerbers, Excellon drill files and board-only STEP/GLB. Imported refdes sets match 574/574 Ultimainboard source references and 391/391 NXP BOM references. DRC reports contain 19/128, 293/569 and 1,087/315 errors/warnings respectively. The imports also retain zero-sized-pad and NXP padstack warnings. These checks preserve provisional reference geometry, not fabrication approval or complete populated 3D assemblies. See [CAD export provenance](../../data/board-sources/CAD_EXPORTS.md).

The **MCXN947 reference** connectivity extraction contains 354 nets and 1470 pin connections. Its manufacturer BOM is normalized into 108 part groups, 278 manufacturer-alternative rows and 434 distinct reference designators. BOM and netlist designator sets match; no duplicate groups or alternative-quantity conflicts were found. Its PCB Rev C and BOM Item Revision A1 are separate metadata. None of these counts or records describes the photographed MCXN236.

NXP source PDFs retain proprietary-use notices; public redistribution permission is unestablished. ESP clone geometry/revision, MCXN236 physical revision and broader photo-to-PCB registration, remaining exact-board models, missing Pi manufacturing/BOM/layout files, engineering review of generated manufacturing exports, community-model licensing, complete component/pin annotations and independent phone captures remain open. Native source files have not been engineering-validated in their original CAD tools.

Initial timed-out DeepPCB source.zip and partial NodeMCU gerbers-extracted files are excluded from usable local data. Use DeepPCB/source-complete.zip and NodeMCU/gerbers-verified instead. PROJECT_CONTEXT.md preserves acquisition history; this coverage document records the current board identities.
