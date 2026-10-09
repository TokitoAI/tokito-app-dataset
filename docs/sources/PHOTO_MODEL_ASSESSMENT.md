# Photo model assessment

Assessment date: 2026-10-09. This assessment reads the saved source dataset; it does not assert that the new Downloads photos are annotated or that a model is trained.

## Model outputs

Use two detection datasets: board instances in full photographs, then visible component instances in board crops. Keep document/engineering associations in a separate structured record. BOM entries, schematic pages, and Gerber layers are linked source documents, not visual component classes in phone photos.

Stable board detection IDs:

| ID | Class | Current source matching limit |
|---|---|---|
| 0 | esp32_board | 30-pin reference sources are a community clone; manufacturer/revision unconfirmed |
| 1 | esp8266_board | Photographed CH340-style clone differs from official NodeMCU reference |
| 2 | ultimainboard | Existing identification photo reads 2.1.4; verify every new specimen |
| 3 | nxp_frdm_mcxn_board | MCXN947 Rev C files available; physical suffix/revision unconfirmed |
| 4 | raspberry_pi_3b_board | Existing identification photo reads Model 3B V1.2; verify new specimens |
| 5 | other_pcb | For positively observed boards outside those families |

An ambiguous image stays in review; uncertainty is not a YOLO class. Record exact model/revision as metadata only when readable markings or geometry support it. Multiple boards in a photograph each require their own annotation.

Candidate component IDs grounded in collected source descriptions:

| ID | Class | Evidence and annotation rule |
|---|---|---|
| 0 | resistor | Ultimaker Resistor and NodeMCU SMT_R records; classify only with visible evidence or confirmed layout correspondence |
| 1 | capacitor | Ultimaker Capacitor and NodeMCU SMT_C records; visually indistinguishable passives remain unresolved |
| 2 | polarized_capacitor | Ultimaker Capacitor Polarity and NodeMCU tantalum records; separate only when evidence distinguishes it |
| 3 | diode | Ultimaker Diode and ESP32 D_Schottky records |
| 4 | led | Ultimaker LED and ESP32 LED records |
| 5 | integrated_circuit | ESP32 CP2102 and Ultimaker A4988/INA826 records; exact part number is linked metadata |
| 6 | transistor | NodeMCU S8050, ESP32 2N2222 and Ultimaker transistor/MOSFET records |
| 7 | ferrite_bead | Ultimaker Ferriet Bead records; needs matched geometry because appearance resembles passives |
| 8 | crystal_resonator | Ultimaker XTAL-3 record; classify only where visible/supportable |
| 9 | connector_header | Ultimaker HEADER and NodeMCU IO connector records |
| 10 | usb_connector | ESP32 USB_B_Micro and NodeMCU USB_Micro records |
| 11 | switch | ESP32 SW_Push and Ultimaker SW-SPDT records |
| 12 | rf_module | NodeMCU ESP_12_E record; ESP32 module identity requires image/source review |
| 13 | test_point | Ultimaker testpoint records; annotate exposed visible feature, not a hidden pad |

These are an initial schema, not declarations that each class appears in every image. Add further visually justified classes after photo review; do not collapse Pi connector types or NXP-specific parts into unsupported exact identities. No inferred bounding boxes should be treated as reviewed ground truth. There are 574 Ultimaker designators, but source testpoints/fiducials and unpopulated footprints mean this is not 574 visible populated components.

## Exact-part linking

For every detection retain `image_id`, `board_instance_id`, class, pixel box/polygon, visibility, annotation provenance, review state, and optional OCR marking. Separate `source_board_id`, `source_revision`, `component_refdes`, `part_description`, manufacturer alternatives, schematic sheet/page, nets/pins, CAD position/side, and source paths. Use nullable links and explicit `unmatched`, `reference_only`, or `verified_revision` status.

Confirm specimen model/revision first. Rectify a straight-on face using board outline/fiducials and verified dimensions. Register component positions from the matching PCB to the photograph, handle bottom-face mirroring explicitly, then visually review projected boxes. OCR of refdes/markings provides supporting evidence; it cannot independently prove a revision match. Keep original pixel coordinates alongside rectified coordinates and the transform. An enclosure STEP is not a populated-board layout.

The strongest current joins are Ultimaker's native PCB coordinates to its owner-linked schematic inventory (574 matching designators), and NXP BOM to netlist (434 matching designators, 354 nets/1470 pin connections). Ultimaker CSV X/Y are mil-valued strings, rotation/layer fields need parsed units; component centers alone do not give body boxes. NXP BRD is Allegro; PCB geometry export still needs a suitable reader. ESP32 interactive BOM/KiCad geometry is reference-only until clone matching. NodeMCU's 34 designators match its reference schematic, not the physical clone. Pi's reduced schematic and community STEP cannot establish a complete refdes/BOM map.

Gerber links identify layer and file provenance after board/revision matching. Gerber copper/mask shapes do not uniquely encode component identity, values, or manufacturer BOM. Schematics/BOM PDFs photographed among the new inputs should be routed to document/OCR extraction, not mixed into populated-board YOLO images.

## Training readiness and gaps

The five saved identification photos have no reviewed component boxes. DeepPCB's 1500 pairs/10013 boxes concern bare-PCB defects and cannot train the proposed component classes. PCB-Vision images/labels are unavailable in the saved dataset. Therefore no existing source establishes a ready component detector.

Ingest downloaded images immutably, hash/deduplicate, flag corrupt/blurred/partial files, and sort board photos versus document screenshots. Produce board boxes first, then review visible component boxes. Keep crops/rotations/near-duplicates from one original/session in one split. With only one specimen/session per board, report that validation measures that specimen/session rather than general board recognition. Never manufacture a test set by splitting nearly identical views.

Train a transfer-learning YOLO baseline only after reviewed labels exist. Evaluate board and component tasks separately, including per-class precision/recall, localization, tiny parts, occlusions, and false labels on unknown boards. A training run that finishes is not evidence that every part is correctly identified. Preserve labels, class IDs, split membership, pretrained-weight origin, config, checkpoints, and held-out predictions with the model.

Remaining dependencies: locate and inspect the new photos, confirm exact revisions, obtain/extract matching body geometry, review annotations, establish enough independent evaluation images, and run actual training/held-out evaluation. Exact Pi BOM/Gerbers, photographed ESP clone source fidelity, and NXP populated-board 3D model remain unresolved.
