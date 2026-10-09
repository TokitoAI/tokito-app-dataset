# Photo model assessment

Updated 2026-10-10 from the saved source and phone datasets. The 80 phone files now have reviewed board identities and boxes. Experimental board detector and crop-classifier training has been performed; complete component annotations and independent evaluation remain unfinished.

## Model outputs

Use board-instance detection in full photographs and a separately annotated component dataset for board crops. Keep document and engineering associations in structured records. BOM entries, schematic pages and Gerber layers are linked documents.

The current board detector has five classes:

| ID | Class | Current source matching limit |
|---|---|---|
| 0 | esp32_board | 30-pin sources are a community clone; manufacturer/revision unconfirmed |
| 1 | esp8266_board | Photographed CH340-style clone differs from official NodeMCU reference |
| 2 | ultimainboard | Phone silkscreen reads 2.1.4; source geometry still requires image registration |
| 3 | nxp_frdm_mcxn236_board | Phone silkscreen reads MCXN236; Rev C schematic and official native design archive acquired, physical PCB revision unconfirmed; MCXN947 sources incompatible |
| 4 | raspberry_pi_3b_board | Phone silkscreen reads Model 3B V1.2; reduced documents and community model do not give a complete part map |

An ambiguous image stays in review. An `other_pcb` class would require positively identified examples and a deliberate schema change; it is not part of the current trained five-class dataset. Record model/revision as metadata only when markings or geometry support it. Multiple boards in one photograph require separate annotations.

Candidate component IDs grounded in collected source descriptions:

| ID | Class | Evidence and annotation rule |
|---|---|---|
| 0 | resistor | Ultimaker Resistor and NodeMCU SMT_R records; classify only with visible evidence or confirmed layout correspondence |
| 1 | capacitor | Ultimaker Capacitor and NodeMCU SMT_C records; visually indistinguishable passives remain unresolved |
| 2 | polarized_capacitor | Ultimaker Capacitor Polarity and NodeMCU tantalum records; separate only when evidence distinguishes it |
| 3 | diode | Ultimaker Diode and ESP32 D_Schottky records |
| 4 | led | Ultimaker LED and ESP32 LED records |
| 5 | integrated_circuit | ESP32 CP2102 and Ultimaker A4988/INA826 source records; exact part number is linked metadata |
| 6 | transistor | NodeMCU S8050, ESP32 2N2222 and Ultimaker transistor/MOSFET source records |
| 7 | ferrite_bead | Ultimaker Ferriet Bead records; needs matched geometry because appearance resembles passives |
| 8 | crystal_resonator | Ultimaker XTAL-3 record; classify only where visible/supportable |
| 9 | connector_header | Ultimaker HEADER and NodeMCU IO connector records |
| 10 | usb_connector | ESP32 USB_B_Micro and NodeMCU USB_Micro records |
| 11 | switch | ESP32 SW_Push and Ultimaker SW-SPDT records |
| 12 | rf_module | NodeMCU ESP_12_E record; ESP32 module identity requires image/source review |
| 13 | test_point | Ultimaker testpoint records; annotate exposed visible feature, not a hidden pad |

This is a proposed component schema. Existing seed files use several naming conventions and are not a finalized component-training dataset. Source inventories do not declare which classes or exact part values appear in a phone image. There are 574 Ultimaker designators, including testpoints/fiducials and potentially unpopulated footprints; this is not a count of visible populated components.

## Exact-part linking

For each detection retain image and board-instance identifiers, class, pixel box/polygon, visibility, provenance, review state and optional observed marking. Store source-board identity, source revision, refdes, description, manufacturer alternatives, schematic page, nets/pins, CAD position/side and source paths separately. Distinguish an observed refdes from a candidate source link and a verified revision-specific part match.

Confirm the specimen model and PCB revision. Rectify a suitable view using board outline/fiducials and verified dimensions, register the matching PCB component positions, handle bottom-face mirroring, and visually review projected boxes. Preserve original coordinates and the transform. Component centres alone do not define body boxes; an enclosure STEP does not provide populated-board layout.

