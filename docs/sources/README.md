# Tokito board dataset

Collection for the iQOO hackathon finale, with Afnan and Navaneeth. The private dataset repository is [TokitoAI/tokito-app-dataset](https://github.com/TokitoAI/tokito-app-dataset), with dataset and model changes proposed through pull requests. The final application aim will be supplied later.

Start with COVERAGE.md for current coverage and gaps. PROJECT_CONTEXT.md preserves acquisition history, including the superseded MCXN947 identity hypothesis. PHOTO_CAPTURE.md remains the protocol for additional independent phone captures.

## Files for data work

In the repository, native documents and derived source records are under `data/board-sources`, the phone corpus and reviewed board labels are under `data/photo-model`, and these notes are under `docs/sources`. The local acquisition collection is `outputs/board-dataset`.

- The local collection's asset-catalog.json, file-inventory.csv, manifest.csv and dataset-audit.json retain acquisition records, hashes and prior audit results. They are historical snapshots, not proof of a current physical-board match or complete coverage of later additions. Read each board's provenance alongside them.
- The repository's import-summary.json records imported paths and sizes. Board annotations record phone-image hashes, identities, reviewed boxes and split membership; the acquisition photo-manifest.json retains its original ingest state.
- LICENSE_NOTES.md and file-specific notices preserve observed source terms.
- Board folders contain original photographs, native files and structured/derived records where available.
- The local auxiliary/DeepPCB collection contains the 1500-pair defect dataset. Repository data/external preserves metadata/audits; bulk auxiliary images are not included there.
- PCB-Vision's complete RGB subset is packaged in `data/external/PCBVision/rgb-subset.zip` through Git LFS: 53 photos plus 106 masks, all verified against source-member CRCs and recorded hashes. Attribution and CC BY 4.0 licensing accompany the data; HSI is excluded. See [acquisition documentation](../PCB_VISION_RGB_ACQUISITION.md).
- ESP32 community-clone, Ultimainboard 2.1.4 and FRDM-MCXN236 folders include generated KiCad PCB, Gerber/drill and board-only STEP/GLB references. DRC errors remain; [CAD_EXPORTS.md](../../data/board-sources/CAD_EXPORTS.md) records engineering-review limits.

## Board matching and photos

The phone photos identify FRDM-MCXN236, Ultimainboard 2.1.4 and Raspberry Pi 3B V1.2. The MCXN236 PCB revision and ESP board manufacturers/revisions still require confirmation. MCXN947 files remain an incompatible reference and must not be used as the photographed NXP board's BOM, PCB or schematic.

MCXN236 sources now include the preserved 13-page SPF-90828 Rev C schematic and the official design ZIP downloaded by the user on 2026-10-10. The ZIP passed CRC verification; its eight files include native Allegro BRD, OrCAD DSN/project, .BOM text/.BOM.xlsx and three connectivity DAT files. `archive-inventory.json` records hashes and member details. The earlier timeout/HTTP 403 attempts are retained as history in PROVENANCE.md.

The official archive contains no separate Gerber, drill, STEP or GLB exports. Provisional files in these formats have since been generated from its BRD through KiCad, with 1,087 DRC errors and 315 warnings; the 3D outputs contain only the board body. Verified structured extraction joins 96 source BOM items to 391 designators; text BOM, XLSX and native part/netlist reference sets agree. It preserves 92 primitives, 296 electrical nets / 1,243 pin records, and a separate NC group / 87 pins. The 63 DNP references and 37 NO PART TO ORDER references remain explicit; the total is not a fitted-part count. See `structured-rev-c/README.md` and `extraction-report.json`. Native CAD has not been engineering-validated, and the physical PCB revision is still unknown. The separate schematic's earlier local download provenance remains unknown.

The schematic index provides 629 reference-like text occurrences across 410 normalized strings, with explicit ambiguity for BGA pin names, history and repeated symbols. These are search entries, not BOM/component counts. 379 native references have schematic-text candidates. SW3 links to the page-10 ISP switch and source BOM item 79, row 93, MPN `434123025826`; its photo association remains model-level, with exact installed-part identity unresolved.

The corpus includes five original identification photos and 80 phone files (47 captures and 33 cropped variants). Board identities and boxes were reviewed. Component seeds cover 236 major visible objects across nineteen photos and remain incomplete. Exact part links require readable markings or reviewed registration to the correct PCB revision.

All board families use board → part → contact/pin labels. The current hierarchy contains 66 located contacts: 22 numbered Ultimainboard pins linked to source records and 44 photographed ESP aliases (15 ESP32, 29 ESP8266). Alias labels preserve the literal printed name without claiming connector numbering or an electrical net. NXP and Pi photo pin locations remain unresolved. These partial labels do not establish component/pin model readiness.

Official NodeMCU reference files differ from the photographed wide CH340-style clone. ESP32 and Pi community models remain comparison references until geometry is checked. Ultimaker's matching revision marking supports further registration; it does not by itself locate every source designator in a photo.

The board detector split has 62 training files, 11 validation originals and seven excluded validation crop variants. Each original and crop stays in the same fold. With one specimen/session per family and no separate ESP32 validation pose, current model diagnostics do not establish recognition across new specimens or sessions. Complete component labeling and independent evaluation data remain necessary.

Missing files and remaining acquisition routes are recorded in REMAINING_SOURCE_LEADS.md. Preserve original images, uncertain links, source attribution and file-specific notices when adding data through PRs.
