# Board and component labeling work

80 phone image files preserved: 47 original captures and 33 tight cropped variants. Photos are separated by board family under by_board. Original and crop share a capture-group ID. Board-family identities were reviewed from image pixels.

New NXP identity: readable silkscreen identifies FRDM-MCXN236. MCXN947 files are retained as reference sources but are incompatible with exact labeling of this specimen. Ultimainboard2.1.4 and Pi3B V1.2 markings are confirmed in the new photos.

## Board detector

Five classes: ESP32, ESP8266, Ultimainboard, FRDM-MCXN236, Pi3B. Board boxes proposed by colour-mask segmentation and visually reviewed on contact sheets. Tight cropped variants use the full visible-board image extent. Metadata records reviewed boxes and truncated imagery.

62 training images, 11 validation originals, 7 corresponding validation crop variants excluded to avoid duplicate evaluation. Original/crop groups never cross folds. Validation includes only four classes because all ESP32 photos belong to one similar pose group retained for training. There is one physical specimen per family and no independent specimen test. Initial CPU YOLO training is an experimental board-family baseline.

## Component and engineering data

Subagent seed annotations identify major visible components on three or four photos of each family. Seeds are partial, retain uncertainty/truncation and are not complete component-training ground truth. Small passives require further labeling. Hidden parts cannot be claimed as visually detected.

A full component detector needs exhaustive reviewed boxes for its defined classes and additional clear views, including backs of boards. Exact component reference-designator or part-number assignment additionally needs readable OCR or registered matched PCB geometry. Manufacturer alternatives and DNP/unpopulated parts must remain distinct from observed physical components.

Gerber layers, BOM rows and schematic pages are document links in a retrieval record, not visual-object classes in a phone-photo YOLO detector. Board detection chooses the compatible source bundle; component detection/OCR and registration select individual records where evidence is sufficient. Uncertain links remain unresolved.
