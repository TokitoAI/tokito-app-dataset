# Board, part and pin labels

The [label hierarchy](../data/photo-model/label-hierarchy.json) applies the same **board → part → pin** order to ESP32, ESP8266, Ultimainboard 2.1.4, NXP FRDM-MCXN236 and Raspberry Pi 3B V1.2. It joins reviewed board labels, existing component seeds, available linked design sources and the shared [photo pin annotation intake](../annotations/pin-annotations.json). Run `python scripts/build_label_hierarchy.py --check` to confirm it still matches those files.

Every one of the 80 images has a reviewed board family and box. Five images currently have partial component seeds: 107 part boxes in total. Ten NXP parts have readable photo reference labels linked to visually reviewed Rev C schematic symbols and BOM records. Those ten source parts provide 352 distinct pin records with source pin numbers and nets.

Each current source pin record has `mapping_status: source_pin_unregistered_in_photo` and `photo_bbox_xyxy_pixels: null`. **No individual pin has a reviewed photo box on any board yet.** The 352 NXP source records give candidates for the next labeling pass; they do not establish a pixel location, the photographed PCB revision or the exact fitted manufacturer part. The other four families follow the same labeling rule. Their source pin records have not yet been safely joined to photographed parts. Unknown pins are never used as negative training examples.

For example, the photographed NXP board contains a seeded MCU SWD header marked J12. The Rev C source lists J12 pin 1 on `JTAG_VREF`, pin 2 on `P0_0/SWDIO` and pin 4 on `P0_1/SWCLK`. The photo shows the header and the J12 marking. Assigning those numbers to individual photographed contacts still requires registration to the PCB layout or an independently checked pin-1 orientation.

The next review must follow this order for each photo, regardless of board manufacturer:

1. Confirm board family, model and revision where visible. Keep unknown revisions explicit.
2. Review each visible part box, class and reference marking. The current 107 boxes are partial seeds.
3. For each visible contact or lead, identify its physical pin number from an oriented layout or legible pin-1 evidence, record its photo box and identity evidence in `annotations/pin-annotations.json`, then attach a source net only when the source matches the photographed board. BGA balls and hidden pins have no photo label from a top-view image.

Each photo pin entry needs a unique `id`, `image_file`, exact `board_family`, parent `part_id` from the generated hierarchy, `pin_number` as a string, `photo_bbox_xyxy_pixels` within that image, `pin_identity_evidence` explaining orientation or marking, and `review_status: visually_reviewed_pin_location`. The generator checks the board and part parent before accepting the pin. An entry can have a reviewed physical pin number without a source net; that status stays explicit. If the pin cannot be numbered reliably, do not put it in the training labels.

Board identification, source component identity and physical pin position have separate evidence requirements. Component and pin model training waits for reviewed, sufficiently complete photo labels and independent validation images.