The following source relationships are available:

- Ultimaker has 574 matching designators between native PCB coordinates and the owner-linked schematic inventory. X/Y values use mil units, with separate rotation/layer fields. Photo registration and population review are still required.
- The NodeMCU reference has 34 matching PCB/schematic designators. These belong to a different USB/UART reference variant from the physical clone.
- The **MCXN947 reference** has 434 matching BOM/netlist designators, 354 nets and 1470 pin connections. These records cannot be joined to the MCXN236 phone specimen.
- MCXN236 sources now include SPF-90828 Rev C plus an eight-file official design archive: Allegro BRD, OrCAD DSN/project, .BOM text/.BOM.xlsx and connectivity DAT files. Verified extraction joins 96 BOM items / 391 designators across text BOM, XLSX, pstxprt and pstxnet. It preserves 92 primitives, 296 electrical nets / 1,243 pins, plus a separate NC group / 87 pins. The 63 DNP and 37 NO PART TO ORDER references remain explicit; total designators are not a fitted-part count. Native CAD has not been engineering-validated, and the specimen's PCB revision remains unknown.
- The MCXN236 schematic index has 629 reference-like text occurrences and 410 distinct normalized strings. BGA pin names, change history, aliases and repeated symbols can resemble refdes; these counts are not BOM quantities or populated components. 379 native references have schematic-text candidates, with symbol identity still unverified by text matching. SW3 joins to source BOM item 79, worksheet row 93 and source MPN `434123025826`, and its readable photo silkscreen links to the page-10 ISP pushbutton with model-level status. Exact specimen revision and installed manufacturer part remain unresolved.
- ESP32 interactive BOM/KiCad geometry remains reference-only until clone matching. Pi's reduced schematic and community STEP cannot establish a complete BOM/refdes map.

The user completed the official MCXN236 download on 2026-10-10 after earlier timeout/HTTP 403 attempts. The 21,418,523-byte ZIP passed CRC verification; `archive-inventory.json` records its SHA-256 and all eight members. There are no separate Gerber/drill/STEP/GLB exports in this archive. The earlier failures are acquisition history, not a current archive-access blocker.

Gerber links should identify board/revision, layer and file provenance. Copper/mask shapes do not uniquely identify component values or manufacturer BOM entries. Document screenshots should receive document/OCR processing and source attribution separately from phone-image object labels.

## Training readiness and gaps

The saved phone corpus has 80 files: 47 captures and 33 cropped variants. Board-family identities and boxes were reviewed. The YOLO board split is 62 training files and 11 validation originals; seven corresponding validation crops are excluded. Original/crop groups do not cross folds.

There is one physical specimen and one capture session per family. Four families appear in validation; all ESP32 views belong to a similar pose group retained in training. Validation measures limited variation of known specimens/sessions and cannot establish independent specimen/session accuracy or held-out ESP32 performance. Additional captures must preserve lineage and keep related views together.

Experimental board detector and crop-classifier models have been trained. Reports on the same 80 supplied files are known-photo diagnostics. The front-view geometric filter was selected after reviewing errors on those files, so its improved result is also exploratory. Preserve the ungated result and filter provenance. Model artifacts and reports are proposed through separate repository PRs.

Component seeds contain 107 major visible objects across five close-ups. Their coverage is partial; dense passives, obscured parts and board backs remain unfinished. Unlabeled regions are not verified negative training examples. Review every visible instance of the chosen classes before component training. Hidden parts cannot be claimed as visually detected.

DeepPCB's 1500 pairs and 10013 boxes concern bare-PCB defects and cannot train these component classes. PCB-Vision RGB images/labels remain unavailable in the saved collection.

Remaining work includes complete component labels, matching physical revisions and PCB geometry, photo registration, independent specimens/capture sessions, component training and separate held-out evaluation. Exact Pi BOM/Gerbers, photographed ESP clone source fidelity, MCXN236 native PCB geometry registration, separate MCXN236 manufacturing exports and complete populated-board models remain unresolved.
