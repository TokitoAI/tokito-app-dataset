# Dataset coverage

Collected sources and derived files are preserved separately. Exact physical-board matching remains unverified where noted.

| Board | Schematic | BOM / component inventory | PCB source | Manufacturing files | STEP and GLB |
|---|---|---|---|---|---|
| NXP FRDM-MCXN947 | Official Rev C DSN and 13-page PDF | Official XLSX, extracted CSV | Official Allegro BRD | Official Gerber ART, drill, route, fabrication PDFs | Enclosure STEP only; complete board model not located |
| Ultimainboard 2.1.4 | Official Altium sheets | 574 PCB component records; procurement BOM not verified | Official PcbDoc; 252 net records | Exported Gerbers not located | Official part 1546 STEP and derived GLB; 61 embedded component STEP models |
| ESP32 30-pin | Community clone KiCad/PDF reference | 24 reference BOM entries, JSON/CSV | Reference KiCad PCB | Exact photographed-board Gerbers not located | Community STEP and verified derived GLB |
| ESP8266 ESP-12E clone | Official NodeMCU reference Altium/PDF | 34 reference PCB component records, JSON/CSV | Reference PcbDoc; 41 net records | Four reference archives fully unpacked: 62 verified files | 17 embedded component STEP models; complete photographed-clone board model not located |
| Raspberry Pi 3B V1.2 | Official reduced schematic PDF | Complete procurement BOM not located | Native board layout not located | Gerbers not located | Community assembly submodel extracted as STEP and converted to GLB |

## Images and auxiliary datasets

Five supplied photographs preserved. Phone capture protocol saved in PHOTO_CAPTURE.md. No component image boxes or refdes labels have been invented.

DeepPCB: full original download passed ZIP CRC checks. Official splits contain 1000 trainval and 500 test pairs. All referenced image/template/annotation paths exist, splits do not overlap, and all 10013 defect boxes have valid bounds and class IDs. MIT source license retained. These are bare-PCB copper-defect examples, not component labels for the physical boards.

PCB-Vision: official metadata and CC BY 4.0 dataset license saved. Remote archive inventory identifies 159 RGB image/label files totaling 20.5 MB compressed. Zenodo file-data requests timed out. The author mirror ignored range requests and its full download stalled. No completed RGB data is available, and no download is currently running. Acquisition and mask/image validation remain pending.

Ultimaker and NodeMCU schematic inventories now include owner-linked designators and component parameters. All 574 Ultimaker and 34 NodeMCU designators match their corresponding native PCB inventories exactly. This establishes consistency between the collected source documents, not physical-board population or clone equivalence.

## Verification and limits

ESP32, Ultimaker and Pi GLBs reopen successfully, contain finite geometry, and preserve tessellated STEP bounds after converting millimetres to metres. Original coordinate offsets retained. Materials and source colours are not retained. These are geometry verification results, not proof of a physical specimen match.

NXP connectivity extraction contains 354 nets and 1470 pin connections. NXP PCB Rev C is verified in the source archive; physical-board revision is unconfirmed. BOM Item Revision A1 is separate metadata and must not be equated with PCB Rev C. Source PDF carries a proprietary-use notice; public redistribution permission is unestablished.

NXP manufacturer BOM normalized into 108 part groups with 278 manufacturer-alternative rows and 434 distinct reference designators. No duplicate reference-designator groups or alternative-quantity conflicts were found. BOM and netlist reference-designator sets match exactly. Raw workbook/CSV retained; normalized JSON preserves manufacturer alternatives and source row numbers.

ESP clone geometry/revision, NXP physical revision, remaining exact-board models, missing manufacturing/BOM files, community-model licensing, photo annotations and additional phone photos remain open. Native source files have not been engineering-validated in their original CAD tools.

Initial timed-out DeepPCB source.zip and partial NodeMCU gerbers-extracted files are excluded from usable data. Use DeepPCB/source-complete.zip and NodeMCU/gerbers-verified instead. Historical notes in PROJECT_CONTEXT.md retain the acquisition history; this document records current coverage.
